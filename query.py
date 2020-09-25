#! /usr/bin/env python3

import urllib.parse
import urllib.request
from bs4 import BeautifulSoup
import csv

def retrieve_duv_statistics(distance, /, *, gender):
    
    url = 'https://statistik.d-u-v.org/getintbestlist.php'
    filename = f'results-{distance}-{gender}.csv'
    
    print(f"Retrieve all DUV performances for {distance} ({gender})")
    for year in list(range(1980, 2021)):
        for nat in list(range(1, 7)):
            for page in range(1, 5):

                print(f"   {year=} continent={nat} {page=}")
                values = dict(
                    gender=gender, dist=distance, year=year, nat=nat, 
                    cat='all', label='', hili='none', tt='netto', page=page,
                )
                data = urllib.parse.urlencode(values)
                req = urllib.request.Request(f"{url}?{data}")
                with urllib.request.urlopen(req) as response:
                    contents = response.read() 
                print('here')
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
    #retrieve_duv_statistics('24h', gender='M') 
    #retrieve_duv_statistics('24h', gender='W') 
    retrieve_duv_statistics('100km', gender='M') 
    retrieve_duv_statistics('100km', gender='W') 
