#! /usr/bin/env python3

import urllib.parse
import urllib.request
from bs4 import BeautifulSoup
import argparse
import csv
import datetime
import os
from astropy.table import Table
import numpy as np

FORMAT = 'ascii.fixed_width_two_line'
EVENTS = ["50km", "50mi", "100km", "100mi", "6h", "12h", "24h", "48h", "6d"]
GENDERS = ['M', 'W'] 
AGE_GROUPS = ["all", "MU23", "M23", "M35", "M40", "M45", "M50", "M55", "M60",
        "M65", "M70", "M75", "M80", "M85", "M90"]            
FIRST_YEAR = 1969
THIS_YEAR = datetime.date.today().year 
CSV_COLNAMES = ['performance', 'age_graded_performance', 'flags',
                'name', 'nationality', 'date_of_birth', 'age_group',
                'age_group_rank','date','venue', 'runner_id', 'event_id']
YEARS = np.arange(FIRST_YEAR, THIS_YEAR + 1)

def filename(ext, event, /, *, gender, year, group):
    if group == 'all':
        group = gender
    filename = f"rankings-{event}-{gender}{group[1:]}-{year}.{ext}"
    return os.path.join(ext, filename)

def alltime_results(event, /, *, year_min=FIRST_YEAR, year_max=THIS_YEAR, 
        overwrite=False):
    
    txtfile = f'txt/results-{event}.txt'

    if os.path.exists(txtfile) and not overwrite:
        return Table.read(txtfile, format=FORMAT)

    # read all yearly tables and put them into a single one
    rows = []
    for gender in GENDERS:
        for year in range(year_min, year_max + 1):
            print(f'Try to load {year} {gender} result table')
            tab = yearly_results(event, gender=gender, year=year, 
                overwrite=overwrite)
            rows += tab.as_array().tolist()

    tab = Table(rows=rows, names=tab.colnames)
    nrows = len(tab)
    
    # add event name and performance unit.
    tab.add_column(nrows * [event], name='event', index=0)
    timed = event[-1] in 'hd'

    if timed:
        unit = 'km'
    else:
        fact = [3600, 60, 1]
        perf = tab['performance']
        perf = [np.dot(fact, [int(s) for s in p.split(':')]) for p in perf]
        tab.remove_column('performance')
        tab.add_column(perf, name='performance', index=0)
        unit = 's'
    tab.add_column(nrows * [unit], name='performance_unit', index=2)

    # transform dates into ISO format
    date = ['-'.join(str(d).split('.')[::-1]) if d is not None else '0001-01-01'
                                                    for d in tab['date']]
    tab['date'] = date

    date = ['-'.join(str(d).split('.')[::-1]) if d is not None else '0001-01-01'
                                            for d in tab['date_of_birth']]
    tab['date_of_birth'] = date

    flags = [f if f is not None else 'R' for f in tab['flags']]
    tab.remove_column('flags')
    tab.add_column(flags, name='flags', index=4)

    # sort
    index = np.argsort(tab['performance'])
    if timed:
        index = index[::-1]
    tab = tab[index]

    tab.write(txtfile, format=FORMAT, overwrite=overwrite)
        
    return tab             

def yearly_results(event, /, *, gender, year, group='all', 
        overwrite=False):
   
    url = 'https://statistik.d-u-v.org/getintbestlist.php'
    
    csvfile = filename('csv', event, gender=gender, year=year, group=group)

    if os.path.exists(csvfile) and not overwrite:
        tab = Table.read(csvfile, format='ascii.csv')
        return tab

    print(f"Download all DUV performances for {event} {gender} in {year}")
    if group != 'all':
        print(f"Age group: {gender}{group[1:]}")
        
    # looping over continents to limit to ≤16,000 rankings (4 pages)
    # as it's DUV's maximum
    rows = []
    for nat in list(range(1, 7)):
        for page in range(1, 5):

            print(f"   continent={nat} {page=}")
            values = dict(
                gender=gender, dist=event, year=year, nat=nat, 
                cat=group, label='', hili='none', tt='netto', page=page,
            )
            data = urllib.parse.urlencode(values)
            req = urllib.request.Request(f"{url}?{data}")
            with urllib.request.urlopen(req) as response:
                contents = response.read() 
                
            soup = BeautifulSoup(contents, 'lxml')
            rankings = soup.find(id='Resultlist')
            if rankings is None:
                break

            # Text contents of all cells plus the runner/event ID 
            # from the url (href)
            rows += [
                [c.text.strip() for c in ranking.findAll('td')[1:]]
              + [l['href'].split('=')[1] for c in ranking.findAll('td') 
                                            for l in c.findAll('a')] 
                                for ranking in rankings.findAll('tr')[1:]]

            pagination = soup.findAll('div', {'class': 'pagination'})
            if len(pagination) == 0:
                npages = 1
            else:
                npages = len(pagination[0].findAll('a')) + 1 # current one
            if page >= npages:
                break

    if len(rows):
        tab = Table(rows=rows, names=CSV_COLNAMES)
    else:
        tab = Table(names=CSV_COLNAMES)
    
    if len(tab) != 0:

        # remove units (km and h) to get numbers, not strings
        for index, name in enumerate(['performance', 'age_graded_performance']):
            col = tab[name]
            if col[0][-3:] == ' km':
                col = [float(c[:-3]) if 'INF' not in c else np.nan for c in col]
            elif col[0][-2:] == ' h':
                col = [c[:-2] for c in col]
            if col is not tab[name]:
                tab.remove_column(name)
                tab.add_column(col, name=name, index=index)

        # parse date
        date = tab['date']
        year = [int(d[6:10]) for d in date]
        day = np.array([int(d[0:2]) for d in date])
        date = np.ma.masked_array(date, mask=(day == 0))
        tab.remove_column('date')
        tab.add_column(year, name='year', index=5)
        tab.add_column(date, name='date', index=5)
        tab.remove_column('age_group_rank')

    tab.write(csvfile, format='ascii.csv', overwrite=overwrite)
   
    return tab

if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        description="Retrieve DUV ultrarunning statistics for an event."
    )
    parser.add_argument('event', choices=EVENTS, metavar='event',
        help="IAU-sanctionned event (distance or timed-event)")
    parser.add_argument('--overwrite', '-o', default=False,
        action='store_true',
        help="download from DUV and overwrite local tables")
    args = parser.parse_args()

    alltime_results(args.event, overwrite=args.overwrite)
