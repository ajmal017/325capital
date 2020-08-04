#! /usr/bin/env python3
# gsc.py
# This

# Get the required packages
from getdata_325 import get_historic_prices
from graphics_325 import compare_series_bar
from screen1 import get_fscore, set_tests
import pandas as pd
import matplotlib.pyplot as plt
import sys

# Set up some convenience settings
pd.set_option('display.max_rows', 200)
pd.set_option('display.max_seq_items', 200)
plt.style.use('325.mplstyle')

# Which ticker you want the score for
ticker = sys.argv[1].upper()

# Put in an optional flag to pull live.  If not flag, then don't
try:
    live = int(sys.argv[2])
except:
    live = 0

# If it is live, pull live data, otherwise use fscores. Note that fscores may have fresher tests
d = pd.read_excel('fscores.xlsx')
d = d.set_index('symbol')

if bool(live):
    print('live is ', bool(live), 'so get live data')
    df1 = get_fscore(ticker)
else:
    df1 = d.copy()

# Make some areas categories so that they graph correctly (instead of floats)
categories = ['sector', 'business',
              'short_sector', 'tamale_status', 'last_work']
for category in categories:
    df1[category] = df1[category].astype('category')

# get the historical prices
hist = get_historic_prices(ticker)
df1.loc[ticker, 'last_price'] = hist.last('1D').Close[0]

# get the tests. Get live tests on df1
# Note that test dict main key is 'tests'
testdict = set_tests(d)

# Make the graph grid
# fig = plt.figure(constrained_layout = True)
fig = plt.figure()
gs = fig.add_gridspec(3, 3)
fig.suptitle(ticker + " - {} \n{} {}".format(
    df1.name[ticker], df1.business[ticker], df1.last_price[ticker]))

# First Row, First Column
ax = fig.add_subplot(gs[0, 0])
# Name of tests
test_data = testdict['valuation_tests']
# Name of fields holding the test values
actual_data = testdict['valuation']
# The true/false values
values = [df1.loc[ticker, i] for i in test_data]
title = 'Valuation tests =  {:2.1f}%'.format(sum(values) / len(values) * 100)
# The ticker's actual values to measure true-false with
ticker_test_values = [df1.loc[ticker, i] for i in actual_data]
# The benchmark values for true-false
benchmark_test_values = [testdict['tests'][i] for i in test_data]
compare_series_bar(ax=ax, data_labels=actual_data, value_list=[
                   ticker_test_values, benchmark_test_values], title=title, percent=False)

# First Row, Second Column
ax = fig.add_subplot(gs[0, 1:])
test_data = testdict['sbm_tests']
actual_data = testdict['sbm']
# The true/false values
values = [df1.loc[ticker, i] for i in test_data]
title = 'Superior Business Model tests =  {:2.1f}%'.format(
    sum(values) / len(values) * 100)
# The ticker's actual values to measure true-false with
ticker_test_values = [df1.loc[ticker, i] for i in actual_data]
# The benchmark values for true-false
benchmark_test_values = [testdict['tests'][i] for i in test_data]
compare_series_bar(ax=ax, data_labels=actual_data, value_list=[
                   ticker_test_values, benchmark_test_values], title=title, percent=True)

# Second Row, All Columns
ax = fig.add_subplot(gs[1, :])
test_data = testdict['puoc_tests']
test_data.remove('financing_acquired_test')
test_data.remove('equity_sold_test')
actual_data = testdict['puoc']
actual_data.remove('financing_acquired')
actual_data.remove('equity_sold')
# The true/false values
values = [df1.loc[ticker, i] for i in test_data]
title = 'Poor Use of Cash/Needs Cash tests =  {:2.1f}%'.format(sum(values) / len(
    values) * 100) + '\n' + 'Equity sold: {}, Financing Acquired: {}'.format(df1.loc[ticker, 'equity_sold'], df1.loc[ticker, 'financing_acquired'])
# The ticker's actual values to measure true-false with
ticker_test_values = [df1.loc[ticker, i] for i in actual_data]
# The benchmark values for true-false
benchmark_test_values = [testdict['tests'][i] for i in test_data]
compare_series_bar(ax=ax, data_labels=actual_data, value_list=[
                   ticker_test_values, benchmark_test_values], title=title, percent=True)

# Second Row, First Column
ax = fig.add_subplot(gs[2, 0])
test_data = testdict['bs_risks_tests']
actual_data = testdict['bs_risks']
# The true/false values
values = [df1.loc[ticker, i] for i in test_data]
title = 'Balance Sheet Risks tests =  {:2.1f}%'.format(
    sum(values) / len(values) * 100)
# The ticker's actual values to measure true-false with
ticker_test_values = [df1.loc[ticker, i] for i in actual_data]
# The benchmark values for true-false
benchmark_test_values = [testdict['tests'][i] for i in test_data]
compare_series_bar(ax=ax, data_labels=actual_data, value_list=[
                   ticker_test_values, benchmark_test_values], title=title, percent=False)

# Second Row, Second Column
ax = fig.add_subplot(gs[2, 1])
test_data = testdict['trade_tests']
actual_data = testdict['trade']
# The true/false values
values = [df1.loc[ticker, i] for i in test_data]
title = 'Trade Risks tests =  {:2.1f}%'.format(sum(values) / len(values) * 100)
# The ticker's actual values to measure true-false with
ticker_test_values = [df1.loc[ticker, i] for i in actual_data]
# The benchmark values for true-false
benchmark_test_values = [testdict['tests'][i] for i in test_data]
compare_series_bar(ax=ax, data_labels=actual_data, value_list=[
                   ticker_test_values, benchmark_test_values], title=title, percent=False)

# Second Row, Third Column
ax = fig.add_subplot(gs[2, 2])
test_data = testdict['experience_tests']
actual_data = testdict['experience']
# The true/false values
values = [df1.loc[ticker, i] for i in test_data]
title = 'Blueprint Execution tests =  {:2.1f}%'.format(sum(values) / len(values) * 100) + '\n' + 'Status: {}, Work: {}, Peers: {}'.format(
    df1.loc[ticker, 'tamale_status'], df1.loc[ticker, 'last_work'], df1.loc[ticker, 'sagard_peers'])
# The ticker's actual values to measure true-false with
ticker_test_values = [df1.loc[ticker, i] for i in actual_data]
# The benchmark values for true-false
benchmark_test_values = [testdict['tests'][i] for i in test_data]
compare_series_bar(ax=ax, data_labels=actual_data, value_list=[
                   ticker_test_values, benchmark_test_values], title=title, percent=False)

plt.savefig("{}.png".format(ticker), dpi=300, bbox_inches='tight')
fig.tight_layout()
plt.show()
