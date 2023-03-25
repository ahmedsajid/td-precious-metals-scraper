import sys
import re
import os
import requests
import csv
import pandas as pd
import plotly.express as px
from datetime import datetime
from bs4 import BeautifulSoup
import pytz

SCRAPE_ENDPOINTS = [
  {
    "name": "100 oz Royal Canadian Mint Silver Bar",
    "url": "https://preciousmetals.td.com/shop/en/tdmetals/silvers/p0021"
  },
  {
    "name": "10 oz TD Silver Bar",
    "url": "https://preciousmetals.td.com/shop/en/tdmetals/silvers/p0027"
  },
  {
    "name": "10 oz TD Silver Stacker",
    "url": "https://preciousmetals.td.com/shop/en/tdmetals/silvers/p0245"
  },
  {
    "name": "10 oz Royal Canadian Mint Silver Bar",
    "url": "https://preciousmetals.td.com/shop/en/tdmetals/silvers/p0020"
  }
]

CSV_HEADERS = ['date', 'price']


def scrape_endpoint(endpoint):

    response = requests.get(endpoint)

    if response.status_code != 200:
        return None
    else:
        return BeautifulSoup(response.text, 'html.parser')


def parse_data(soup):

    # product_title = soup.find('h1', attrs={'class': 'td-product-details-banner-title'}).text.strip()

    product_price_span = soup.find('span', attrs={'class': 'td-product-tier-pricing-quantity-price', 'role': 'cell'}).text.strip()
    price = re.search('(\d{1,3})(,\d{1,3})*(\.\d{1,})?', product_price_span).group(0).strip(',')
    price_float = float(price.replace(',', ''))

    return price_float


def write_to_file(datetimenow, csv_file, price):

    with open(csv_file, 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([datetimenow, price])


def dedup_insert(input_file, current_value):
    if os.path.isfile(input_file):
        df = pd.read_csv(input_file, header=None, names=CSV_HEADERS, parse_dates=True)
        last_value = df['price'].iloc[-1]

        if last_value == current_value:
            return True
        else:
            return False
    else:
        return False


def csv_to_plot(input_file, output_file, title):

    df = pd.read_csv(input_file, header=None, names=CSV_HEADERS, parse_dates=True)

    # fig = px.line(df, x='date', y='price', title=title, text='price', markers=True)
    # fig.update_traces(textposition='top center')

    fig = px.line(df, x='date', y='price', title=title, markers=True)

    fig.write_html(output_file + '.html', include_plotlyjs='cdn')
    fig.write_image('images/' + output_file + '.png')


def main():

    datetimenow = datetime.now(pytz.timezone('America/Toronto'))

    for endpoint in SCRAPE_ENDPOINTS:

        soup = scrape_endpoint(endpoint['url'])

        if soup is not None:
            price = parse_data(soup)
            title = endpoint['name']

            print("Price for '" + title + ", " + str(price) + "'")

            if price > 0:
                title_underscore = title.replace(' ', '_')
                csv_file = 'csv/' + title_underscore + '.csv'

                if dedup_insert(csv_file, price) is False:
                    write_to_file(datetimenow, csv_file, price)
                    csv_to_plot(csv_file, title_underscore, title)
                else:
                    print("Existing price same as last for '" + title + ", " + str(price) + "'")

            else:
                print("Unable to determine price")
                sys.exit(1)


if __name__ == '__main__':
    main()
