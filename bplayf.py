#! /usr/bin/env python3
import seaborn as sns
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import re

# Set up some convenience settings
pd.set_option('display.max_rows', 200)
pd.set_option('display.max_seq_items', 200)

# Get the latst fscores from can_fscores.xlsx

# Read the main database into d
kwargs = {'io': '325universe.xlsx',
 'sheet_name': 'Sheet1',
 'header': 0,
 'usecols': 'A:BJ',
 'nrows': 1251,
 'na_filter': True}

d = pd.read_excel(**kwargs)
d = d.set_index('ticker')

# Read the main database into d
ttfdf = pd.read_excel('fscores.xlsx')
ttfdf = ttfdf.set_index('symbol')

d = d.merge(ttfdf[['tamale_status', 'last_work', 'sagard_peers', 'market_leader', 'triggers']], how = 'left', left_index = True, right_index = True)

reasonable_eps = (d.ep_total_to_market_cap >= 1.5) & (d.ep_total_to_market_cap <= 15)
high_roic_potential = d.roic_high_5 > d.roic_high_5.quantile(q = 0.75)
high_roic_today = d.roic_ltm > d.roic_ltm.quantile(q = .75)
target_industries = (~d.sector.isin(['Retailing', 'Pharmaceuticals & Biotechnology', 'Travel & Leisure'])) & (~d.business.isin(['Retailing', 'Pharmaceuticals & Biotechnology', 'Travel & Leisure']))
ep_display = ['ep_market_cap', 'ep_value_from_fcfe', 'ep_value_from_ebitda', 'ep_value_from_roic', 'ep_total_est_value', 'ep_total_to_market_cap']
display = ['name', 'sector', 'business', 'last_work','revenue_ltm', 'em_ltm', 'ev_to_ebitda_ltm', 'net_debt_to_ebitda_ltm', 'roic_ltm','ep_total_to_market_cap']
pd.set_option('max_colwidth', 25)
pd.set_option('precision', 2)
pd.set_option('display.float_format', '{:.2f}'.format)

roth = ['ALRM', 'ASPU', 'BQ', 'PRTS', 'APPS', 'FTHM', 'GLUU', 'QH', 'MARK', 'VERI', 'NVEE', 'HCKT', 'MWK', 'ASUR', 'CYRX', 'EGAN', 'FIVN', 'MTBC', 'OPRX', 'RSSS', 'RMNI', 'SSTI', 'SNCR', 'VTSI', 'CMBM', 'DGII', 'GOGO', 'PI', 'IDCC', 'INUV', 'LTRX', 'LIFX', 'OSS', 'PWFL', 'TSXV:STC', 'SQNS', 'SMSI', 'LSE:TCM', 'ACMR', 'AKTS', 'CRNC', 'CEVA', 'DSPG', 'WATT', 'IDXAF', 'KN', 'LSCC', 'MX', 'MXL', 'NLST', 'PXLW', 'QUIK', 'SIMO', 'SITM']

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

    d = pd.read_excel('325universe.xlsx')
    d = d.set_index('ticker')

    # Read the main database into d
    ttfdf = pd.read_excel('fscores.xlsx')
    ttfdf = ttfdf.set_index('symbol')


    # If it is live, pull live data, else fscores.  fscores may have fresher tests
    if bool(live):
        print('live is', bool(live), 'so get live data')
        df1 = get_b_score(ticker)
    else:
        df1 = d

    df1 = df1.merge(ttfdf[['tamale_status', 'last_work', 'sagard_peers', 'market_leader', 'triggers']], how = 'left', left_index = True, right_index = True)

    categories = ['sector', 'business', 'tamale_status', 'last_work']
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
    fig = plt.figure(constrained_layout=True)
    gs = fig.add_gridspec(3, 3)
    fig.suptitle(ticker + " - {} \n{} {:2.1f}".format(
        df1.name[ticker], df1.business[ticker], df1.last_price[ticker]))

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
        df1.loc[ticker, 'tamale_status'], df1.loc[ticker, 'market_leader'])
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
    plt.show()

    return fig
