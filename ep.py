#! /usr/bin/env python3
# This file attempts to calucalte an earings power and return to current price
# it collects data from both screen1.get_fscore and complete financials from FundamentalAnalysis

from screen1 import *
import seaborn as sns
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import re
import itertools
import FundamentalAnalysis as fa
import sys
from sklearn.linear_model import LinearRegression


# Set up some convenience settings
pd.set_option('display.max_rows', 200)
pd.set_option('display.max_seq_items', 200)

# Get the latst fscores from fscores.xlsx
# This sheet is populated using build_fscores_excel.py
# It also uses Fundamental Analysis toolkit so have the api_key ready
api_key = "c350f6f5a4396d349ee4bbacde3d5999"
filenames = ['fscores.xlsx']
sheets = {'Sheet1':[0, 'A:DO', 1612]}
d = getasheet(filenames, sheets, 'symbol')

# Split out the most wanted sectors
short_sector_wanted = ['TMT',
 'Healthcare',
 'Industrials',
 'Consumer Cyclical',
 'Commercial Service',
 'Technology',
 'Construction',
 'Communication Services',
 'Consumer Product',
 'Utilities',
 'Retail',
 'Consumer Defensive']

short_sector_not_wanted = ['Financial Services',
        'Ag Chem and Materials',
        'Energy',
        'Basic Materials',
        'Real Estate'
        ]

sector_not_wanted = ['Biotechnology',
        'Capital Markets'
        ]

# screen for wanted spaces
b = d[d.short_sector.isin(short_sector_wanted)]
b = b[~b.sector.isin(sector_not_wanted)]

# screeners for 235 actives
actives = b[b.last_work == 'Active']

# what ticker do you want to calculate for?
ticker = sys.argv[1]

# grab the score for the ticker in question
# score = d.loc[ticker]

# a function that takes a ticker and financials and returns a base case earnings power
# model in forecasts (dataframe) and the assumptions it used in inputs (a dataframe also)
# ticker is a string ticker (e.g. 'GPX'), inc is fa.income_statement, bs is balance sheet, cf is
# cash flow. revenue_scenario is a iterable of 5 growth rates for years 1 through 5 to use
# ebitda_scenario is a list that is multiplied by the ebitda margin to push scenario up or down in total

from sklearn.linear_model import LinearRegression
import FundamentalAnalysis as fa
api_key = "c350f6f5a4396d349ee4bbacde3d5999"

revenue_scenario = []
ebitda_scenario = []

print('getting forecast')
# Get the financials for the ticker in question. Focus on annuals for now
inc = fa.income_statement(ticker, api_key, 'annual').T
inc.index = pd.to_datetime(inc.index)
inc.sort_index(inplace = True)

bs = fa.balance_sheet_statement(ticker, api_key, 'annual').T
bs.index = pd.to_datetime(bs.index)
bs.sort_index(inplace = True)

bs['wc'] = (bs.totalCurrentAssets - bs.cashAndShortTermInvestments) - bs.totalCurrentLiabilities

cf = fa.cash_flow_statement(ticker, api_key, 'annual').T
cf.index = pd.to_datetime(cf.index)
cf.sort_index(inplace = True)

# Find the fixed and variable components of costs at the GM level and then at EBITDA
# Get the data with the X = revenues and Y first COGS and then Y as SG&A
# Fill in missing values in revenues if required
inc.revenue  = inc.revenue.replace(0, np.nan).interpolate()
inc.grossProfit  = inc.grossProfit.replace(0, np.nan).interpolate()
inc.ebitda  = inc.ebitda.replace(0, np.nan).interpolate()
inc.costOfRevenue  = inc.costOfRevenue.replace(0, np.nan).interpolate()
inc.incomeBeforeTax  = inc.incomeBeforeTax.replace(0, np.nan).interpolate()
bs.totalDebt  = bs.totalDebt.replace(0, np.nan).interpolate()
revenues = inc.revenue.fillna(0).values.reshape(-1,1)
cogs = (inc.revenue - inc.grossProfit).fillna(0).values.reshape(-1,1)
sga = (inc.revenue - inc.ebitda - inc.costOfRevenue).fillna(0).values.reshape(-1,1)

cogsreg = LinearRegression()
cogsreg.fit(revenues, cogs)
sgareg = LinearRegression()
sgareg.fit(revenues, sga)

# hold some key inputs for calculations
inputs = pd.DataFrame()
inputs['ep_discount'] = [.1]
inputs['out_years_revenue_growth'] = [.03]
inputs['da_to_revenue_5_median'] = [(cf.depreciationAndAmortization / inc.revenue).last('5Y').median()]
inputs['sbc_to_revenue_5_median'] = [(cf.stockBasedCompensation / inc.revenue).last('5Y').median()]
inputs['interest_rate'] = [(inc.interestExpense / bs.totalDebt).last('5Y').median()]
inputs['wc_to_revenue_5_median'] = [(bs.wc / inc.revenue).last('5Y').median()]
inputs['capex_to_revenue_5_median'] = [(cf.capitalExpenditure / inc.revenue).last('5Y').median()]
inputs['maintenance_capex_to_revenue'] = [(cf.capitalExpenditure / inc.revenue).last('5Y').min()]
inputs['revenue_growth_3_median'] = [inc.revenue.pct_change(1).last('3Y').median()]
inputs['ebitda_margin_3_median'] = [(inc.ebitda / inc.revenue).last('3Y').median()]
inputs['interest_placeholder'] = [(inc.interestExpense / inc.revenue).last('5Y').median()]
inputs['so'] = [inc.weightedAverageShsOutDil['2019'][0]]
# use last tax_rate given changes in 2019
inputs['tax_rate'] = [(inc.incomeTaxExpense / inc.incomeBeforeTax).last('1Y').median()]
inputs['dividend_payout_to_ebitda_ratio_3_median'] = [(cf.dividendsPaid / inc.ebitda).last('3Y').median()]

# create a forecast dataframe
forecast = pd.DataFrame(columns = np.arange(start = 0, stop = 11, step = 1))

# Fill in a starting year in 2019
forecast.loc['revenue', 0] = inc.revenue['2019'][0]
forecast.loc['gm', 0] = inc.grossProfit['2019'][0]
forecast.loc['sga', 0] = inc.revenue['2019'][0]  - inc.ebitda['2019'][0] - (inc.revenue['2019'][0] - inc.grossProfit['2019'][0])
forecast.loc['ebitda', 0] = inc.ebitda['2019'][0]
forecast.loc['da', 0] = cf.depreciationAndAmortization['2019'][0]
forecast.loc['ebit', 0] = inc.operatingIncome['2019'][0]
forecast.loc['interest_expense', 0] = inc.interestExpense['2019'][0]
forecast.loc['net_debt', 0] = bs.netDebt['2019'][0]
forecast.loc['total_debt', 0] = bs.totalDebt['2019'][0]
forecast.loc['wc', 0] = bs.wc['2019'][0]
forecast.loc['cum_dividends', 0] = cf.dividendsPaid['2019'][0]

# set up to evenutally use scenarios
if len(revenue_scenario) == 0:
    # no revenue scenario provided, so use historical 3 year median
    revenue_scenario = np.full(5, inputs['revenue_growth_3_median'][0])

# Fill in revenues which drive a lot of the model; regular growth for years 1 - 5 (remember python lists end AFTER the alst year wanted
# and fill in long-term forecast from years 6-10
for year in forecast.columns[1:6]:
    forecast.loc['revenue',year] = forecast.loc['revenue', year - 1] * (1 + revenue_scenario[year - 1])

for year in forecast.columns[6:]:
    forecast.loc['revenue',year] = forecast.loc['revenue', year - 1] * (1 + inputs['out_years_revenue_growth'][0])

# fill in predicted cogs and sga for revenue forecast
revenues = forecast.loc['revenue'].values.reshape(-1,1)
pcogs = cogsreg.predict(revenues)
pcogs = [i[0]  for i in pcogs]
forecast.loc['cogs'] = pcogs

psga = sgareg.predict(revenues)
psga = [i[0]  for i in psga]
forecast.loc['sga'] = psga

# forecast.loc['ebitda'] = forecast.loc['revenue'] * inputs['ebitda_margin_3_median'][0]
forecast.loc['gm'] = forecast.loc['revenue'] - forecast.loc['cogs']
forecast.loc['ebitda'] = forecast.loc['gm'] - forecast.loc['sga']

# if there is an ebitda scenario, apply it
# note multiplying multiplier by ebitda is same as by ebitda margin since revenue is fixed
if len(ebitda_scenario) > 1:
    for year in forecast.columns[1:]:
        forecast.loc['ebitda', year] = forecast.loc['ebitda', year] * (ebitda_scenario[year - 1])
elif len(ebitda_scenario) == 1:
    for year in forecast.columns[1:]:
        forecast.loc['ebitda', year] = forecast.loc['ebitda', year] * (ebitda_scenario[0])

# do non-cross-year calcs first
forecast.loc['da' ] = forecast.loc['revenue'] * inputs['da_to_revenue_5_median'][0]
forecast.loc['ebit' ] = forecast.loc['ebitda']  - forecast.loc['da']
forecast.loc['maintenance_capex' ] = forecast.loc['revenue'] * inputs['maintenance_capex_to_revenue'][0]
forecast.loc['capex' ] = forecast.loc['revenue'] * inputs['capex_to_revenue_5_median'][0]
forecast.loc['wc' ] = forecast.loc['revenue'] * inputs['wc_to_revenue_5_median'][0]
forecast.loc['dividends' ] = forecast.loc['ebitda'] * inputs['dividend_payout_to_ebitda_ratio_3_median'][0]
forecast.loc['earnings_power' ] = ( forecast.loc['ebitda'] - forecast.loc['maintenance_capex'] ) * (1  - inputs['tax_rate'][0] )

# do some cross-year calculations
for year in forecast.columns[1:]:
    forecast.loc['change_in_working_cap', year] = forecast.loc['wc', year] - forecast.loc['wc', year - 1]
    forecast.loc['total_debt', year] = forecast.loc['total_debt', year - 1] - forecast.loc['ebitda', year] - forecast.loc['capex', year]
    forecast.loc['interest_expense', year] = max(0, forecast.loc['total_debt', year - 1] * inputs['interest_rate'][0])
    forecast.loc['cum_dividends', year ] = forecast.loc['dividends', year] + forecast.loc['dividends', year - 1]

forecast.loc['IBT'] = forecast.loc['ebit']  - forecast.loc['interest_expense']
forecast.loc['taxes'] = forecast.loc['IBT'] * inputs['tax_rate'][0]
forecast.loc['NI' ] = forecast.loc['IBT'] - forecast.loc['taxes']

forecast.loc['cash_available_to_pay_debt'] = (
        forecast.loc['ebitda']
        - forecast.loc['taxes']
        - forecast.loc['interest_expense']
        - forecast.loc['change_in_working_cap']
        - forecast.loc['capex']
        - forecast.loc['dividends']
            )

for year in forecast.columns[1:]:
    forecast.loc['net_debt', year] = forecast.loc['net_debt', year - 1] - forecast.loc['cash_available_to_pay_debt', year]

# calculate incremental earnings power in the outyears
# set up some year 5 cumulative markers
forecast.loc['discounted_ep', 5] = 0

for year in forecast.columns[6:]:
    forecast.loc['incremental_ep', year] = forecast.loc['earnings_power', year] - forecast.loc['earnings_power', 5]
    # put in extra capital required to maintain?
    forecast.loc['discounted_ep', year] = forecast.loc['earnings_power', year] / ( (1 + inputs['ep_discount'][0]) ** (year) )
    forecast.loc['cumulative_ep', year] = forecast.loc['discounted_ep', year] +  forecast.loc['discounted_ep', year - 1]
    forecast.loc['tv'] = forecast.loc['cumulative_ep', year] / inputs['ep_discount'][0]

forecast.loc['ev_in_year'] = forecast.loc['earnings_power'] / inputs['ep_discount'][0]

for year in forecast.columns:
    forecast.loc['tv_value_in_year', year] = forecast.loc['tv', 10] / ( ( 1 + inputs['ep_discount'][0] ) ** ( 10 - year) )

forecast.loc['ev'] = forecast.loc['ev_in_year'] + forecast.loc['tv_value_in_year'] + forecast.loc['cum_dividends']
forecast.loc['implied_ebitda_multiple'] = forecast.loc['ev'] / forecast.loc['ebitda']
forecast.loc['equity_value'] = forecast.loc['ev'] - forecast.loc['net_debt']
forecast.loc['value_per_share'] = forecast.loc['equity_value'] / inputs['so'][0]

forecast = forecast.astype(np.float) / 1e6
forecast.loc['value_per_share'] *= 1e6
forecast.loc['implied_ebitda_multiple'] *= 1e6


