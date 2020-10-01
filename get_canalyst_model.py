#! /usr/bin/env python3
# get_canalyst_model.py
# This file defines functions to take a canalyst model and create
# a relevant set of financials in a dataframe.

import os
import sys

import openpyxl
import pandas as pd

from getdata_325 import get_key_stats
from cantest import get_summary_page
from screen1 import run_tests


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

    # Return the first distionary entry [0] and then the first entry of key/value pair which is the filename [0]
    return files[0][0]


def get_canalyst_model(ticker, directory):
    """ This function takes a filename of a Canalyst model and returns a dataframe with
    the latest financial information for that file. It uses function get_latest_file_for_ticker
    It returns two more dataframes called q for quarterly data and fy for fiscal year,
    and importantly, the mrfp that these dataframes are relevant for
    """

    # Get the latest date of the model using openpyxl and MO.MRFP field in canalyst models
    # set up the working file with path
    filename = directory + '/' + get_latest_file_for_ticker(ticker, directory)
    workbook = openpyxl.load_workbook(filename)

    # Select the range where MO.MRFP or the last date of the model is stored in Canalyst models
    # MRFP_range will then have a list of the sheet and the range of the date (but with $ signs)
    MRFP_range = workbook.defined_names['MO.MRFP'].attr_text.split('!')

    # The last date is in the workbook[sheetname][range].value have to remember to remove the $
    mrfp = workbook[MRFP_range[0]][MRFP_range[1].replace("$", '')].value

    # create a pandas dataframe from the Model sheet of the Canalyst file
    can_model = pd.read_excel(filename, sheet_name='Model', header=4, index_col=0)
    print(f'Imported the {ticker} model from {filename} with date {mrfp}')

    # drop blank rows
    temp_model = can_model[can_model.index.notnull()]

    # drop blank columns
    temp_model = temp_model.loc[:, ~temp_model.columns.str.startswith('Unn')]

    # create list of section names in preparation for adding second index
    section_names = {
        'Growth Analysis': 'growth',
        'Margin Analysis': 'margin',
        'Segmented Results Breakdown (FS)': 'segments',
        'Key Metrics - Backlog (FS)': 'backlog',
        'Segmented Results Breakdown - Historical (FS)': 'segments_historical',
        'Income Statement - As Reported': 'is',
        'Adjusted Numbers - As Reported': 'adj_is',
        'GAAP EPS': 'eps',
        'Revised Income Statement': 'ris',
        'Cash Flow Summary': 'cf_sum',
        'Balance Sheet Summary': 'bs_sum',
        'Valuation': 'valuation',
        'Cumulative Cash Flow Statement': 'cum_cf',
        'Cash Flow Statement': 'cf',
        'Working Capital Forecasting': 'wc',
        'Current Assets': 'bs_ca',
        'Current Assets': 'bs_ca',
        'Non-Current Assets': 'bs_nca',
        'Current Liabilities': 'bs_cl',
        'Non-Current Liabilities': 'bs_ncl',
        "Shareholders' Equity": 'bs_se',
        'Model Checks': 'model_checks',
        'Other Tables': 'other_tables'
    }

    # Set initial section index to 'misc' to capture variability of the models in the initial sections
    current_section = 'misc'

    # Loop through the column list and create a corresponding list of the section names
    section_index = []
    fields_imported = temp_model.index
    for field in fields_imported:
        if field in section_names.keys():
            current_section = section_names[field]
        section_index.append(current_section)

    # add the section_index to temp_model
    temp_model['section'] = section_index

    # drop the rows where the section and index are identical
    temp_model = temp_model[temp_model.section != temp_model.index]

    # create standard field names and add to temp_model
    fields = pd.Series(temp_model.index)
    fields = fields.str.lower()
    fields = fields.str.replace(' ', '_')
    fields = fields.str.replace('(', '')
    fields = fields.str.replace(')', '')
    fields = temp_model.section.values + '_' + fields

    # take care of any remaining duplicate index items
    for dup in fields[fields.duplicated()].unique():
        fields[fields[fields == dup].index.values.tolist()] = [dup + '.' + str(i) if i != 0 else dup for i in range(
            sum(fields == dup))]  # left side items by row no / right side the numbered names

    temp_model['std_field'] = fields.values

    # reset index and then set indexe to 'std_field'
    # possible to set second index of 'section', but cell selection seems to get much more complicated
    # temp_model.reset_index()
    temp_model = temp_model.set_index('std_field')

    # set index and column titles
    temp_model.columns.names = ['period']

    # Transpose the model so that the periods become the row index and remove forward
    m = temp_model.T
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
    mrfp = pd.to_datetime(mrfp.split('-')[1] + mrfp.split('-')[0])

    # Cut off forward periods - often contains 0 that kill math in denominators
    forward = (q.index > mrfp)
    q = q.loc[~forward]
    forward = (f.index > mrfp)
    f = f.loc[~forward]

    # series to allow for checks of field names
    fields = pd.Series(q.columns)

    # Set tax rate
    tax_rate = .3

    # Revenue and growth

    q['revenue_ltm'] = q.ris_net_revenue.rolling(4).sum()
    f['revenue_ltm'] = f.ris_net_revenue
    q['revenue_growth_3'] = (q.revenue_ltm / q.revenue_ltm.shift(12))**(1/3) - 1

    # EBITDA and margins

    if 'ris_adjusted_ebitda' not in fields.values:
        colname = q.columns[q.columns.str.startswith('ris_adjusted_ebitda')].values.tolist()
        q['ris_adjusted_ebitda'] = q[colname]
    q['ebitda_ltm'] = q.ris_adjusted_ebitda.rolling(4).sum()
    f['ebitda_ltm'] = f.ris_adjusted_ebitda
    q['ebitda_margin_ltm'] = q['ebitda_ltm'] / q['revenue_ltm']
    f['ebitda_margin_ltm'] = f['ebitda_ltm'] / f['revenue_ltm']
    q['ebitda_margin_high_5'] = q.ebitda_margin_ltm.rolling(20).max()
    f['ebitda_margin_high_5'] = f.ebitda_margin_ltm.rolling(5).max()
    q['da'] = q.cum_cf_depreciation_and_amortization.rolling(4).sum()
    f['da'] = f.cum_cf_depreciation_and_amortization
    if 'adj_is_adjusted_income_from_operations' not in fields.values:
        colname = q.columns[
                (q.columns.str.contains('operating')) &
                (q.columns.str.contains('income'))
                ].values.tolist()
        q['adj_is_adjusted_income_from_operations'] = q[colname]
        f['adj_is_adjusted_income_from_operations'] = f[colname]
    q['ebit'] = q.adj_is_adjusted_income_from_operations
    f['ebit'] = f.adj_is_adjusted_income_from_operations
    q['gross_profit_ltm'] = q.ris_gross_profit.rolling(4).sum()
    f['gross_profit_ltm'] = f.ris_gross_profit
    q['gm_ltm'] = q.gross_profit_ltm / q.revenue_ltm
    q['sga_ltm'] = q['ris_sg&a_adj._for_sbc'].rolling(4).sum()
    f['sga_ltm'] = f['ris_sg&a_adj._for_sbc']
    q['sgam_ltm'] = q.sga_ltm / q.revenue_ltm
    f['sgam_ltm'] = f.sga_ltm / f.revenue_ltm

    # Valuation and market_cap

    f['ev'] = f['valuation_enterprise_value_-_avg']
    q['ev'] = q['valuation_enterprise_value_-_avg']
    q['market_cap'] = q['valuation_market_cap_-_avg']
    f['market_cap'] = f['valuation_market_cap_-_avg']

    # Replace latest wtih live data from Yahoo

    key_stats = get_key_stats(ticker)
    q.loc[mrfp, 'ev'] = key_stats.ev[0]
    q.loc[mrfp, 'market_cap'] = key_stats.market_cap[0]

    # Debt

    q['total_debt_ltm'] = q.bs_sum_debt
    q['net_debt_ltm'] = q.bs_sum_net_debt
    f['net_debt_ltm'] = f.bs_sum_net_debt
    q['cash_ltm'] = q.bs_sum_cash

    # Free cash flow to equity

    q['fcfe'] = q['cf_net_cfo'] + q['cf_sum_capex']
    f['fcfe'] = f['cf_net_cfo'] + f['cf_sum_capex']
    q['fcfe_ltm'] = q.fcfe.rolling(4).sum()
    q['fcfe_to_marketcap'] = q.fcfe / q.market_cap
    f['fcfe_to_marketcap'] = f.fcfe / f.market_cap
    q['fcfe_sum_3'] = q.fcfe.rolling(12).sum()

    # Capex and operating and investing cash flow

    q['capex_ltm'] = q.cf_sum_capex.rolling(4).sum()
    q['capex_avg_3'] = q.capex_ltm.rolling(12).mean()
    q['capex_ago_5'] = q.capex_ltm.shift(20)
    q['ocf_ltm'] = q.cum_cf_net_cfo.rolling(4).sum()
    q['icf_ltm'] = q.cum_cf_net_cfi.rolling(4).sum()
    q['icf_avg_3'] = q.icf_ltm.rolling(12).mean()
    q['icf_avg_3_to_fcf'] = q.icf_avg_3 / q.fcfe_ltm
    q['capex_to_ocf'] = q.capex_ltm / q.ocf_ltm
    q['financing_acquired'] = q.cum_cf_net_cff.rolling(4).sum()
    q['capex_to_revenue_ltm'] = q.capex_ltm / q.revenue_ltm
    q['capex_to_revenue_avg_3'] = q.capex_to_revenue_ltm.rolling(12).mean()

    # IC and ROIC

    q['ic'] = q.bs_sum_net_debt + q.bs_se_total_se
    f['ic'] = f.bs_sum_net_debt + f.bs_se_total_se
    q['roic'] = q.ebit * (1 - tax_rate) / q.ic
    f['roic'] = f.ebit * (1 - tax_rate) / f.ic
    q['avg_ic'] = (q.ic + q.ic.shift(2) + q.ic.shift(3) + q.ic.shift(4)) / 4
    q['roic_high_5'] = q.roic.rolling(20).max()
    q['roic_avg_5'] = q.roic.rolling(20).mean()
    q['ic_delta_3'] = q.ic - q.ic.shift(12)

    # Multiples

    q['ev_to_ebitda_ltm'] = q.ev / q.ebitda_ltm
    f['ev_to_ebitda_ltm'] = f.ev / f.ebitda_ltm
    f['ebitda_cagr_3'] = (f.ris_adjusted_ebitda / f.ris_adjusted_ebitda.shift(3)) ** (1 / 3) - 1
    q['ev_to_gm_ltm'] = q.ev / q.gross_profit_ltm
    f['ev_to_gm_ltm'] = f.ev / f.gross_profit_ltm
    q['net_debt_to_ebitda_ltm'] = q.net_debt_ltm / q.ebitda_ltm
    f['net_debt_to_ebitda_ltm'] = f.net_debt_ltm / f.ebitda_ltm

    # M & A

    q['cf_for_ma'] = q['cf_sum_acquisitions'] +  q['cf_sum_divestiture']
    q['cf_for_ma_ltm'] = q.cf_for_ma.rolling(4).sum()
    q['cf_for_ma_sum_3'] = q.cf_for_ma.rolling(12).sum()

    # shareholder cash flows
    repurchases = q.columns[
            (q.columns.str.contains('repurchses')) &
            (q.columns.str.contains('common'))
            ].values.tolist()
    issuance = q.columns[
            (q.columns.str.contains('issuance')) &
            (q.columns.str.contains('common'))
            ].values.tolist()
    q['common_repurchases'] = q[repurchases]
    q['common_issuance'] = q[issuance]

    if 'cf_sum_net_share_issuance_buybacks' not in fields.values:
        # consider setting up 'startswith' search then summing in for loop?
        q['cf_net_share_issuance_buybacks_sum'] = q.cf_common_stock_repurchases +  q.cf_common_stock_issuance
    q['shareholders'] = q['cf_sum_dividend_paid'] +  q['cf_sum_net_share_issuance_buybacks']
    q['shareholders_ltm'] = q.shareholders.rolling(4).sum()
    q['shareholders_sum_3'] = q.shareholders.rolling(12).sum()

    # Financing with Debt and Equity

    # if summary field missing, then create it from source data on cash flow statement
    if 'cf_sum_net_debt_issuance_repayment' not in fields.values:
        cols = q.columns[q.columns.str.startswith('cf_borrowings') | q.columns.str.startswith('cf_repayment')].values.tolist()
        colnum = [q.columns.get_loc(c) for c in cols]
        colsum = pd.Series(dtype='float')
        for i in colnum:
            if colsum.empty:
                colsum = pd.Series(q.iloc[:, i])
            else:
                colsum = colsum + pd.Series(q.iloc[:, i])
        q['cf_sum_net_debt_issuance_repayment'] = colsum
    q['financing_aqcuired'] = q.cf_sum_net_debt_issuance_repayment.rolling( 4).sum()
    q['net_debt_issued_sum_3'] = q.cf_sum_net_debt_issuance_repayment.rolling( 12).sum()

    # Earnings Power

    q['ep'] = (q.ris_adjusted_ebitda + q.cf_sum_capex) * (1 - tax_rate)
    f['ep_ltm'] = (f.ris_adjusted_ebitda + f.cf_sum_capex) * (1 - tax_rate)
    q['ep_ltm'] = q.ep.rolling(4).sum()

    ## EP estimate  of market value
    q['ep_market_cap'] = q.ep_ltm * 10 - q.bs_sum_net_debt

    ## FCFE 3-year estimate of market value
    q['fcfe_avg_3'] = q.fcfe_sum_3 / 3
    q['value_from_fcfe'] = q.fcfe_avg_3 * 10

    # est market value from return to peak EBITDA margins
    q['value_from_ebitda_margin'] = (q.ebitda_margin_high_5 - q.ebitda_margin_ltm) * q.revenue_ltm * 10 * (1 - tax_rate)
    f['value_from_ebitda_margin'] = (f.ebitda_margin_high_5 - f.ebitda_margin_ltm) * f.revenue_ltm * 10 * (1 - tax_rate)

    # value from achieving peak 5-year ROIC on last 3 year change in IC
    q['ep_roic'] = q.ep_ltm / q.avg_ic
    f['ep_roic'] = f.ep_ltm / f.ic
    q['ep_delta_3'] = q.ep_ltm - q.ep_ltm.shift(12)
    q['ep_ic_delta_3'] = q.ep_delta_3 / q.ic_delta_3
    q['value_from_ic'] = q.ic_delta_3 * q.roic_high_5 * 10 - q.ic_delta_3

    # Total estimated value from all sources
    q['total_est_value'] = q.ep_market_cap + q.value_from_fcfe + q.value_from_ebitda_margin + q.value_from_ic

    # Add mrfp to fiscal database after removing spurious 2020
    f = f.loc[~(f.index == '2020')]
    f = f.append(q.loc[mrfp])

    # Update rolling/over-time items in f
    f['gm_high_5'] = f['margin_gross_margin_including_d&a,_%'].rolling(5).max()
    q['low_fcfe_to_historical'] = q.fcfe_to_marketcap / f.fcfe_to_marketcap.rolling(5).max()
    f['ic_delta_3'] = f.ic - f.ic.shift(3)
    f['roic_avg_5'] = f.roic.rolling(5).mean()
    f['roic_ago_5'] = f.roic.shift(5)
    f['roic_high_5'] = f.roic.rolling(5).max()
    f['ebitda_cagr_to_evx'] = f.ebitda_cagr_3.rolling(3).max() / f.ev_to_ebitda_ltm
    f['sgam_low_5'] = f.sgam_ltm.rolling(5).min()
    f['revenue_growth_3'] = (f.revenue_ltm / f.revenue_ltm.shift(3)) ** (1 / 3) - 1
    f['revenue_growth_max'] = f.revenue_growth_3.rolling(5).max()
    f['ebitda_avg_3'] = f.ebitda_ltm.rolling(3).mean()
    f['ebitda_ago_5'] = f.ebitda_ltm.shift(5)

    # That's all folks - return the quarterly, fiscal, and mrfp
    return q, f, mrfp


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
    this_ticker = run_tests(this_ticker)

    # update fscores and write it
    fscores.update(this_ticker)
    fscores.to_excel('fscores.xlsx')

    return cq, cf, mrfp, this_ticker


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


    # print some output
    print('\n\n')
    print(f'The model for {ticker} has been imported as of {mrfp}')
    print('The current market cap is ${0:,.0f}mm'.format(market_cap))
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
    print('growth:\t\t{0:.1f}x'.format(q.value_from_ic[mrfp]/market_cap))
    print('-----------\t----')
    print('total:\t\t{0:.1f}x'.format(
        q.ep_total_est_value[mrfp]/market_cap))

    return q
