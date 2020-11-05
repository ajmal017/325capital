#! usr/bin/env python3
import sys

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

from getdata_325 import get_historic_prices
from graphics_325 import series_bar, compare_series_bar
from screen1 import get_fscore, set_tests

# Set up some convenience settings
pd.set_option('display.max_rows', 999)
pd.set_option('display.max_seq_items', 999)
plt.style.use('325.mplstyle')


def report_score (ticker, live = 0):

    # Convert to upper in case user put in lower case
    ticker = ticker.upper()

    d = pd.read_excel('fscores.xlsx')
    d = d.set_index('symbol')

    # If it is live, pull live data, else fscores.  fscores may have fresher tests
    if bool(live):
        print('live is ', bool(live), 'so get live data')
        df1 = get_b_score(ticker)
        d.update(df1)
        d.to_excel('fscores.xlsx')
    else:
        df1 = d

    categories = ['sector', 'business',
                  'short_sector', 'tamale_status', 'last_work']
    for category in categories:
        df1[category] = df1[category].astype('category')


    # get the historical prices
    hist = get_historic_prices(ticker)
    df1.loc[ticker, 'last_price'] = hist.last('1D').Close[0]

    # Make the first row of graphs
    fig = plt.figure(constrained_layout=True)
    gs = fig.add_gridspec(3, 3)
    fig.suptitle(ticker + " - {} \n{} {}".format(
        df1.name[ticker], df1.business[ticker], df1.last_price[ticker]))

    # First Row, First Column
    ax = fig.add_subplot(gs[0, 0])
    data = ['revenue_ltm', 'ebitda_ltm', 'ocf_ltm',
            'net_debt_ltm', 'cash_ltm', 'market_cap']
    values = [df1.loc[ticker, i] for i in data]
    series_bar(ax, data, values, 'Key Financials', False)

    # First Row, Second Column
    ax = fig.add_subplot(gs[0, 1])
    data = ['VALUATION_test', 'SBM_test', 'PI_test', 'BS_risks_test',
            'PUOC_test', 'TRADE_test', 'ep_irr', 'ep_irr_sector']
    values = [df1.loc[ticker, i] for i in data]
    series_bar(ax, data, values,
               'Key Tests (first three higher is better; not for others', True)

    # First Row, Third Column
    ax = fig.add_subplot(gs[0, 2])
    data = ['roic', 'roic_high_5', 'roic_avg_5',
            'roic_change_from_ic', 'roic_change_from_r']
    values = [df1.loc[ticker, i] for i in data]
    series_bar(ax, data, values, 'Key Return on Capital Changes', True)

    # Second Row, First Column
    ax = fig.add_subplot(gs[1, 0])
    data = ['ev_to_ebitda_ltm', 'fcfe_to_marketcap', 'net_debt_to_ebitda_ltm']
    values = [df1.loc[ticker, i] for i in data]
    series_bar(ax, data, values, 'Multiples', False)

    # Second Row, Second Column
    ax = fig.add_subplot(gs[1, 1])
    data = ['revenue_growth_3', 'gm_ltm', 'gm_high_5', 'ebitda_margin_ltm',
            'ebitda_margin_high_5', 'sgam_ltm', 'sgam_low_5']
    values = [df1.loc[ticker, i] for i in data]
    title = "Margins vs. Highs"
    series_bar(ax, data, values, title, True)
    ax.annotate(xy=(1.5, max(values) * 1.2), s="ratios of improvement to current price \n em:{:3.1f},sgam:{:3.1f},roic:{:3.1f}".format(
        df1.price_opp_at_em_high[0], df1.price_opp_at_sgam_low[0], df1.price_opp_at_roic_high[0]))

    # Second Row, Third Column
    ax = fig.add_subplot(gs[1, 2])
    data = ['ep_today_sector', 'buy_price_ten_percent',
            'buy_price_ten_percent_sector']
    title = "EP price today and buy prices. \n status = {}, market leader ={}".format(
        df1.loc[ticker, 'tamale_status'], df1.loc[ticker, 'market_leader_test'])
    values = [df1.loc[ticker, i] for i in data]
    series_bar(ax, data, values, title, False)

    # Third Row, First Two Columns
    ax = fig.add_subplot(gs[2, 0:2])
    ax.plot(hist['Close'])
    price_change_52_high = df1.price_change_52[ticker]
    price_change_ytd = df1.last_price[ticker] / hist.loc['2019-12-31']['Close'] - 1

    ax.annotate(
        s='{:3.1f}'.format(df1.last_price[ticker]),
        xy=(mdates.date2num(df1.date_of_data)[0], df1.last_price[ticker]),
        ha='left',
    )
    ax.set_title("From 2019 high: {:3.1%}\n and YTD: {:3.1%}".format(
        price_change_52_high, price_change_ytd))

    # Third Row, Third Column
    ax = fig.add_subplot(gs[2, 2])
    adv = df1.loc[ticker, 'adv_avg_months_3']
    so = df1.loc[ticker, 'so']
    market_cap = df1.loc[ticker, 'market_cap']
    data_labels = ['ADV(3mo)K', '% Traded Daily',
                   '$ Traded Daily M', '% Own w/ $5M', '$12.5M']
    values = [adv * 1000, adv/so * 100, adv/so *
              market_cap, 5/market_cap*100, 12.5/market_cap*100]
    title = "Trading Stats"
    series_bar(ax, data_labels, values, title, False)

    plt.savefig("{}.png".format(ticker), dpi=300, bbox_inches='tight')
    plt.show()

    return fig

def report_score_details (ticker, live = 0):

    # Convert to upper in case user put in lower case
    ticker = ticker.upper()

    # If it is live, pull live data, else fscores.  fscores may have fresher tests
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
    # fig.tight_layout()
    plt.show()

    return fig
