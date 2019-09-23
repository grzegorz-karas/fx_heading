import argparse
import pprint
import datetime
import time
import pandas as pd

import requests
from scrapy import Selector

from futures_scanner import ProfileScanner


def get_symbol(future_html):

    return future_html.xpath('./td[1]/b/a/text()').extract()[0]


def get_name(future_html):

    return future_html.xpath('./td[2]/text()').extract()[0]


def get_futures_link(future_html):

    return future_html.xpath('./td[1]/b/a/@href').extract()[0]


def get_settle_price(future_html, as_number=False):

    value = future_html.xpath('./td[3]/b/span/text()').extract()

    if not as_number:
        if value:
            return 'Y'
        else:
            return 'N'
    else:
        if value:
            return float(value[0])
        else:
            return ''


def get_fx_for_future(fx_list, future):

    fx_base = [fx for fx in fx_list if fx['fx_symbol'][:3] in future['symbol']]

    future.update(fx_base[0])

    return future


def get_list_of_futures(fx_list):

    future_html_list = []

    sel = ProfileScanner.webpage_scraper('https://stooq.pl/t/?i=567')

    future_html_list_one_page = sel.xpath('//table[@id="fth1"]/tbody/tr')

    future_html_list = future_html_list + future_html_list_one_page

    futures_list = [{'symbol': get_symbol(future_html),
                     'bid_ask_link': get_futures_link(future_html),
                     'settle_price': get_settle_price(future_html),
                     } for future_html in future_html_list]

    futures_list_with_fx = \
        [get_fx_for_future(fx_list, future) for future in futures_list]

    return futures_list_with_fx


def scann_futures(futures_list):

    return [ProfileScanner(future) for future in futures_list]


def extract_info_from_future_instance(scanned_futures):

    return [future.info for future in scanned_futures]


def get_main_fx_rates():

    fx_html_list = []

    sel = ProfileScanner.webpage_scraper('https://stooq.pl/t/?i=60')

    fx_html_list = sel.xpath('//table[@id="fth1"]/tbody/tr')

    fx_html_list_filtered = [fx_html for fx_html in fx_html_list
                             if fx_html.xpath('@id').extract()]

    fx_list = [{'fx_symbol': get_symbol(fx_html),
                'fx_name': get_name(fx_html),
                'fx_bid_ask_link': get_futures_link(fx_html),
                'fx_spot': get_settle_price(fx_html, as_number=True)
                } for fx_html in fx_html_list_filtered]

    return fx_list


def save_results(futures_info, destination_path, file_type):

    pd_futures_info = pd.DataFrame(futures_info)

    nazwa_pliku = destination_path \
        + str(datetime.date.today()).replace('-', '') \
        + '_' + file_type + '.xlsx'

    pd_futures_info.to_excel(nazwa_pliku)


def main():

    fx_list = get_main_fx_rates()
    futures_list = get_list_of_futures(fx_list)

    scanned_futures = scann_futures(futures_list)

    futures_info = extract_info_from_future_instance(scanned_futures)

    save_results(fx_list, args.output_destination_path, 'FX')
    save_results(futures_info, args.output_destination_path, 'FUTURES')


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--output_destination_path',
        type=str,
        default='D:\\Projekty\\fx_heading\\data\\',
        help='Folder where data will be store'
    )

    args = parser.parse_args()

    # for i in range(int(3600*2), 0, -1):
    #     time.sleep(1)
    #     print('Seconds to start: ' + str(i), end='\r')

    main()
