#! /usr/bin/env python3

import urllib.parse
import urllib.request
from bs4 import BeautifulSoup
import argparse
import csv
import datetime
import os
from astropy import table
import numpy as np

EVENTS = ["50km", "50mi", "100km", "100mi", "6h", "12h", "24h", "48h", "6d"]
GENDERS = ['M', 'W'] 
AGE_GROUPS = ["all", "MU23", "M23", "M35", "M40", "M45", "M50", "M55", "M60",
        "M65", "M70", "M75", "M80", "M85", "M90"]            
PAST_YEAR = datetime.date.today().year - 1

def retrieve_duv_statistics(event, /, *, gender, group='all',
        year_min=PAST_YEAR-29, year_max=PAST_YEAR, filename=None,
        overwrite=False):
    
    url = 'https://statistik.d-u-v.org/getintbestlist.php'
    if filename is None:
        filename = f'results-{event}-{gender}-{year_min}-{year_max}'
        if group != 'all':
            filename += f"-{group}"
    if filename[-4:] != '.csv':
        filename += '.csv'
    
    filename = os.path.join('csv', filename)
    if os.path.exists(filename) and not overwrite:
        return

    with open(filename, 'w') as fh:
        pass
    
    print(f"Retrieve all DUV performances for {event} ({gender})")
    print(f"From {year_min} to {year_max} in age-group: {group}")
    for year in list(range(year_min, year_max)):
        # looping over continents to limit to ≤16,000 results (4 pages)
        # as it's DUV maximum
        for nat in list(range(1, 7)):
            for page in range(1, 5):

                print(f"   {year=} continent={nat} {page=}")
                values = dict(
                    gender=gender, dist=event, year=year, nat=nat, 
                    cat=group, label='', hili='none', tt='netto', page=page,
                )
                data = urllib.parse.urlencode(values)
                req = urllib.request.Request(f"{url}?{data}")
                with urllib.request.urlopen(req) as response:
                    contents = response.read() 
                soup = BeautifulSoup(contents, 'lxml')

                results = soup.find(id='Resultlist')
                if results is None:
                    break

                rows = [
                    [c.text.strip() for c in result.findAll('td')[1:]]
                  + [l['href'].split('=')[1] for c in result.findAll('td') 
                                                for l in c.findAll('a')] 
                                    for result in results.findAll('tr')[1:]]
    
                with open(filename, 'a') as fh:
                    writer = csv.writer(fh)
                    writer.writerows(rows)

                pagination = soup.findAll('div', {'class': 'pagination'})
                if len(pagination) == 0:
                    npages = 1
                else:
                    npages = len(pagination[0].findAll('a')) + 1 # current one
                if page >= npages:
                    break

def process_duv_statistics(event, /, *, gender, group='all',
        year_min=PAST_YEAR-29, year_max=PAST_YEAR, filename=None,
        overwrite=False):
    
    url = 'https://statistik.d-u-v.org/getintbestlist.php'
    if filename is None:
        filename = f'results-{event}-{gender}-{year_min}-{year_max}'
        if group != 'all':
            filename += f"-{group}"
    if filename[-4:] != '.csv':
        filename += '.csv'

    datfilename = filename[:-4] + '.dat'
    
    filename = os.path.join('csv', filename)
    datfilename = os.path.join('dat', datfilename)

    if os.path.exists(datfilename):
        tab = table.Table.read(datfilename, format='ascii.fixed_width_two_line')
        return tab
    
    with open(datfilename, 'w'):
        pass

    tab = table.Table.read(filename, format='ascii.no_header', 
        names=['performance', 'age_graded_performance', 'flags',
                'name', 'nationality', 'date_of_birth', 'age_group',
                'age_group_rank','date','venue', 'runner_id', 'event_id'])

    for index, name in enumerate(['performance', 'age_graded_performance']):
        col = tab[name]
        if col[0][-3:] == ' km':
            col = [float(c[:-3]) if 'INF' not in c else np.nan for c in col]
            tab.remove_column(name)
            tab.add_column(col, name=name, index=index)

    date = tab['date']
    year = [int(d[6:10]) for d in date]
    day = np.array([int(d[0:2]) for d in date])
    date = np.ma.masked_array(date, mask=(day == 0))
    tab.remove_column('date')
    tab.add_column(year, name='year', index=5)
    tab.add_column(date, name='date', index=5)
    tab.remove_column('age_group_rank')

    tab.write(datfilename, format='ascii.fixed_width_two_line')
   
    return tab


if __name__ == '__main__':

    parser = argparse.ArgumentParser(
         description="Retrieve DUV ultrarunning statistics for an event."
    )
    parser.add_argument('--events', choices=EVENTS + ['all'], default='all',
        nargs="+", help="IAU-sanctionned event (distance or timed-event)")
    parser.add_argument('--genders', '-g', choices=GENDERS + ['all'], 
        nargs="+", default='all', help="Gender")
    parser.add_argument('--age-group', '-a', choices=AGE_GROUPS, default='all',
        dest='group', help="Age group")
    parser.add_argument('--year-min', type=int, default=PAST_YEAR-39,
        dest='year_min', help='First year to query')
    parser.add_argument('--year-max', type=int, default=PAST_YEAR + 1,
        dest='year_max', help='First year to query')
    parser.add_argument('--filename', '-f', type=str, default=None,
        help='File to save to')
    parser.add_argument('--overwrite', '-o', type=bool, default=False,
        action='store_true')
    args = parser.parse_args()

    if args.genders == 'all':
        args.genders = GENDERS
    if args.events == 'all':
        args.events = EVENTS

    keys = dict(
        group=args.group, year_min=args.year_min, year_max=args.year_max, 
        filename=args.filename, overwrite=args.overwrite)

    for event in args.events:
        for gender in args.genders:
            retrieve_duv_statistics(event, gender=gender, **keys) 
            process_duv_statistics(event, gender=gender, **keys)
