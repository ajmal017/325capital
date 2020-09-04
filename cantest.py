#! /usr/bin/env python3
# get_canalyst_model.py
# This file defines functions to take a canalyst model and create
# a relevant set of financials in a dataframe.

import os
import sys

import openpyxl
import pandas as pd
import numpy as np

from getdata_325 import get_key_stats


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
    c = c.convert_dtypes()
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
            'Other Items': 'other_cf_items',
            'EBT': 'ebt',
            'Tax': 'tax',
            'Discontinued Operations': 'disc_ops',
            'Net Income to NCI': 'net_income_to_nci',
            'Preferred stock dividends': 'preferred_dividends',
            'Net Income from Continued Operation': 'opinc',
            'GAAP EPS': 'gaap_eps',
            'Adjusted EBITDA': 'ebitda_adjusted',
            'Adjusted EBITDA (No Adjustments)': 'ebitda_adjusted',
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
    if 'da' not in m.columns: m['da'] = m.d + m.a
    if 'ga' in m.columns: m['sga_ex_sbc'] = m.sga_ex_sbc + m.ga
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
    q['ebitda_ltm'] = q.ebitda_adjusted.rolling(4).sum()
    q['revenue_growth_3'] = (q.revenue_ltm / q.revenue_ltm.shift(12)) ** (1 / 3) - 1
    q['revenue_growth_max'] = q.revenue_growth_3.rolling(20).max()
    q['ebitda_growth_3'] = (q.ebitda_ltm / q.ebitda_ltm.shift(12)) ** (1 / 3) - 1
    q['ebitda_margin_ltm'] = q.ebitda_ltm / q.revenue_ltm
    q['ebitda_margin_high_5'] = q.ebitda_ltm.rolling(20).max()
    q['ebitda_avg_3'] = q.ebitda_ltm.rolling(12).mean()
    q['ebitda_ago_5'] = q.ebitda_ltm.shift(20)
    q['da_ltm'] = q.da.rolling(4).sum()
    q['ebit_ltm'] = q.ebit.rolling(4).sum()
    q['cogs'] = q.cogs_ex_da
    q['sga'] = q.sga_ex_sbc
    q['gross_profit'] = q.revenue - q.cogs
    q['gross_profit_ltm'] = q.gross_profit.rolling(4).sum()
    q['gm_ltm'] = q.gross_profit_ltm / q.revenue_ltm
    q['gm_high_5'] = q.gm_ltm.rolling(20).max()
    q['sga_ltm'] = q.sga.rolling(4).sum()
    q['sgam_ltm'] = q.sga_ltm / q.revenue_ltm
    q['sgam_low_5'] = q.sga_ltm.rolling(20).min()

    # Valuation

    q['ev'] = q.ev_avg.rolling(4).mean()
    q['market_cap'] = q.market_cap_avg.rolling(4).mean()

    key_stats = get_key_stats(ticker)
    q.loc[mrfp,'ev'] = key_stats.ev[0]
    q.loc[mrfp,'market_cap'] = key_stats.market_cap[0]
    q['total_debt'] = q.debt
    q['net_debt'] = q.debt  - q.cash
    q['cash_ltm'] = q.cash

    # FCFE

    q['fcfe'] = q.fcf_pre_div
    q['fcfe_ltm'] = q.fcfe.rolling(4).sum()
    q['fcfe_to_market_cap'] = q.fcf_to_market_cap
    q['fcf_sum_3'] = q.fcf_pre_div.rolling(12).sum()
    q['fcfe_avg_3'] = q.fcfe_ltm.rolling(12).mean()

    # IC and ROIC

    q['ic'] = q.ic_avg.rolling(4).mean()
    q['roic'] = q.roic
    q['roic_high_5'] = q.roic.rolling(20).max()
    q['roic_avg_5'] = q.roic.rolling(20).mean()
    q['roic_ago_5'] = q.roic.shift(20)
    q['ic_delta_3'] = q.ic - q.ic.shift(12)

    # Multiples

    q['ev_to_ebitda_ltm'] = q.ev / q.ebitda_ltm
    q['ebitda_cagr_3'] = (q.ebitda_ltm / q.ebitda_ltm.shift(12)) ** (1 / 3) -1
    q['ev_to_gross_profit_ltm'] = q.ev / q.gross_profit_ltm
    q['net_debt_to_ebitda_ltm'] = q.net_debt / q.ebitda_ltm

    # M&A cash
    # note acqisitions are negative numbers (use of cash) and divestitures are positive for receipt of cash
    q['cf_for_ma'] = q.acquisitions + q.divestitures
    q['cf_for_ma_ltm'] = q.cf_for_ma.rolling(4).sum()
    q['cf_for_ma_sum_3'] = q.cf_for_ma.rolling(12).sum()


    # Shareholder capital issued (net of buybacks) and dividends paid

    q['shareholders'] = q.equity_issued + q.dividends
    q['shareholders_ltm'] = q.shareholders.rolling(4).sum()
    q['shareholders_sum_3'] = q.shareholders.rolling(12).sum()

    # Debt issued, net of repaid

    q['financing_acquired'] = q.debt_issued
    q['financing_acquired_ltm'] = q.financing_acquired.rolling(4).sum()
    q['net_debt_issued_sum_3'] = q.debt_issued.rolling(12).sum()


    # Earnings Power

    q['ep'] = (q.ebitda_adjusted + q.capex) * (1 - tax_rate)
    q['ep_ltm'] = q.ep.rolling(4).sum()

    ## estimate of market value
    q['ep_market_cap'] = q.ep_ltm * 10 - q.net_debt

    ## 3-year fcfe estimate of market value
    q['ep_value_from_fcfe'] = q.fcfe_avg_3 * 10

    ## return to peak EBITDA estimate of market value
    q['ep_value_from_ebitda'] = ((q.ebitda_margin_high_5 - q.ebitda_margin_ltm)
            * q.revenue_ltm
            * 10
            * (1 - tax_rate)
            )

    ## value from achieveing peak 5-year roic
    q.ic_avg = q.ic_avg.replace(0, pd.NA)
    q['ep_roic'] = q.ep_ltm / q.ic_avg
    q['ep_delta_3'] = q.ep_ltm - q.ep_ltm.shift(12)
    q['ep_ic_delta_3'] = q.ep_delta_3 / q.ic_delta_3
    q['ep_value_from_ic'] = q.ic_delta_3 * q.roic_high_5 * 10 - q.ic_delta_3

    ## Total value added from all sources
    q['ep_total_est_value'] = q.ep_market_cap + q.ep_value_from_fcfe + q.ep_value_from_ebitda + q.ep_value_from_ic

    # That's all folks - return the q and f dataframes
    return q, f, mrfp
