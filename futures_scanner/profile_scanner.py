import requests
import pandas as pd
import datetime
from datetime import date
from dateutil.relativedelta import relativedelta, FR
import time

from scrapy import Selector


class ProfileScanner:

    PROFILE_PAGE = "https://stooq.pl/q/?s="

    MAPPING = {'F': '01',
               'G': '02',
               'H': '03',
               'J': '04',
               'K': '05',
               'M': '06',
               'N': '07',
               'Q': '08',
               'U': '09',
               'V': '10',
               'X': '11',
               'Z': '12'}

    def __init__(self, future):

        self.symbol = future['symbol']
        self.bid_ask_link = future['bid_ask_link']
        self.has_settle_price = future['settle_price']
        self.fx_spot = future['fx_spot']
        self.bid, self.bid_vol, self.ask, self.ask_vol = self._get_bid_ask()

        print('Init: ', self.symbol)

        self.info = {}
        self.info['Stooq_ask'] = self.ask
        self.info['Stooq_ask_vol'] = self.ask_vol
        self.info['Stooq_bid'] = self.bid
        self.info['Stooq_bid_vol'] = self.bid_vol
        self.info['Stooq_symbol'] = self.symbol
        self.info['fx_symbol'] = future['fx_symbol']
        self.info['fx_name'] = future['fx_name']
        self.info['fx_spot'] = self.fx_spot

        self.info['expiration'] = self._extract_expiration_date(self.symbol)
        self.info['strategy_maturity'] = self._contract_maturity()

        if self.info['strategy_maturity'] > 0:
            self.info['expired'] = False
        else:
            self.info['expired'] = True

        if self.ask and self.bid and not self.info['expired']:

            if self.fx_spot < self.bid:

                self.info['strategy_type'] = 'SHORT'
                self.info['kontrakt_position'] = 'SELL KONTRAKT'
                self.info['fx_position'] = 'BUY ' + self.info['fx_symbol'][:3]
                self.info['strategy_profit'] = self.bid - self.fx_spot
                self.info['profit_brutto'] = self._calcualte_gross_profit()

            if self.fx_spot > self.ask:

                self.info['strategy_type'] = 'LONG'
                self.info['kontrakt_position'] = 'BUY KONTRAKT'
                self.info['fx_position'] = 'SELL ' + self.info['fx_symbol'][:3]
                self.info['strategy_profit'] = self.fx_spot - self.ask
                self.info['profit_brutto'] = self._calcualte_gross_profit()

    def _calcualte_gross_profit(self):

        profit = self.info['strategy_profit']

        scaler = 360 / self.info['strategy_maturity']

        return profit / self.bid * scaler

    @classmethod
    def _get_third_fri_of_mth(cls, dt):
        return dt + relativedelta(day=1, weekday=FR(3))

    @classmethod
    def _extract_expiration_date(cls, ticker):

        year = int('20' + ticker[-2:])
        month_letter = ticker[-3]
        month_number = int(cls.MAPPING[month_letter])

        return cls._get_third_fri_of_mth(date(year, month_number, 1))

    def _contract_maturity(self):

        delta = self.info['expiration'] - date.today()

        return delta.days

    @classmethod
    def webpage_scraper(cls, url):

        html_page = ''
        counter = 0
        while html_page == '':
            try:
                html_page = requests.get(url)
                break
            except:
                counter += 1
                print('Sleeping for 5 sec [' + str(counter) + ']', end='\r')
                time.sleep(5)
                continue

        html_body = html_page.text

        scraper = Selector(text=html_body)

        return scraper

    def _get_bid_ask(self):

        if self.has_settle_price:

            scraper = self.webpage_scraper(
                'https://stooq.pl/' + self.bid_ask_link)

            bid = scraper.xpath(
                '//*[@id="t1"]/tbody/tr[5]/td[1]/font[2]//text()').extract()

            bid_vol = scraper.xpath(
                '//*[@id="t1"]/tbody/tr[5]/td[1]/font[3]//text()').extract()

            ask = scraper.xpath(
                '//*[@id="t1"]/tbody/tr[5]/td[2]/font[2]//text()').extract()

            ask_vol = scraper.xpath(
                '//*[@id="t1"]/tbody/tr[5]/td[2]/font[3]//text()').extract()

            if bid and ask:

                bid = float(bid[0])
                bid_vol = bid_vol[0]
                ask = float(ask[0])
                ask_vol = ask_vol[0]

            else:

                bid = ''
                bid_vol = ''
                ask = ''
                ask_vol = ''

        else:

            bid = ''
            bid_vol = ''
            ask = ''
            ask_vol = ''

        return bid, bid_vol, ask, ask_vol
