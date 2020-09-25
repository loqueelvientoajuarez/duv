#! /usr/bin/env python3

import urllib.parse
import urllib.request
from bs4 import BeautifulSoup
import argparse
import csv
import datetime

EVENTS = ["50km", "50mi", "100km", "100mi", "6h", "12h", "24h", "48h", "6d"]
AGE_GROUPS = ["all", "MU23", "M23", "M35", "M40", "M45", "M50", "M55", "M60",
        "M65", "M70", "M75", "M80", "M85", "M90"]            
PAST_YEAR = datetime.date.today().year - 1

def retrieve_duv_statistics(event, /, *, gender, group='all',
        year_min=PAST_YEAR-29, year_max=PAST_YEAR, filename=None):
    
    url = 'https://statistik.d-u-v.org/getintbestlist.php'
    if filename is None:
        filename = f'results-{event}-{gender}-{year_min}-{year_max}'
        if group != 'all':
            filename += f"-{group}"
    if filename[-4:] != '.csv':
        filename += '.csv'

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

                rows = [[cell.text for cell in result.findAll('td')[1:]]
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


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
         description="Retrieve DUV ultrarunning statistics for an event."
    )
    parser.add_argument('event', choices=EVENTS,
        help="IAU-sanctionned event (distance or timed-event)")
    parser.add_argument('--gender', '-g', choices=["M", "W"], 
        help="Gender")
    parser.add_argument('--age-group', '-a', choices=AGE_GROUPS, default='all',
        dest='group', help="Age group")
    parser.add_argument('--year-min', type=int, default=PAST_YEAR-39,
        dest='year_min', help='First year to query')
    parser.add_argument('--year-max', type=int, default=PAST_YEAR,
        dest='year_max', help='First year to query')
    parser.add_argument('--filename', '-f', type=str, default=None,
        help='File to save to')
    args = parser.parse_args()
    retrieve_duv_statistics(args.event, gender=args.gender, group=args.group,
        year_min=args.year_min, year_max=args.year_max, filename=args.filename) 
