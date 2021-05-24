from bs4 import BeautifulSoup
import json
import os
import re
import requests
from typing import List


def get_url(ticker: str, period: int) -> str:
    """
    Compile the url for Historical Data from Yahoo Finance for Jan 1, 2020 to March 31, 2021. Frequency set to Daily.

    :param str ticker: without ^ or other special characters
    :param int period: Yahoo will not return such a large time-span, must break make multiple requests and paginate
    :return str: the full url for the provided date range for the provided ticker
    """
    periods = {
        1: 'period1=1577836800&period2=1585699200',  # First  Quarter 2020
        2: 'period1=1585699200&period2=1593561600',  # Second Quarter 2020
        3: 'period1=1593561600&period2=1601510400',  # Third  Quarter 2020
        4: 'period1=1601510400&period2=1609459200',  # Fourth Quarter 2020
        5: 'period1=1609459200&period2=1617235200'   # First  Quarter 2021
    }
    return (f"https://finance.yahoo.com/quote/%5E{ticker}/history?{periods[period]}&interval=1d"
            '&filter=history&frequency=1d&includeAdjustedClose=true')


def convert_html_to_list(html: str) -> List[dict]:
    """
    When passed raw HTML from Yahoo Finance, will convert the table of Historical Stock data into a list of dictionary
    objects for each day of data.

    :param str html: raw HTML from Yahoo Finance
    :return list[dicts]: all records in their own dictionaries contained inside of a list
    """
    soup = BeautifulSoup(html, 'html.parser')
    if not (tbodies := soup.find_all('tbody')):  # Find the Table
        raise ValueError('No tables found in the HTML passed!')

    index_column_map = {
        1: 'date',
        2: 'open',
        3: 'high',
        4: 'low',
        5: 'close',
        6: 'adj_close',
        7: 'volume'
    }

    stock_data = []
    current_record = {}
    index = 1
    for td in tbodies[0].find_all('td'):

        if index not in index_column_map:  # surpassed the max value in the dict
            stock_data.append(current_record)
            index = 1  # Reset index
            current_record = {}  # Reset current record dict

        value = re.search(r'>(.*)<', str(td.contents[0])).group(1)
        # Convert to float if possible
        value = float(val_no_comma) if (val_no_comma := value.replace(',', '')).replace('.', '').isalnum() else value
        current_record[index_column_map[index]] = value
        index += 1

    return stock_data


def save_stock_data_json(stock_data: list, path: str) -> bool:
    """

    :param list stock_data: all records in their own dictionaries contained inside of a list
    :param str path: the location to save the newly generated JSON file
    :return bool: successfully generated?
    """
    with open(path, 'w') as json_file:
        json.dump(stock_data, json_file)
    return True


def create_json_for_ticker(ticker: str, path: str) -> bool:
    """
    Will paginate through all 5 quarters of interest for the provided ticker, combining all of the records into a
    single list and saving that list as a JSON file saved at the provided path.

    :param str ticker: ticker of the stock, no special characters like ^
    :param str path: the location to save the newly generated JSON file
    :return bool: successfully generated?
    """
    stock_data = []  # Will have to paginate over the data, one financial quarter at a time
    for period in range(1, 6):  # 5 financial quarter period
        response = requests.get(get_url(ticker, period))
        stock_data += convert_html_to_list(str(response.content))[::-1]  # Sort oldest date -> most recent date

    return save_stock_data_json(stock_data, path)


if __name__ == '__main__':
    for ticker in ['DJI', 'GSPC']:
        create_json_for_ticker(ticker, os.path.join('../data', f"{ticker.lower()}_data.json"))
