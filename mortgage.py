#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function
import sys
import argparse
import decimal
import datetime as dt
import pandas as pd
import numpy as np

MONTHS_IN_YEAR = 12
DOLLAR_QUANTIZE = decimal.Decimal('.01')

def dollar(f, round=decimal.ROUND_CEILING):
    """
    This function rounds the passed float to 2 decimal places.
    """
    if not isinstance(f, decimal.Decimal):
        f = decimal.Decimal(str(f))
    return f.quantize(DOLLAR_QUANTIZE, rounding=round)

class House:
    def __init__(self, purch_price, down_pct, purch_date):
        self._purch_price = purch_price
        self._down_pct = down_pct
        self._purch_date = purch_date

    def purch_price(self):
        return self._purch_price

    def build_mortgage(self, interest, months):
        return Mortgage(interest, months, (1-self._down_pct)*self._purch_price, self._purch_date)


class Mortgage:
    def __init__(self, interest: float, months: int, amount, start_date: dt.datetime):
        self._interest = float(interest)
        self._months = int(months)
        self._amount = dollar(amount)
        self._start_date = start_date

    def rate(self):
        return self._interest

    def month_growth(self):
        return 1. + self._interest / MONTHS_IN_YEAR

    def apy(self):
        return self.month_growth() ** MONTHS_IN_YEAR - 1

    def loan_years(self):
        return float(self._months) / MONTHS_IN_YEAR

    def loan_months(self):
        return self._months

    def amount(self):
        return self._amount

    def monthly_payment(self):
        pre_amt = float(self.amount()) * self.rate() / (float(MONTHS_IN_YEAR) * (1.-(1./self.month_growth()) ** self.loan_months()))
        return dollar(pre_amt, round=decimal.ROUND_CEILING)

    def total_value(self, m_payment):
        return m_payment / self.rate() * (float(MONTHS_IN_YEAR) * (1.-(1./self.month_growth()) ** self.loan_months()))

    def annual_payment(self):
        return self.monthly_payment() * MONTHS_IN_YEAR

    def total_payout(self):
        return self.monthly_payment() * self.loan_months()

    def monthly_payment_schedule(self):
        monthly = self.monthly_payment()
        balance = dollar(self.amount())
        rate = decimal.Decimal(str(self.rate())).quantize(decimal.Decimal('.000001'))
        while True:
            interest_unrounded = balance * rate * decimal.Decimal(1)/MONTHS_IN_YEAR
            interest = dollar(interest_unrounded, round=decimal.ROUND_HALF_UP)
            if monthly >= balance + interest:
                yield balance, interest
                break
            principle = monthly - interest
            yield principle, interest
            balance -= principle

    def payment_schedule_df(self) -> pd.DataFrame():
        dt_ix = pd.date_range(self._start_date, periods=self._months, freq='M')

        schedule = [(index, payment[0], payment[1]) for index, payment in enumerate(self.monthly_payment_schedule())]
        schedule_df = pd.DataFrame(schedule, index=dt_ix, columns=['Period', 'Principal', 'Interest'])
        schedule_df.loc[:, 'PrincipalBalance'] = self._amount
        schedule_df.loc[:, 'tmp'] = schedule_df.loc[:, 'Principal'].cumsum()
        schedule_df.loc[:, 'PrincipalBalance'] = schedule_df.loc[:, 'PrincipalBalance'] - schedule_df.loc[:, 'tmp']
        del schedule_df['tmp']

        return schedule_df

def print_summary(m):
    print('{0:>25s}:  {1:>12.6f}'.format('Rate', m.rate()))
    print('{0:>25s}:  {1:>12.6f}'.format('Month Growth', m.month_growth()))
    print('{0:>25s}:  {1:>12.6f}'.format('APY', m.apy()))
    print('{0:>25s}:  {1:>12.0f}'.format('Payoff Years', m.loan_years()))
    print('{0:>25s}:  {1:>12.0f}'.format('Payoff Months', m.loan_months()))
    print('{0:>25s}:  {1:>12.2f}'.format('Amount', m.amount()))
    print('{0:>25s}:  {1:>12.2f}'.format('Monthly Payment', m.monthly_payment()))
    print('{0:>25s}:  {1:>12.2f}'.format('Annual Payment', m.annual_payment()))
    print('{0:>25s}:  {1:>12.2f}'.format('Total Payout', m.total_payout()))

def main():
    parser = argparse.ArgumentParser(description='Mortgage Amortization Tools')
    parser.add_argument('-i', '--interest', default=6, dest='interest')
    parser.add_argument('-y', '--loan-years', default=30, dest='years')
    parser.add_argument('-m', '--loan-months', default=None, dest='months')
    parser.add_argument('-a', '--amount', default=100000, dest='amount')
    args = parser.parse_args()

    if args.months:
        m = Mortgage(float(args.interest) / 100, float(args.months), args.amount)
    else:
        m = Mortgage(float(args.interest) / 100, float(args.years) * MONTHS_IN_YEAR, args.amount)

    print_summary(m)

if __name__ == '__main__':
    main()
