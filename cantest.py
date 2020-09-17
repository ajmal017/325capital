#! /usr/bin/env python3
# get_canalyst_model.py
# This file defines functions to take a canalyst model and create
# a relevant set of financials in a dataframe.

import os
import sys

import openpyxl
import pandas as pd
import numpy as np

from getdata_325 import get_key_stats, get_historic_prices
from screen1 import run_tests, run_eps


def get_latest_file_for_ticker(ticker, directory):
    """ This function takes a ticker and a directory and scans all the files and
    returns the most recent file with the ticker's name in it.
    """
    # Get all the directory entries in the directory
    dir_entries = os.scandir(directory)

    # Make a dictionary of all the excel files with the tickers name in it with date/time
    files = {entry.name: entry.stat().st_mtime for entry in dir_entries if (ticker in entry.name) & ('.xls' in entry.name)}

    # Sort the files by date (item 1) in reverse order (most recent first)
    files = sorted(files.items(), key=lambda item: item[1], reverse=True)
    print(files)

    # Return the first distionary entry [0] and then the first entry of key/value pair which is the filename [0]
    return files[0][0]

def get_summary_page(ticker):
    """ This function takes a ticker and looks in Anil's 325resarch path and reads the
        latest canalyst sheet (based on get_latest_file_for_ticker function.

        It then returns two dataframes and the mrfp - q and f which are the normalized quarterly and
        fiscal year cuts of that spreadsheet page

        Typical errors are related to quality of input data. Recommend: update the model to the latest,
        ensure that summary page rows are named consistently for reading.
        Example errors are:
        - out of range - not enough data
        - can't read some values, dataframe doesn't recognize some fields as numerical due to some text typed
        - < error or something; which acutally means that there are multple columns named the same thing
            by mistake; check parsing of fields
        """

    # Set up to run interactively while experimenting
    directory = '/home/aks/325research/'+ticker.upper()+'/Models'

    # Get the latest date of the model using openpyxl and MO.MRFP field in canalyst models
    filename = directory + '/' + get_latest_file_for_ticker(ticker, directory)
    workbook = openpyxl.load_workbook(filename)

    # MRFP_range will then have a list of the sheet and the range of the date (but with $ signs)
    MRFP_range = workbook.defined_names['MO.MRFP'].attr_text.split('!')

    # The last date is in the workbook[sheetname][range].value have to remember to remove the $
    mrfp = workbook[MRFP_range[0]][MRFP_range[1].replace("$", '')].value

    # create a pandas dataframe from the Model sheet of the Canalyst file
    c = pd.read_excel(filename, sheet_name='Summary Page', header=1)
    c = c.set_index('Reports')
    print(f'Imported the {ticker} model from {filename} with date {mrfp}')

    # Drop NA rows (section headers) and USD column (which reads in as all NA)
    c = c.replace(to_replace = ["NMF","NaN"], value = pd.NA)
    c = c.dropna(axis = 'index', how = 'all')
    drop_columns = c.columns[c.columns.str.contains('Unnamed')].values.tolist()
    drop_columns.append('USD')
    c = c.drop(columns = drop_columns)

    new_field_names = {
            'Stock Price - Avg': 'price_avg',
            'Adjusted Shares Outstanding - WAD': 'so',
            'Market Cap - Avg': 'market_cap_avg',
            'Cash': 'cash',
            'Debt': 'debt',
            'Operating Lease Liabilities': 'operating_leases',
            'Other EV Components': 'other_ev_components',
            'Enterprise Value - Avg': 'ev_avg',
            'Total Revenue Growth, %': 'revenue_growth',
            'Gross Revenue': 'revenue',
            'Net Revenue': 'revenue',
            'COGS (adj. for D&A)': 'cogs_ex_da',
            'COGS (adj. for SBC and Amortization Expense': 'cogs_ex_da',
            'SG&A (adj. for SBC)': 'sga_ex_sbc',
            'Salaries and wages': 'sga_ex_sbc',
            'SG&A (adj. for SBC and Depreciation Expense)': 'sga_ex_sbc',
            'R&D (adj. for SBC)': 'rd_ex_sbc',
            'EBITDA': 'ebitda',
            'SBC': 'sbc',
            'D&A': 'da',
            'R&D': 'rd',
            'Interest expense, net': 'interest_expense',
            'Other Items': 'other_items',
            'EBT': 'ebt',
            'Tax': 'tax',
            'Discontinued Operations': 'disc_ops',
            'Net Income to NCI': 'net_income_to_nci',
            'Preferred stock dividends': 'preferred_dividends',
            'Net Income from Continued Operation': 'opinc',
            'GAAP EPS': 'gaap_eps',
            'Adjusted EBITDA': 'ebitda_adjusted',
            'Adjusted EBITDA (No Adjustments)': 'ebitda_adjusted_none',
            'Adjusted Net Income': 'ni_adjusted',
            'Adjusted Earnings Per Share - WAD': 'eps_adjusted',
            'COGS Margin (Excluding D&A), %': 'cogs_margin_ex_da',
            'SG&A Margin (adj. for SBC), %': 'sga_margin_ex_sbc',
            'SG&A (adj. for SBC) Margin, %': 'sga_margin_ex_sbc',
            'EBITDA Margin, %': 'ebitda_margin',
            'Adjusted EBITDA Margin, %': 'ebitda_margin_adjusted',
            'Operating Cash Flow before WC': 'OCF_before_wc',
            'Capex': 'capex',
            'Core FCF, Pre Div': 'fcf_pre_div',
            'Dividend Paid': 'dividends',
            'Core FCF, Post Div': 'fcf_post_div',
            'Acquisitions': 'acquisitions',
            'Divestiture': 'divestitures',
            'Change in WC': 'wc_delta',
            'New Equity Issuance': 'equity_issued',
            'New Debt Issuance': 'debt_issued',
            'Change in Cash Position': 'cash_delta',
            'Operating Cash Flow Per Share': 'ocf_per_share',
            'Core Free Cash Flow Per Share, Pre Div': 'fcf_per_share',
            'Dividend Per Share': 'div_per_share',
            'Dividend Payout Ratio vs Core FCF, Pre Div': 'div_to_fcf_pre_div',
            'Dividend Payout Ratio vs Earnings Per Share': 'div_to_eps',
            'Net Debt / EBITDA': 'net_debt_to_ebitda',
            'Net Debt / Cash Flow': 'net_debt_to_cf',
            'Net Debt / Capital': 'net_debt_to_capital',
            'LTM EBITDA': 'ebitda_ltm',
            'LTM Cash Flow': 'cf_ltm',
            'Net Income': 'ni',
            'LTM Net Income': 'ni_ltm',
            "Shareholder's Equity": 'equity_shareholders',
            "Average Shareholder's Equity": 'se_average',
            'ROE': 'roe',
            'Net Operating Profit': 'opinc_net',
            'LTM Net Operating Profit': 'opinc_net_ltm',
            'Total Assets': 'total_assets',
            'Average Total Assets': 'total_assets_avg',
            'ROA': 'roa',
            'Book Value of Debt': 'book_value_of_to_debt',
            'Average Book Value of Debt': 'book_value_of_debt_avg',
            'Average Invested Capital': 'ic_avg',
            'ROIC': 'roic',
            'EBIT': 'ebit',
            'LTM EBIT': 'ebit_ltm',
            'Current Liabilities': 'current_liabilites',
            'Average Current Liabilities': 'current_liabilities_avg',
            'Average Capital Employed': 'ce_average',
            'ROCE': 'roce',
            'Revenue Per Share Growth': 'revenue_per_share_growth',
            'Adj. EBITDA Per Share Growth': 'adj_ebitda_per_share_growth',
            'Adj. Earnings Per Share Growth': 'adj_earnings_per_share_growth',
            'Operating Cash Flow Per Share Growth': 'ocf_per_share_growth',
            'Free Cash Flow Per Share Growth': 'fcf_per_share_growth',
            'P/E - Avg': 'pe_avg',
            'EV/EBITDA - Avg': 'ev_to_ebitda_avg',
            'P/CF - Avg': 'p_to_cf_avg',
            'FCF Yield % to Avg Market Cap': 'fcf_to_market_cap',
            'FCF Yield % to Avg Enterprise Value': 'fcf_to_ev',
            'Non GAAP NI': 'ni_non_gaap',
            'GAAP NI': 'ni_gaap',
            'Change in Cash Summary = Change in Cash Model': 'change_in_cash_summary'
            }

    c = c.rename(index = new_field_names)
    c.index.name = ticker
    m = c.T
    m = m.convert_dtypes()


    # Fix some odd issues if they exist
    d = [i for i in m.columns if i.startswith('Depreciation')]
    a = [i for i in m.columns if i.startswith('Amortization')]
    e = [i for i in m.columns if i.startswith('Adjusted EBITDA')]
    c = [i for i in m.columns if i.startswith('COGS')]
    s = [i for i in m.columns if (i.startswith('SG&A') | (i.startswith('S&M')))]
    g = [i for i in m.columns if i.startswith('G&A')]

    d = d[0] if len(d) > 0 else 'd'
    a = a[0] if len(a) > 0 else 'a'
    e = e[0] if len(e) > 0 else 'e'
    c = c[0] if len(c) > 0 else 'c'
    s = s[0] if len(s) > 0 else 's'
    g = g[0] if len(g) > 0 else 'g'

    m = m.rename(columns = {
        d: 'd',
        a: 'a',
        e: 'ebitda_adjusted',
        c: 'cogs_ex_da',
        s: 'sga_ex_sbc',
        g: 'ga',
        })

    # remove the last few "check" columns in canalyst model which confuse pandas with duplicate names
    m = m.iloc[:, 0:-5]

    # check we have ebitda adjusted (if not, then probably ebitda_adjusted_none is the right field
    if 'ebitda_adjusted_none' in m.columns:
        m['ebitda_adjusted'] = m.ebitda_adjusted_none

    if 'da' not in m.columns: m['da'] = m.d + m.a
    if 'ga' in m.columns: m['sga_ex_sbc'] = m.sga_ex_sbc + m.ga

    # Drop "other items" which often appears many times in Canalyst page
    m = m.drop(columns = ['other_items'])
    m.to_excel('debug.xlsx')

    # Split into two dataframes, one for quarters and one for fiscal years
    q = m[m.index.str.startswith('Q')].copy()
    f = m[m.index.str.startswith('F')].copy()

    # Change index to datetime (reformat Q for quarters and remove FY for years first)

    q.index = q.index.str.split('-').str.get(1) +  q.index.str.split('-').str.get(0)
    f.index = f.index.str.replace('FY', '')

    q.index = pd.to_datetime(q.index)
    f.index = pd.to_datetime(f.index)

    # Switch mrfp to date time format so that we can use it to index
    if mrfp.startswith('FY'): mrfp = pd.to_datetime(mrfp.rsplit('Y')[1])
    else: mrfp = pd.to_datetime(mrfp.split('-')[1] + mrfp.split('-')[0])

    # Cut off forward periods - often contains 0 that kill math in denominators
    forward = (q.index > mrfp)
    q = q.loc[~forward]
    forward = (f.index > mrfp)
    f = f.loc[~forward]

    # Working variables
    tax_rate = .3

    # P&L

    q['revenue_ltm'] = q.revenue.rolling(4).sum()
    f['revenue_ltm'] = f.revenue
    q['ebitda_ltm'] = q.ebitda_adjusted.rolling(4).sum()
    f['ebitda_ltm'] = f.ebitda_adjusted
    q['revenue_growth_3'] = (q.revenue_ltm / q.revenue_ltm.shift(12)) ** (1 / 3) - 1
    f['revenue_growth_3'] = (f.revenue_ltm / f.revenue_ltm.shift(3)) ** (1 / 3) - 1
    q['revenue_growth_max'] = q.revenue_growth_3.rolling(20).max()
    q['ebitda_growth_3'] = (q.ebitda_ltm / q.ebitda_ltm.shift(12)) ** (1 / 3) - 1
    f['ebitda_growth_3'] = (f.ebitda_ltm / f.ebitda_ltm.shift(3)) ** (1 / 3) - 1
    q['ebitda_margin_ltm'] = q.ebitda_ltm / q.revenue_ltm
    f['ebitda_margin_ltm'] = f.ebitda_ltm / f.revenue_ltm
    q['ebitda_margin_high_5'] = q.ebitda_margin_ltm.rolling(20).max()
    f['ebitda_margin_high_5'] = f.ebitda_margin_ltm.rolling(5).max()
    q['ebitda_avg_3'] = q.ebitda_ltm.rolling(12).mean()
    f['ebitda_avg_3'] = f.ebitda_ltm.rolling(3).mean()
    q['ebitda_ago_5'] = q.ebitda_ltm.shift(20)
    f['ebitda_ago_5'] = f.ebitda_ltm.shift(5)
    q['da_ltm'] = q.da.rolling(4).sum()
    f['da_ltm'] = f.da
    q['ebit_ltm'] = q.ebit.rolling(4).sum()
    f['ebit_ltm'] = f.ebit
    q['cogs'] = q.cogs_ex_da
    f['cogs'] = f.cogs_ex_da
    q['sga'] = q.sga_ex_sbc
    f['sga'] = f.sga_ex_sbc
    q['gross_profit'] = q.revenue - q.cogs
    f['gross_profit'] = f.revenue - f.cogs
    q['gross_profit_ltm'] = q.gross_profit.rolling(4).sum()
    f['gross_profit_ltm'] = f.gross_profit
    q['gm_ltm'] = q.gross_profit_ltm / q.revenue_ltm
    f['gm_ltm'] = f.gross_profit_ltm / f.revenue_ltm
    q['gm_high_5'] = q.gm_ltm.rolling(20).max()
    f['gm_high_5'] = f.gm_ltm.rolling(5).max()
    q['sga_ltm'] = q.sga.rolling(4).sum()
    f['sga_ltm'] = f.sga
    q['sgam_ltm'] = q.sga_ltm / q.revenue_ltm
    f['sgam_ltm'] = f.sga_ltm / f.revenue_ltm
    q['sgam_low_5'] = q.sgam_ltm.rolling(20).min()
    f['sgam_low_5'] = f.sgam_ltm.rolling(5).min()
    q['capex_ltm'] = q.capex.rolling(4).sum()
    f['capex_ltm'] = f.capex

    # Valuation

    q['ev'] = q.ev_avg.rolling(4).mean()
    f['ev'] = f.ev_avg
    q['market_cap'] = q.market_cap_avg.rolling(4).mean()
    f['market_cap'] = f.market_cap_avg

    key_stats = get_key_stats(ticker)
    q.loc[mrfp,'ev'] = key_stats.ev[0]
    q.loc[mrfp,'market_cap'] = key_stats.market_cap[0]
    q['total_debt'] = q.debt
    f['total_debt'] = f.debt
    q['net_debt_ltm'] = q.debt  - q.cash
    f['net_debt_ltm'] = f.debt  - f.cash
    q['cash_ltm'] = q.cash
    f['cash_ltm'] = f.cash

    # FCFE

    q['fcfe'] = q.fcf_pre_div
    f['fcfe'] = f.fcf_pre_div
    q['fcfe_ltm'] = q.fcfe.rolling(4).sum()
    f['fcfe_ltm'] = f.fcfe
    q['fcfe_to_market_cap'] = q.fcf_to_market_cap
    f['fcfe_to_market_cap'] = f.fcf_to_market_cap
    q['fcf_sum_3'] = q.fcf_pre_div.rolling(12).sum()
    f['fcf_sum_3'] = f.fcf_pre_div.rolling(3).sum()
    q['fcfe_avg_3'] = q.fcfe_ltm.rolling(12).mean()
    f['fcfe_avg_3'] = f.fcfe_ltm.rolling(3).mean()

    # IC and ROIC

    q['ic'] = q.ic_avg.rolling(4).mean()
    f['ic'] = f.ic_avg
    q['roic'] = q.roic
    f['roic'] = f.roic
    q['roic_high_5'] = q.roic.rolling(20).max()
    f['roic_high_5'] = f.roic.rolling(5).max()
    q['roic_avg_5'] = q.roic.rolling(20).mean()
    f['roic_avg_5'] = f.roic.rolling(5).mean()
    q['roic_ago_5'] = q.roic.shift(20)
    f['roic_ago_5'] = f.roic.shift(5)
    q['ic_delta_3'] = q.ic - q.ic.shift(12)
    f['ic_delta_3'] = f.ic - f.ic.shift(3)

    # Multiples

    q['ev_to_ebitda_ltm'] = q.ev / q.ebitda_ltm
    f['ev_to_ebitda_ltm'] = f.ev / f.ebitda_ltm
    q['ebitda_cagr_3'] = (q.ebitda_ltm / q.ebitda_ltm.shift(12)) ** (1 / 3) -1
    f['ebitda_cagr_3'] = (f.ebitda_ltm / f.ebitda_ltm.shift(3)) ** (1 / 3) -1
    q['ev_to_gross_profit_ltm'] = q.ev / q.gross_profit_ltm
    f['ev_to_gross_profit_ltm'] = f.ev / f.gross_profit_ltm
    q['net_debt_to_ebitda_ltm'] = q.net_debt_ltm / q.ebitda_ltm
    f['net_debt_to_ebitda_ltm'] = f.net_debt_ltm / f.ebitda_ltm

    # M&A cash
    # note acqisitions are negative numbers (use of cash) and divestitures are positive for receipt of cash
    q['cf_for_ma'] = q.acquisitions + q.divestitures
    f['cf_for_ma'] = f.acquisitions + f.divestitures
    q['cf_for_ma_ltm'] = q.cf_for_ma.rolling(4).sum()
    f['cf_for_ma_ltm'] = f.cf_for_ma
    q['cf_for_ma_sum_3'] = q.cf_for_ma.rolling(12).sum()
    f['cf_for_ma_sum_3'] = f.cf_for_ma.rolling(3).sum()


    # Shareholder capital issued (net of buybacks) and dividends paid

    q['shareholders'] = q.equity_issued + q.dividends
    f['shareholders'] = f.equity_issued + f.dividends
    q['shareholders_ltm'] = q.shareholders.rolling(4).sum()
    f['shareholders_ltm'] = f.shareholders
    q['shareholders_sum_3'] = q.shareholders.rolling(12).sum()
    f['shareholders_sum_3'] = f.shareholders.rolling(3).sum()

    # Debt issued, net of repaid

    q['financing_acquired'] = q.debt_issued
    f['financing_acquired'] = f.debt_issued
    q['financing_acquired_ltm'] = q.financing_acquired.rolling(4).sum()
    f['financing_acquired_ltm'] = f.financing_acquired
    q['net_debt_issued_sum_3'] = q.debt_issued.rolling(12).sum()
    f['net_debt_issued_sum_3'] = f.debt_issued.rolling(3).sum()


    # Earnings Power

    q['ep'] = (q.ebitda_adjusted + q.capex) * (1 - tax_rate)
    f['ep'] = (f.ebitda_adjusted + f.capex) * (1 - tax_rate)
    q['ep_ltm'] = q.ep.rolling(4).sum()
    f['ep_ltm'] = f.ep

    ## estimate of market value
    q['ep_market_cap'] = q.ep_ltm * 10 - q.net_debt_ltm
    f['ep_market_cap'] = f.ep_ltm * 10 - f.net_debt_ltm

    ## 3-year fcfe estimate of market value
    q['ep_value_from_fcfe'] = q.fcfe_avg_3 * 10
    f['ep_value_from_fcfe'] = f.fcfe_avg_3 * 10

    ## return to peak EBITDA estimate of market value
    q['ep_value_from_ebitda'] = ((q.ebitda_margin_high_5 - q.ebitda_margin_ltm) * q.revenue_ltm
            * 10
            * (1 - tax_rate)
            )
    f['ep_value_from_ebitda'] = ((f.ebitda_margin_high_5 - f.ebitda_margin_ltm)
            * f.revenue_ltm
            * 10
            * (1 - tax_rate)
            )

    ## value from achieveing peak 5-year roic
    q.ic_avg = q.ic_avg.replace(0, pd.NA)
    f.ic_avg = f.ic_avg.replace(0, pd.NA)
    q['ep_roic'] = q.ep_ltm / q.ic_avg
    f['ep_roic'] = f.ep_ltm / f.ic_avg
    q['ep_delta_3'] = q.ep_ltm - q.ep_ltm.shift(12)
    f['ep_delta_3'] = f.ep_ltm - f.ep_ltm.shift(3)
    q['ep_ic_delta_3'] = q.ep_delta_3 / q.ic_delta_3
    f['ep_ic_delta_3'] = f.ep_delta_3 / f.ic_delta_3
    q['ep_value_from_ic'] = q.ic_delta_3 * q.roic_high_5 * 10 - q.ic_delta_3
    f['ep_value_from_ic'] = f.ic_delta_3 * f.roic_high_5 * 10 - f.ic_delta_3

    ## Total value added from all sources
    q['ep_total_est_value'] = q.ep_market_cap + q.ep_value_from_fcfe + q.ep_value_from_ebitda + q.ep_value_from_ic
    f['ep_total_est_value'] = f.ep_market_cap + f.ep_value_from_fcfe + f.ep_value_from_ebitda + f.ep_value_from_ic

    # Update f with the ltm from q so that it too is a viable, full database
    try:
        f = f.drop(index = pd.to_datetime('2020'))
    except:
        print(f'Model has date {mrfp} and so can not drop 2020')


    f = f.append(q.loc[mrfp])

    # That's all folks - return the q and f dataframes
    return q, f, mrfp

def print_mb_report(ticker):
    """ This function prints Michael Braner's original report in his model import
    file to see if it all working correctly. It takes a ticker and a dataframe for q
    as definied in get_canalyst_model and returned by it second
    """
    # get the latest canalyst data in q, f, and m which are quarterly df, fiscal year df, and mrfp
    q, _f, mrfp = get_summary_page(ticker)

    # set display columns for potential value summary
    display_value_summary = [
            'revenue_ltm',
            'ebitda_ltm',
            'ebitda_margin_ltm',
            'capex_ltm',
            'ep_ltm',
            'revenue_growth_3',
            'ep_roic',
            'net_debt_ltm',
            'ep_market_cap',
            'fcfe_ltm',
            'fcfe_avg_3',
            'ep_value_from_fcfe',
            'ebitda_margin_high_5',
            'ep_value_from_ebitda',
            'ep_delta_3',
            'ic_delta_3',
            'roic_high_5',
            'ep_value_from_ic',
            'ep_ic_delta_3',
            'ep_total_est_value'
            ]

    # set display for potential value relative to current market cap
    key_stats = get_key_stats(ticker)
    market_cap = key_stats.market_cap[0]
    historic = get_historic_prices(ticker)
    last_price  = historic.last('1D').Close[0]

    # Format pandas output for floats
    pd.options.display.float_format = '{:,.2f}'.format
    # print some output
    print('\n\n')
    print(f'The model for {ticker} has been imported as of {mrfp}')
    print(f'The current market cap is ${market_cap:,.1f}M at ${last_price:,.2f}')
    print('\n')
    print(q.loc[mrfp][display_value_summary])
    print('\n')
    print('The estimated value from each source:')
    print('current ep:\t{0:.1f}x'.format(
        q.market_cap[mrfp]/market_cap))
    print('avg fcfe:\t{0:.1f}x'.format(
        q.ep_value_from_fcfe[mrfp]/market_cap))
    print('margin:\t\t{0:.1f}x'.format(
        q.ep_value_from_ebitda[mrfp]/market_cap))
    print('growth:\t\t{0:.1f}x'.format(q.ep_value_from_ic[mrfp]/market_cap))
    print('-----------\t----')
    print('total:\t\t{0:.1f}x'.format(
        q.ep_total_est_value[mrfp]/market_cap))

    return q

def update_fscores_with_canalyst(ticker):
    """
    This function takes a ticker and a directory where its latest Canalyst Model is stored
    and updates the master fscores database with the Canalyst information to be more accurate
    where we have downloaded a Canalyst model.  It does not return a value, but updates the fscores
    and replaces data for the ticker named and resaves fscores.xlsx
    """

    # Get the two master data sources from fscores and canalyst
    fscores = pd.read_excel('fscores.xlsx')
    fscores = fscores.set_index('symbol')

    # cq refers to canalyst quarterlies, cf to canalyst fiscals. function in cantest.py
    cq, cf, mrfp = get_summary_page(ticker)

    # Pull out a record to update for this ticker
    this_ticker = fscores.loc[ticker].copy()
    this_ticker = pd.DataFrame(this_ticker).T

    # For any columns in cq, update this_ticker. (Note: tried pd.update and errors)
    shared_columns = [i for i in this_ticker.columns if i in cq.columns]
    for col in shared_columns:
        this_ticker[col] = cq.loc[mrfp, col]

    # Update tests for this_ticker function in screen1.py
    this_ticker = run_eps(this_ticker)
    this_ticker = run_tests(this_ticker)

    # Update the time stamp of the data
    today = pd.to_datetime('today')
    this_ticker.date_of_data = today

    # update fscores and write it
    fscores.update(this_ticker)
    fscores.to_excel('fscores.xlsx')

    return cq, cf, mrfp, this_ticker


