#! /usr/bin/env python3
import seaborn as sns
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import re
import bql
import bqviz as bqv
bq = bql.Service()

# Set up some convenience settings
pd.set_option('display.max_rows', 200)
pd.set_option('display.max_seq_items', 200)

# Read the main database into d
kwargs = {'io': '325Universe.xlsx',
 'sheet_name': 'Sheet1',
 'na_filter': True}

d = pd.read_excel(**kwargs)
d = d.set_index('ticker')

reasonable_eps = (d.ep_total_to_market_cap >= 1.5) & (d.ep_total_to_market_cap <= 15)
high_roic_potential = d.roic_high_5 > d.roic_high_5.quantile(q = 0.75)
high_roic_today = d.roic_ltm > d.roic_ltm.quantile(q = .75)
target_industries = (~d.sector.isin(['Retailing', 'Pharmaceuticals & Biotechnology', 'Travel & Leisure'])) & (~d.business.isin(['Retailing', 'Pharmaceuticals & Biotechnology', 'Travel & Leisure']))
ep_display = ['ep_market_cap', 'ep_value_from_fcfe', 'ep_value_from_ebitda', 'ep_value_from_roic', 'ep_total_est_value', 'ep_total_to_market_cap']
display = ['name', 'sector', 'business', 'last_work','revenue_ltm', 'em_ltm', 'ev_to_ebitda_ltm', 'net_debt_to_ebitda_ltm', 'roic_ltm','roic_high_5','ep_total_to_market_cap']
pd.set_option('max_colwidth', 25)
pd.set_option('precision', 2)
pd.set_option('display.float_format', '{:.2f}'.format)

def get_ttf_universe():
    import bql

    # Set up the bloomberg service
    bq = bql.Service()

    # start with Russell 2000
    rty = bq.univ.members('RTY Index')

    # create some filters using market_cap
    market_cap = bq.data.market_cap()
    less_than_1750 = market_cap <= 1750e6
    more_than_100 = market_cap >= 100e6
    size_criteria = bq.func.and_(
            less_than_1750,
            more_than_100,
            )
    univ = bq.univ.filter(rty, size_criteria)

    # create a filter domicile in US
    country = bq.data.cntry_of_domicile()
    in_us = country == 'US'
    in_cn = country == 'CN'
    in_na = bq.func.or_(in_us, in_cn)
    univ = bq.univ.filter(univ, in_na)


    # create a filter to remove industries
    group = bq.data.gics_industry_group_name()
    sector = bq.data.gics_sector_name()
    not_in_banks = group != 'Banks'
    not_in_energy = group != 'Energy'
    not_in_biotech = sector != 'Biotechnology'
    not_in_finance = group != 'Diversified Financials'
    not_in_retail = group != 'Food & Staples Retailing'
    not_in_insurance = group != 'Insurance'
    univ = bq.univ.filter(univ, not_in_banks)
    univ = bq.univ.filter(univ, not_in_energy)
    univ = bq.univ.filter(univ, not_in_biotech)
    univ = bq.univ.filter(univ, not_in_finance)
    univ = bq.univ.filter(univ, not_in_retail)
    univ = bq.univ.filter(univ, not_in_insurance)

    # return the universe
    return univ


def report_b_score (ticker, live = 0):
    import matplotlib.dates as mdates
    import matplotlib.pyplot as plt
    from graphics_325 import series_bar
    import bql
    import bqviz as bqv
    from bquant import get_b_score

    bq = bql.Service()

    plt.style.use('325.mplstyle')

    # Convert to upper in case user put in lower case
    ticker = ticker.upper()

    d = pd.read_excel('325Universe.xlsx')
    d = d.set_index('ticker')

    # If it is live, pull live data, else 325Universe which may have outdated data
    if bool(live):
        print('live is', bool(live), 'so get live data')
        df1 = get_b_score(ticker)
    else:
        df1 = d

    categories = ['sector', 'business', 'status', 'last_work']
    for category in categories:
        df1[category] = df1[category].astype('category')


    # get the historical prices
    prices = bq.data.px_last(dates = bq.func.range('-3Y', '0D'), per = 'D')
    request = bql.Request(f'{ticker} US Equity', {'px_last':prices})
    response = bq.execute(request)
    hist = response[0].df()
    hist = hist.set_index(pd.to_datetime(hist.DATE))['px_last']
    df1['last_price'] = hist.last('1D')[0]

    # Make the first row of graphs
    fig = plt.figure(constrained_layout = True)
    gs = fig.add_gridspec(3, 3)
    fig.suptitle(ticker + f" - {df1.name[ticker]} \n{df1.business[ticker]} {df1.last_price[ticker]:2.1f} Monitor for: {df1.monitor_price[ticker]:2.1f}")

    # First Row, First Column
    ax = fig.add_subplot(gs[0, 0])
    data = ['revenue_ltm', 'ebitda_ltm', 'ocf_ltm',
            'net_debt_ltm', 'cash_ltm', 'market_cap']
    values = [df1.loc[ticker, i] for i in data]
    series_bar(ax, data, values, 'Key Financials', False)

    # First Row, Second Column
    ax = fig.add_subplot(gs[0, 1])
    data = ['ep_market_cap', 'ep_value_from_ebitda', 'ep_value_from_roic', 'ep_value_from_fcfe', 'ep_total_est_value']
    values = [df1.loc[ticker, i] for i in data]
    series_bar(ax, data, values,
               'Earnings Power Breakdown', False)

    # First Row, Third Column
    ax = fig.add_subplot(gs[0, 2])
    data = ['roic_ltm', 'roic_high_5']
    values = [df1.loc[ticker, i] for i in data]
    series_bar(ax, data, values, 'Key Return on Capital Changes', True)

    # Second Row, First Column
    ax = fig.add_subplot(gs[1, 0])
    data = ['ev_to_ebitda_ltm', 'net_debt_to_ebitda_ltm']
    values = [df1.loc[ticker, i] for i in data]
    series_bar(ax, data, values, 'Multiples', False)

    # Second Row, Second Column
    ax = fig.add_subplot(gs[1, 1])
    data = ['revenue_growth_3', 'gm_ltm', 'gm_high_5', 'em_ltm', 'em_high_5', 'sgam_ltm', 'sgam_low_5']
    values = [df1.loc[ticker, i] for i in data]
    title = "Margins vs. Highs"
    series_bar(ax, data, values, title, True)
    ax.annotate(xy=(1.5, max(values) * 1.2), s=f"ratios of improvement to current price \n em:{df1.price_opp_at_em_high[ticker]:3.1f},sgam:{df1.price_opp_at_sgam_low[ticker]:3.1f},roic:{df1.price_opp_at_roic_high[ticker]:3.1f}")

    # Second Row, Third Column
    ax = fig.add_subplot(gs[1, 2])
    data = ['ep_today', 'ep_total', 'buy_price_entry' ]
    title = "EP price today and buy prices. \n status = {}, market leader ={}".format(
        df1.loc[ticker, 'status'], df1.loc[ticker, 'market_leader'])
    values = [df1.loc[ticker, i] for i in data]
    series_bar(ax, data, values, title, False)

    # Third Row, First Two Columns
    ax = fig.add_subplot(gs[2, 0:2])
    ax.plot(hist)
    price_change_52_high = df1.price_change_52[ticker]
    price_change_ytd = df1.loc[ticker, 'last_price'] / hist.asof('2019-12-31') - 1


    ax.annotate(
        s='{:3.1f}'.format(df1.last_price[ticker]),
        xy=(mdates.date2num(df1.loc[ticker,'date_of_data']), df1.last_price[ticker]),
        ha='left',
    )
    ax.set_title("From 2019 high: {:3.1%}\n and YTD: {:3.1%}".format( price_change_52_high, price_change_ytd))

    # Third Row, Third Column
    ax = fig.add_subplot(gs[2, 2])
    adv = df1.loc[ticker, 'adv_3_mo']
    so = df1.loc[ticker, 'so']
    market_cap = df1.loc[ticker, 'market_cap']
    data_labels = ['ADV(3mo)K', '% Traded Daily', '$ Traded Daily M', '% Own w/ $4M', '$10M']
    values = [adv * 1000, adv/so * 100, adv/so * market_cap, 4/market_cap*100, 10/market_cap*100]
    title = "Trading Stats"
    series_bar(ax, data_labels, values, title, False)

    plt.savefig("{}.png".format(ticker), dpi=300, bbox_inches='tight')

    return fig


def report_b_test (ticker, live = 0):
    import matplotlib.dates as mdates
    import matplotlib.pyplot as plt
    from graphics_325 import series_bar, compare_series_bar
    import bql
    import bqviz as bqv
    from bquant import get_b_score, get_b_field

    bq = bql.Service()

    plt.style.use('325.mplstyle')

    # Convert to upper in case user put in lower case
    ticker = ticker.upper()

    d = pd.read_excel('325Universe.xlsx')
    d = d.set_index('ticker')

    # If it is live, pull live data, else fscores.  fscores may have fresher tests
    if bool(live):
        print('live is', bool(live), 'so get live data')
        df1 = get_b_score(ticker)
    else:
        df1 = d

    categories = ['sector', 'business', 'status', 'last_work']
    for category in categories:
        df1[category] = df1[category].astype('category')


    # get the historical prices
    prices = bq.data.px_last(dates = bq.func.range('-3Y', '0D'), per = 'D')
    request = bql.Request(f'{ticker} US Equity', {'px_last':prices})
    response = bq.execute(request)
    hist = response[0].df()
    hist = hist.set_index(pd.to_datetime(hist.DATE))['px_last']
    df1['last_price'] = hist.last('1D')[0]

    # Make the first row of graphs
    fig = plt.figure(constrained_layout = True)
    gs = fig.add_gridspec(2, 2)
    fig.suptitle(ticker + f" - {df1.name[ticker]} \n{df1.business[ticker]} {df1.last_price[ticker]:2.1f} CEO tenure:{df1.ceo_tenure[ticker]}")

    # First Row, First Column

    ax = fig.add_subplot(gs[0, 0])
    data_labels = ['em_ltm','roic_ltm', 'gm_ltm', 'capex_ltm', 'fcfe_yield']
    values = [
            df1.loc[ticker, 'em_ltm'],
            df1.loc[ticker, 'roic_ltm'],
            df1.loc[ticker, 'gm_ltm'],
            df1.loc[ticker, 'capex_ltm'] / df1.loc[ticker, 'revenue_ltm'],
            df1.loc[ticker, 'fcfe_ltm'] / df1.loc[ticker, 'ebitda_ltm']
            ]
    test_values = [
            d.em_ltm.quantile(q = .75),
            d.roic_ltm.quantile(q = .75),
            d.gm_ltm.quantile(q = .75),
            (d.capex_ltm / d.revenue_ltm).quantile(q = .25),
            (d.fcfe_ltm / d.ebitda_ltm).quantile(q = .75)
            ]
    compare_series_bar(
            ax = ax,
            data_labels = data_labels,
            value_list = [values, test_values],
            title = 'Quality (top quartile)',
            percent = True
            )

    # First, Row, Second Column
    ax = fig.add_subplot(gs[0,1])
    data_labels = ['em_delta', 'sgam_delta', 'roic_delta']
    values = [
            df1.loc[ticker, 'em_high_5'] - df1.loc[ticker, 'em_ltm'],
            df1.loc[ticker, 'sgam_ltm'] - df1.loc[ticker, 'sgam_low_5'],
            df1.loc[ticker, 'roic_high_5'] - df1.loc[ticker, 'roic_ltm'],
            ]
    test_values = [
            (d.em_high_5 - d.em_ltm).quantile(q = 0.75),
            (d.sgam_ltm - d.sgam_low_5).quantile(q = 0.75),
            (d.roic_high_5 - d.roic_ltm).quantile(q=0.75),
            ]
    compare_series_bar(
            ax = ax,
            data_labels = data_labels,
            value_list = [values, test_values],
            title = 'Opportunity for Value',
            percent = True,
            )

    # Second Row, First Column
    ax = fig.add_subplot(gs[1,0])
    data_labels = ['revenue_growth_3', 'revenue_growth_ntm']
    values = [
            df1.loc[ticker, i] for i in data_labels
            ]
    test_values = [
            d[i].quantile(q = 0.75) for i in data_labels
            ]
    compare_series_bar(
            ax = ax,
            data_labels = data_labels,
            value_list = [values, test_values],
            title = 'Growth Rates',
            percent = True,
            )

    # Second Row, Second Column
    ax = fig.add_subplot(gs[1,1])
    data_labels = ['ocf to icf ratio', 'net_debt to ocf', 'capex to ocf ratio', 'ocf to net_debt due in one year']
    debt_due_in_1_year = get_b_field(ticker, 'MATURING_DEBT_1Y_TO_TOTAL_DEBT(fpt=A)') * df1.loc[ticker, 'total_debt']
    values = [
            df1.loc[ticker, 'ocf_ltm'] / df1.loc[ticker, 'icf_ltm'],
            df1.loc[ticker, 'net_debt_ltm'] / df1.loc[ticker, 'ocf_ltm'],
            df1.loc[ticker, 'capex_ltm'] / df1.loc[ticker, 'ocf_ltm'],
            debt_due_in_1_year / df1.loc[ticker, 'ocf_ltm'],
            ]
    test_values = [
            (d.ocf_ltm / d.icf_ltm).quantile(q = 0.75),
            (d.net_debt_ltm / d.ocf_ltm).quantile(q = 0.5),
            (d.capex_ltm / d.ocf_ltm).quantile(q = 0.5),
            3
            ]
    compare_series_bar(
            ax = ax,
            data_labels = data_labels,
            value_list = [values, test_values],
            title = 'Cash Flow Characteristics',
            percent = False,
            )

    plt.savefig(f"{ticker}_test.png", dpi=300, bbox_inches='tight')


    return fig


