# getdata_325.py
# This file holds a large list of useful functions used in 325 capital
# to read and write data from various websites and excel formats
# Including from xbrlus.org, yahoo.finance.com, and spreadsheets that contain yahoo,
# fidelity.com and other data in their down load formats
# This note was written on August 04, 2020

# Get the required packages
from matplotlib.ticker import (PercentFormatter)
import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
import re
import logging

# Set up some convenience settings
pd.set_option('display.max_rows', 900)
pd.set_option('display.max_seq_items', 900)

# Set up graphics standards
plt.style.use('325.mplstyle')

def get_token():

    import requests

    # Where to get the token for xbrl.us
    authentication_url = "https://api.xbrl.us/oauth2/token"

    # data required to request the token
    client_id = "b5ba00b7-aed1-469b-a109-a3b09ca11d55"
    client_secret = "5c644800-3484-45dc-9d98-9e33fb76a387"
    username = "ashrivastava@325capital.com"
    password = "5gXGS9D2Dx4p"
    grant_type = "password"
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    authentication_payload = {'grant_type': "password", 'client_id': client_id,
                              'client_secret': client_secret, 'username': username, 'password': password}

    # request and return the token received
    r = requests.post(authentication_url,
                      data=authentication_payload, headers=headers)

    return r.json()["access_token"]


def get_xbrl_data(ticker, line_item, period):

    from bs4 import BeautifulSoup
    import re
    import json
    import re
    import requests
    import pandas as pd

    # source url
    source_url = "https://api.xbrl.us"

    # base url for a fact search

    fact_url = "/api/v1/fact/search"
    report_url = "/api/v1/report/search"
    concept = "/api/v1/concept/search"

    # headers with token
    token = get_token()
    headers = {"Authorization": "Bearer " +
               token, 'Content-type': 'application/json'}

    # get the CIK from Sec.gov
    url = "https://www.sec.gov/cgi-bin/browse-edgar?ticker=" + \
        ticker + "&action=getcompany"
    r = requests.get(url)
    tree = BeautifulSoup(r.text, 'lxml')
    CIK_span = tree.find('span', class_="companyName")
    CIK = re.split(' ', CIK_span.find('a').string)[0]

    period_field = "Y"
    period_years = "2007,2008,2009,2010,2011,2012,2013,2014,2015,2016,2017,2018,2019,2020"
    limit = 5
    if period == "LTM":
        period_field = "1Q, 2Q, 3Q, 4Q"
        period_years = "2018, 2019"
        limit = 4

    # set up the field results dictionary
    fact_request_dictionary = {
        "fact.has-dimensions": "false",
        "concept.local-name": line_item,
        "period.fiscal-period": period_field,
        "entity.cik": CIK,
        "fact.ultimus-index": "1",
        "period.fiscal-year": period_years,
        "fields":
        "period.fiscal-year.sort(ASC), \
                                    period.fiscal-period, \
                                    fact.value, \
                                    report.entry-url, \
                                    concept.local-name, \
                                    fact.limit(" + str(limit)
    }
    r = requests.get(source_url + fact_url,
                     params=fact_request_dictionary, headers=headers)

    if 'error' in r.json():
        return {}
    else:
        data = r.json()['data']

    # go through and create a dict by year
    results = {}
    for dict in data:
        period = str(dict['period.fiscal-year'])
        results[period] = [dict['fact.value']]

    # create a dataframe from the dict
    linedf = pd.DataFrame.from_dict(results)

    return linedf.T


def get_xbrl_lineitems(ticker):

    line_items = {
        "Revenue": "RevenuesAbstract,RevenueFromContractWithCustomerExcludingAssessedTax, RevenueFromContractWithCustomerIncludingAssessedTax, Revenues, SalesRevenueNet, ContractsRevenue",
        "GrossProfit": "GrossProfit",
        "COGS": "CostOfRevenueAbstract, CostOfGoodsAndServicesSold",
        "GA": "GeneralAndAdministrativeExpense",
        "SM": "SellingAndMarketingExpense",
        "SGA": "SellingGeneralAndAdministrativeExpense,SellingGeneralAndAdminstrativeExpensesMember",
        "RD": "ResearchAndDevelopmentExpense",
        "Preferred": "PreferredStockValue",
        "OneTimes": "RestructuringCharges",
        "OpInc": "OperatingIncomeLoss, IncomeLossFromContinuingOperationsBeforeInterestExpenseInterestIncomeIncomeTaxesExtraordinaryItemsNoncontrollingInterestsNet, IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest",
        "Int": "InterestExpense, InterestIncomeExpenseNet",
        "Tax": "IncomeTaxExpenseBenefit",
        "OpCF": "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations, NetCashProvidedByUsedInOperatingActivities",
        "NetInc": "NetIncomeLossAvailableToCommonStockholdersBasic, NetIncomeLoss, ProfitLoss",
        "CF": "CashAndCashEquivalentsPeriodIncreaseDecrease",
        "AcqCF": "PaymentsToAcquireBusinessesNetOfCashAcquired",
        "DivestCF": "ProceedsFromDivestitureOfBusinesses,GainLossOnSaleOfBusiness, ProceedsFromDivestitureOfBusinessesNetOfCashDivested",
        "StockComp": "StockGrantedDuringPeriodValueSharebasedCompensation, StockIssuedDuringPeriodValueShareBasedCompensation, ShareBasedCompensation",
        "DA": "DepreciationDepletionAndAmortization, DepreciationAndAmortization",
        "Capex": "PaymentsToAcquireProductiveAssets, PaymentsToAcquirePropertyPlantAndEquipment",
        "SharesOut": "WeightedAverageNumberOfSharesOutstandingBasic, NumberOfSharesOutstanding, WeightedAverageNumberOfShareOutstandingBasicAndDiluted",
        "EPS": "EarningsPerShareBasic, EarningsPerShare",
        "Dividends": "DividendsCommonStockCash",
        "SharePrice": "SharePrice",
        "Cash": "CashAndCashEquivalentsAtCarryingValue, CashAndCashEquivalents",
        "LTDebtCur": "LongTermDebtCurrent",
        "OpLeases": "OperatingLeaseLiability",
        "LTDebtNonCur": "LongTermDebtNoncurrent, LongTermLineOfCredit,LongTermDebtAndCapitalLeaseObligations",
                        "AssetsCur": "AssetsCurrent",
                        "LiabilitiesCur": "LiabilitiesCurrent",
                        "StockholdersEq": "StockholdersEquity"
    }

    import pandas as pd

    dfannual = pd.DataFrame()
    for line_item, tags in line_items.items():
        dfitem = get_xbrl_data(ticker, tags, "Annual")
        if not dfitem.empty:
            dfitem.columns = [line_item]
            dfannual = pd.merge(
                dfannual, dfitem, left_index=True, right_index=True, how='outer')
        else:
            dfannual[line_item] = 0

    dfannual = dfannual.apply(pd.to_numeric)

    dfannual.fillna(value=0, inplace=True)
    dfannual = dfannual / 1000000

    dfannual['Int'] = abs(dfannual['Int'])
    # dfannual['OpInc'] = dfannual['OpInc'] + dfannual['OneTimes']
    dfannual['EBITDA'] = dfannual['OpInc'] + dfannual['DA']
    dfannual['AdjEBITDA'] = dfannual['EBITDA'] + dfannual['StockComp']
    # dfannual['MarketCap'] = dfannual['SharePrice'] * dfannual['SharesOut']
    # dfannual['TEV'] = dfannual['MarketCap'] + dfannual['LTDebtNonCur'] + dfannual['LTDebtCur'] + dfannual['OpLeases']+ dfannual['Preferred'] - dfannual['Cash']
    # dfannual['Multiple'] = dfannual['TEV'] / dfannual['EBITDA']

    return dfannual.sort_index()

    # Set up the excel import


def getasheet(filenames, sheets, index_name):

    df = pd.DataFrame()
    for f in filenames:
        dftemp = pd.DataFrame()
        for sheet in sheets:
            sheet_name = sheet
            header = sheets[sheet][0]
            usecols = sheets[sheet][1]
            nrows = sheets[sheet][2]
            na_filter = True
            nextdf = pd.read_excel(
                io=f,
                sheet_name=sheet_name,
                header=header,
                usecols=usecols,
                nrows=nrows,
                na_filter=na_filter)
            nextdf.set_index(index_name, inplace=True)

            # concat sheet to main dataframe
            dftemp = pd.concat((dftemp, nextdf), axis=1)
        df = pd.concat((df, dftemp), axis=0)

    print("read the data {}".format(filenames))
    return df


def get_master_screen_sheets(name):

    # enable windows filestructure handling
    filename = "../325 Capital Screen Master.xlsm"

    sheet_name = name
    header = 5-1  # header names start on row 5 but 0 indexed is 6
    usecols = "A:GD"
    nrows = 642-5  # rows of data including the header
    na_filter = True
    df = pd.read_excel(
        io=filename,
        sheet_name=sheet_name,
        header=header,
        usecols=usecols,
        nrows=nrows,
        na_filter=na_filter)
    df.set_index("short_ticker", inplace=True)
    df['last_work'] = pd.Categorical(df['last_work'])
    df['tamale_status'] = pd.Categorical(df['tamale_status'])
    print("read the data from {}".format(name))

    return df


def get_fidelity_sheets(filenames):

    df = pd.DataFrame()
    for filen in filenames:
        dftemp = pd.DataFrame()
        # enable windows filestructure handling
        sheets = {
            "Search Criteria": "A:D",
            "Basic Facts": "A:J",
            "Performance & Volatility": "A:F",
            "Valuation, Growth & Ownership": "A:K",
            "Analyst Opinions": "A:I"}
        for sheet in sheets:
            sheet_name = sheet
            header = 0  # header names start on row 5 but 0 indexed is 6
            usecols = sheets[sheet]
            nrows = 500
            if filen == "../sc5.xls":
                nrows = 179
            na_filter = True
            nextdf = pd.read_excel(
                io=filen,
                sheet_name=sheet_name,
                header=header,
                usecols=usecols,
                nrows=nrows,
                na_filter=na_filter)
            nextdf.set_index('Symbol', inplace=True)
            # concat sheet to main dataframe
            dftemp = pd.concat((dftemp, nextdf), axis=1)
        df = pd.concat((df, dftemp), axis=0)
    print("read the data {}".format(filenames))
    return df


def getyahoosheet(filenames):

    df = pd.DataFrame()
    for filen in filenames:
        dftemp = pd.DataFrame()
        # enable windows filestructure handling
        sheets = {"Financials": "A:BH"}
        for sheet in sheets:
            sheet_name = sheet
            header = 0  # header names start on row 5 but 0 indexed is 6
            usecols = sheets[sheet]
            nrows = 2145
            na_filter = True
            nextdf = pd.read_excel(
                io=filen,
                sheet_name=sheet_name,
                header=header,
                usecols=usecols,
                nrows=nrows,
                na_filter=na_filter)
            nextdf.set_index('ticker', inplace=True)
            # concat sheet to main dataframe
            dftemp = pd.concat((dftemp, nextdf), axis=1)
        df = pd.concat((df, dftemp), axis=0)
    print("read the data")
    return df


def get_historic_prices(ticker):

    import yfinance as yf

    base = yf.Ticker(ticker)

    # put in the stock prices for year end and LTM
    hist = pd.DataFrame(base.history(period="10Y"))

    return hist


def get_analysis(symbol):

    tgt = r'https://sg.finance.yahoo.com/quote/{}/analysis?p={}'.format(
        symbol, symbol)
    df_list = pd.read_html(tgt)

    for i in analysis[1].index:
        for k in analysis[1].keys():
            if (isinstance(analysis[1].loc[i][k], str)):
                if (re.search(r'\dM$', analysis[1].loc[i][k])):
                    analysis[1].loc[i][k] = float(
                        analysis[1].loc[i][k][0: len(analysis[1].loc[i][k])-1].replace(',', ''))
                elif (re.search(r'\dk$', analysis[1].loc[i][k])):
                    analysis[1].loc[i][k] = .001 * float(
                        analysis[1].loc[i][k][0: len(analysis[1].loc[i][k])-1].replace(',', ''))
                elif (re.search(r'\dB$', analysis[1].loc[i][k])):
                    analysis[1].loc[i][k] = 1000 * float(
                        analysis[1].loc[i][k][0: len(analysis[1].loc[i][k])-1].replace(',', ''))
                elif (re.search(r'\d%$', analysis[1].loc[i][k])):
                    analysis[1].loc[i][k] = .01 * float(
                        analysis[1].loc[i][k][0: len(analysis[1].loc[i][k])-1].replace(',', ''))

    return df_list


def get_holders(symbol):

    tgt = r'https://sg.finance.yahoo.com/quote/{}/holders?p={}'.format(
        symbol, symbol)
    df_list = pd.read_html(tgt)

    return df_list


def get_profile(symbol):

    tgt = r'https://sg.finance.yahoo.com/quote/{}/profile?p={}'.format(
        symbol, symbol)
    df_list = pd.read_html(tgt)

    return df_list


def get_key_stats(ticker):

    # set tgt url to the location at yahoo finance with the ticker's info
    tgt = r'https://sg.finance.yahoo.com/quote/{}/key-statistics?p={}'.format(
        ticker, ticker)

    df_list = pd.read_html(tgt)
    resultdf = df_list[0]
    for df in df_list[1:]:
        resultdf = resultdf.append(df)

    resultdf.set_index(0, inplace=True)

    for i in resultdf.index:
        if (isinstance(resultdf.loc[i, 1], str)):
            if (re.search(r'\dM$', resultdf.loc[i, 1])):
                resultdf.loc[i, 1] = float(
                    resultdf.loc[i, 1].replace(',', '').replace('M', ''))
            elif (re.search(r'\dB$', resultdf.loc[i, 1])):
                resultdf.loc[i, 1] = pd.to_numeric(
                    resultdf.loc[i, 1].replace(',', '').replace('B', '')) * 1000
            elif (re.search(r'\dk$', resultdf.loc[i, 1])):
                resultdf.loc[i, 1] = pd.to_numeric(
                    resultdf.loc[i, 1].replace(',', '').replace('k', '')) * 0.001
            elif (re.search(r'\d%$', resultdf.loc[i, 1])):
                resultdf.loc[i, 1] = pd.to_numeric(
                    resultdf.loc[i, 1].replace(',', '').replace('%', '')) * 0.01
        #    if (re.search(r'\dM$', result_df.loc[i][1])):
        #        result_df.loc[i][1] = float(
        #                result_df.loc[i][1][0: len(result_df.loc[i][1])-1].replace(',', ''))
        #    elif (re.search(r'\dk$', result_df.loc[i][1])):
        #        result_df.loc[i][1] = .001 * float(
        #                result_df.loc[i][1][0: len(result_df.loc[i][1])-1].replace(',', ''))
        #    elif (re.search(r'\dB$', result_df.loc[i][1])):
        #        result_df.loc[i][1] = 1000 * float(
        #                result_df.loc[i][1][0: len(result_df.loc[i][1])-1].replace(',', ''))
        #    elif (re.search(r'\d%$', result_df.loc[i][1])):
        #        result_df.loc[i][1] = .01 * float(
        #              result_df.loc[i][1][0: len(result_df.loc[i][1])-1].replace(',', ''))

    returndf = resultdf.T.set_index(pd.Series(ticker))

    new_names = {'Market cap (intra-day) 5': 'market_cap',
                 'Enterprise value 3': 'ev',
                 'Trailing P/E': 'pe_ltm',
                 'Forward P/E 1': 'pe_ntm',
                 'PEG Ratio (5 yr expected) 1': 'peg_expected_forward',
                 'Price/sales (ttm)': 'ps_ltm',
                 'Price/book (mrq)': 'pb_mrq',
                 'Enterprise value/revenue 3': 'ev_to_revenue_ltm',
                 'Enterprise value/EBITDA 6': 'ev_to_ebitda_ltm',
                 'Beta (5Y monthly)': 'beta_5',
                 '52-week change 3': 'price_change_52',
                 'S&P500 52-week change 3': 'price_change_sp500_52',
                 '52-week high 3': 'price_high_52',
                 '52-week low 3': 'price_low_52',
                 '50-day moving average 3': 'price_avg_50_day',
                 '200-day moving average 3': 'price_average_200_day',
                 'Avg vol (3-month) 3': 'vol_avg_3_mo',
                 'Avg vol (10-day) 3': 'vol_avg_10_day',
                 'Shares outstanding 5': 'so',
                 'Float': 'float',
                 '% held by insiders 1': 'insider_percent',
                 '% held by institutions 1': 'insitution_percent',
                 'Shares short (28 May 2020) 4': 'shares_short_apr15',
                 'Short ratio (28 May 2020) 4': 'short_ratio_april15',
                 'Short % of float (28 May 2020) 4': 'shares_short_percent_float_apr15',
                 'Short % of shares outstanding (28 May 2020) 4': 'shares_short_outstanding_apr15',
                 'Shares short (prior month 29 Apr 2020) 4': 'shares_short_prior_month_may',
                 'Forward annual dividend rate 4': 'dividend_annual_forward',
                 'Forward annual dividend yield 4': 'dividend_yield_annual_forward',
                 'Trailing annual dividend rate 3': 'dividend_rate_ltm',
                 'Trailing annual dividend yield 3': 'dividend_yield_ltm',
                 '5-year average dividend yield 4': 'dividend_yield_avg_5',
                 'Payout ratio 4': 'payout_ratio',
                 'Dividend date 3': 'dividend_date',
                 'Ex-dividend date 4': 'dividend_ex_date',
                 'Last split factor 2': 'split_factor_last',
                 'Last split date 3': 'split_date_last',
                 'Fiscal year ends': 'year_fiscal_end',
                 'Most-recent quarter (mrq)': 'mrq',
                 'Profit margin': 'profit_margin_ltm',
                 'Operating margin (ttm)': 'operating_margin_ltm',
                 'Return on assets (ttm)': 'roa_ltm',
                 'Return on equity (ttm)': 'roe_ltm',
                 'Revenue (ttm)': 'revenue_ltm',
                 'Revenue Per Share (ttm)': 'revenue_per_share_ltm',
                 'Quarterly revenue growth (yoy)': 'quarterly_revenue_growth_yoy',
                 'Gross profit (ttm)': 'gross_profit_ltm',
                 'EBITDA': 'ebitda_ltm',
                 'Net income avi to common (ttm)': 'ni_to_common_ltm',
                 'Diluted EPS (ttm)': 'eps_diluted_ltm',
                 'Quarterly earnings growth (yoy)': 'ni_growth_yoy',
                 'Total cash (mrq)': 'cash_mrq',
                 'Total cash per share (mrq)': 'cash_per_share_mrq',
                 'Total debt (mrq)': 'debt_total_mrq',
                 'Total debt/equity (mrq)': 'debt_to_equity_mrq',
                 'Current ratio (mrq)': 'ratio_current_mrq',
                 'Book value per share (mrq)': 'book_per_share_mrq',
                 'Operating cash flow (ttm)': 'operating_cash_flow_ltm',
                 'Levered free cash flow (ttm)': 'cash_flow_levered_ltm',
                 'Net Debt LTM': 'net_debt_ltm',
                 'Net Debt to EBITDA': 'net_debt_to_ebitda_ltm',
                 '325 Score': '325',
                 '325 Experience': '325_experience',
                 'Tamale Status': 'tamale_status',
                 'Last Work': 'last_work',
                 'Sagard Peer Count': 'sagard_peers',
                 'Market Leader?': 'market_leader_q',
                 'Net Debt (LTM)': 'net_debt_ltm',
                 'Net Debt to EBITDA (LTM)': 'net_debt_to_ebtida_ltm',
                 'Cash Conversion Ratio': 'cash_conversion_ltm',
                 'Gross Margin (LTM)': 'gross_profit_margin_ltm'}

    # Put in place good database names from the names dictionary above
    returndf.rename(columns=new_names, inplace=True)

    # Replace strings with numbers whereever possible otherwise, 'ignore' meaning leave them
    returndf = returndf.apply(pd.to_numeric, errors = 'ignore')

    return returndf


def refresh_yahoo(tickerdf):
    # get the data from key stats from yahoo for a list of tickers
    # give it a list of tickers and it will look them and return
    # a dataframe of them

    # Create an empty dataframe
    yahoo = pd.DataFrame()

    # Go through tickers in fidelity list and get the yahoo statistics
    for ticker in tickerdf.index:

        print("Working on {}".format(ticker))

        # call the get key stats function in screen1 to get the stats from yahoo and set the index
        try:
            stats = get_key_stats(ticker)
        except:
            print("Could not retreive {}".format(ticker))
            continue
        stats.set_index(pd.Series(ticker), inplace=True)
        stats.convert_dtypes()

        # stitch the yahoo dataframe together with new stats pulled
        yahoo = pd.concat([yahoo, stats], join='outer', axis=0)

    # Return the stiched up database from yahoo
    return yahoo


def get_yahoo_labels(data):
    # Get the translation of Yahoo names to database lables
    filenames = ["yahoo_to_database_titles.xlsx"]
    sheets = {"Sheet1": [0, "A:C", 107]}
    names = getasheet(filenames, sheets, 'yahoo_name')

    data_labels = [names['325_name'][names['database_name'] == d][0]
                   for i, d in enumerate(data)]

    return data_labels


def update_all_fscores_with_canalyst(directory):
    """
    This function uses functions get_all_models to get a list of tickers for which there is a model.
    It then runs update_fscores_with_canalyst to update fscores with whatever canalyst models it finds
    note directory has to have a trailing / as in '/home/aks/325research/' not '/home/aks/325ressearch'
    """

    tickers_with_models = get_all_models(directory)

    for i in tickers_with_models:
        try:
            update_fscores_with_canalyst(i, directory + i + '/Models/')
        except:
            print(f'Updating {i} model failed')
            continue
    return


def get_all_models(directory):
    """ get_all_models
    This function takes a base directory of tickers where models should be (e.g. 325 Research)
    it then looks inside each directory entry for the existence of 'Models' and returns
    those tickers (defined as directory names <= 5) for which it finds a Model as a list'
    note directory has to have a trailing slash
    """

    import os
    import sys

    if len( directory ) == 0:
        directory = '/home/aks/325research/'

    research_files = [i for i in os.scandir(directory)]
    ticker_dirs = [i for i in research_files if i.is_dir()]
    model_dirs = [i.name for i in ticker_dirs if ('Models' in os.listdir(directory + i.name)) & (len(i.name) <= 5)]

    models_available = [i for i in model_dirs if get_latest_excel_for_ticker(i, directory + i + '/Models/')]

    return models_available


def get_latest_excel_for_ticker(ticker, directory):
    """ This function takes a ticker and a directory and scans all the files and
    returns the most recent file with the ticker's name in it.
    note directory has to have a trailing slash
    """
    import os

    # Get all the directory entries in the directory
    dir_entries = os.scandir(directory)

    # Make a dictionary of all the excel files with the tickers name in it with date/time
    files = {entry.name: entry.stat().st_mtime for entry in dir_entries if (ticker in entry.name) & ('.xls' in entry.name)}

    # Sort the files by date (item 1) in reverse order (most recent first)
    files = sorted(files.items(), key=lambda item: item[1], reverse=True)

    # Return the first distionary entry [0] and then the first entry of key/value pair which is the filename [0]
    if files:
        return files[0][0]
    else:
        return 0

def get_summary_page(ticker, directory):
    """ This function takes a ticker and looks in Anil's 325resarch path and reads the
        latest canalyst sheet (based on get_latest_excel_for_ticke function.

        It then returns two dataframes and the mrfp - q and f which are the normalized quarterly and
        fiscal year cuts of that spreadsheet page

        Typical errors are related to quality of input data. Recommend: update the model to the latest,
        ensure that summary page rows are named consistently for reading.
        Example errors are:
        - out of range - not enough data
        - can't read some values, dataframe doesn't recognize some fields as numerical due to some text typed
        - pandas < error acutally means that there are multple columns named the same thing
            by mistake; check parsing of fields

        note directory name has to have a trailing slash
        """

    import openpyxl

    # Stop openpyxl from complaining
    logging.captureWarnings(True)

    # Set up to run automatically while experimenting
    if 'Models' not in directory:
        directory = '/home/aks/325research/'+ticker.upper()+'/Models/'

    # Get the latest date of the model using openpyxl and MO.MRFP field in canalyst models
    filename = directory + get_latest_excel_for_ticker(ticker, directory)
    workbook = openpyxl.load_workbook(filename)

    # MRFP_range will then have a list of the sheet and the range of the date (but with $ signs)
    MRFP_range = workbook.defined_names['MO.MRFP'].attr_text.split('!')

    # The last date is in the workbook[sheetname][range].value have to remember to remove the $
    mrfp = workbook[MRFP_range[0]][MRFP_range[1].replace("$", '')].value

    # create a pandas dataframe from the Model sheet of the Canalyst file
    c = pd.read_excel(filename, sheet_name='Summary Page', header=1)
    c = c.set_index('Reports')
    print(f'Imported the {ticker} model from {filename} with date {mrfp}')

    # Turn warnings back on
    logging.captureWarnings(False)

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
            'OPEX (adj. for SBC)': 'sga_ex_sbc',
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

    # This is only way i know to drop duplicate column names
    duplicate_column_names = m.columns.duplicated()
    m = m.loc[:,~duplicate_column_names]

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
    f['revenue_growth_max'] = f.revenue_growth_3.rolling(3).max()
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

    ## 3-year fcfe estimate of market value; 5-year hold period cumulative fcfe
    q['ep_value_from_fcfe'] = q.fcfe_avg_3 * 5
    f['ep_value_from_fcfe'] = f.fcfe_avg_3 * 5

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
    q['ep_value_from_ic'] = (q.ic_delta_3 / 3 * 5 * q.roic_high_5)
    f['ep_value_from_ic'] = (f.ic_delta_3 / 3 * 5 * f.roic_high_5)

    ## Total value added from all sources
    q['ep_total_est_value'] = q.ep_market_cap + q.ep_value_from_fcfe + q.ep_value_from_ebitda + q.ep_value_from_ic
    f['ep_total_est_value'] = f.ep_market_cap + f.ep_value_from_fcfe + f.ep_value_from_ebitda + f.ep_value_from_ic

    # Update f with the ltm from q so that it too is a viable, full database
    try:
        f = f.drop(index = pd.to_datetime('2020'))
    except:
        print(f'Model has date {mrfp} and so can not drop 2020')

    # Note if this line fails due to "reindex" error; probably one item has been added to one df and not the other
    f = f.append(q.loc[mrfp])

    # Add an mrfp field for tracking in fscores
    f['mrfp'] = mrfp

    # That's all folks - return the q and f dataframes
    return q, f, mrfp


def get_mb_report(tickerdf):
    """ This function prints Michael Braner's original report.  It takes a cut of a
    ticker from a dataframe from fscores and prints the result
    """
    # rename tickerdf as q for consistency with original code
    q = tickerdf.copy()
    ticker = q.name
    mrfp = q.date_of_data

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
    print(q[display_value_summary])
    print('\n')
    print('The estimated value from each source:')
    print('current ep:\t{0:.1f}x'.format(q.ep_market_cap/market_cap))
    print('avg fcfe:\t{0:.1f}x'.format(q.ep_value_from_fcfe/market_cap))
    print('margin:\t\t{0:.1f}x'.format(q.ep_value_from_ebitda/market_cap))
    print('growth:\t\t{0:.1f}x'.format(q.ep_value_from_ic/market_cap))
    print('-----------\t----')
    print('total:\t\t{0:.1f}x'.format(q.ep_total_est_value/market_cap))
    return

def print_mb_report(ticker, directory):
    """ This function prints Michael Braner's original report in his model import
    file to see if it all working correctly. It takes a ticker and a dataframe for q
    as definied in get_canalyst_model and returned by it second
    """
    # get the latest canalyst data in q, f, and m which are quarterly df, fiscal year df, and mrfp
    q, _f, mrfp = get_summary_page(ticker, directory)

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
    print('current ep:\t{0:.1f}x'.format(q.ep_market_cap[mrfp]/market_cap))
    print('avg fcfe:\t{0:.1f}x'.format(q.ep_value_from_fcfe[mrfp]/market_cap))
    print('margin:\t\t{0:.1f}x'.format(q.ep_value_from_ebitda[mrfp]/market_cap))
    print('growth:\t\t{0:.1f}x'.format(q.ep_value_from_ic[mrfp]/market_cap))
    print('-----------\t----')
    print('total:\t\t{0:.1f}x'.format(q.ep_total_est_value[mrfp]/market_cap))

    return q

def update_fscores_with_canalyst(ticker, directory):
    """
    This function takes a ticker and a directory where its latest Canalyst Model is stored
    and updates the master fscores database with the Canalyst information to be more accurate
    where we have downloaded a Canalyst model.  It does not return a value, but updates the fscores
    and replaces data for the ticker named and resaves fscores.xlsx
    """

    from screen1 import run_tests, run_eps

    # Get the two master data sources from fscores and canalyst
    fscores = pd.read_excel('fscores.xlsx')
    fscores = fscores.set_index('symbol')

    # cq refers to canalyst quarterlies, cf to canalyst fiscals. function in cantest.py
    cq, cf, mrfp = get_summary_page(ticker, directory)

    # Pull out a record to update for this ticker
    this_ticker = fscores.loc[ticker].copy()
    this_ticker = pd.DataFrame(this_ticker).T


    # For any columns in cq, update this_ticker. (Note: tried pd.update and errors)
    this_ticker = cq.loc[mrfp]
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


# Set up a request
token ='eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VybmFtZSI6ImFzaHJpdmFzdGF2YSIsImVtYWlsIjoiYXNocml2YXN0YXZhQDMyNWNhcGl0YWwuY29tIiwiZmlyc3RfbmFtZSI6IkFuaWwiLCJsYXN0X25hbWUiOiJTaHJpdmFzdGF2YSIsImNvbXBhbnlfbmFtZSI6IjMyNSBDYXBpdGFsIiwiaXNfc3VwZXJ1c2VyIjpmYWxzZSwiaXNfc3RhZmYiOmZhbHNlLCJpc19zeW50aGV0aWMiOmZhbHNlLCJpc19jb2xsZWN0aXZlIjpmYWxzZSwidXNlcl91dWlkIjoiYmY1ZGRmNjctMjBhNC00MTc4LThjNjYtNTlhOGYzMDQ5ZGYyIiwiaWF0IjoxNjAxOTM2MDczLCJpc3MiOiJhcHAuY2FuYWx5c3QuY29tIiwidHlwZSI6ImFwcGxpY2F0aW9uIiwidXVpZCI6IjMyODZkZWRmLTVjYzktNGJiNy04MTRjLTI0OWIxZWIyMjUyZiJ9.huaTYZWul7ZSvK5KHSBBA9wELE12Me5_JQCdB9wm1MU'

def get_csin_and_model_for_ticker(ticker):
    """ This function takes a ticker; converts to Bloomberg style for US
    as in ATRO US if given atro.  And looks up the CSIN and Model Number for
    Canalyst API.  This function is used by other canalyst looks ups to
    get data from a specific model. Note it requires a global for the token
    data defined outsdie this function.
    """

    import requests
    token ='eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VybmFtZSI6ImFzaHJpdmFzdGF2YSIsImVtYWlsIjoiYXNocml2YXN0YXZhQDMyNWNhcGl0YWwuY29tIiwiZmlyc3RfbmFtZSI6IkFuaWwiLCJsYXN0X25hbWUiOiJTaHJpdmFzdGF2YSIsImNvbXBhbnlfbmFtZSI6IjMyNSBDYXBpdGFsIiwiaXNfc3VwZXJ1c2VyIjpmYWxzZSwiaXNfc3RhZmYiOmZhbHNlLCJpc19zeW50aGV0aWMiOmZhbHNlLCJpc19jb2xsZWN0aXZlIjpmYWxzZSwidXNlcl91dWlkIjoiYmY1ZGRmNjctMjBhNC00MTc4LThjNjYtNTlhOGYzMDQ5ZGYyIiwiaWF0IjoxNjAxOTM2MDczLCJpc3MiOiJhcHAuY2FuYWx5c3QuY29tIiwidHlwZSI6ImFwcGxpY2F0aW9uIiwidXVpZCI6IjMyODZkZWRmLTVjYzktNGJiNy04MTRjLTI0OWIxZWIyMjUyZiJ9.huaTYZWul7ZSvK5KHSBBA9wELE12Me5_JQCdB9wm1MU'

    base_url = 'https://mds.canalyst.com/api'

    # Authentication string
    headers = {'Authorization': f'Bearer {token}'}

    # Set up to get company list
    endpoint_path = '/equity-model-series/'

        # Parameters to pass
    params = {'page_size': 200,
            'company_ticker_bloomberg': ticker,
            }

        # Get the page
    target_url = base_url + endpoint_path
    r = requests.get(
            target_url,
            headers = headers,
            params = params,
            )

    return r.json()['results'][0]['csin'], r.json()['results'][0]['latest_equity_model']['model_version']['name']


def get_can_series(ticker, field = 'MO_RIS_REV', ltm_type = 'sum'):
    """
    This function takes a ticker in upper or lower case and calls
    get_csin_and_model_for_ticker function to get a canalst csin and
    model number.

    It then finds the field requested and returns two series: q and f
    q is the quarterly data and f is the annual data with ltm appended. The index for both
    series is the pandas datetime format for dates.

    If the data is in dollars it is returned as millions. Otherwise it is
    returned as-is

    If the field can't be found, it returns two series of 40 and 10 zeros
    """

    import requests
    import logging
    logger = logging.getLogger(__name__)
    token ='eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VybmFtZSI6ImFzaHJpdmFzdGF2YSIsImVtYWlsIjoiYXNocml2YXN0YXZhQDMyNWNhcGl0YWwuY29tIiwiZmlyc3RfbmFtZSI6IkFuaWwiLCJsYXN0X25hbWUiOiJTaHJpdmFzdGF2YSIsImNvbXBhbnlfbmFtZSI6IjMyNSBDYXBpdGFsIiwiaXNfc3VwZXJ1c2VyIjpmYWxzZSwiaXNfc3RhZmYiOmZhbHNlLCJpc19zeW50aGV0aWMiOmZhbHNlLCJpc19jb2xsZWN0aXZlIjpmYWxzZSwidXNlcl91dWlkIjoiYmY1ZGRmNjctMjBhNC00MTc4LThjNjYtNTlhOGYzMDQ5ZGYyIiwiaWF0IjoxNjAxOTM2MDczLCJpc3MiOiJhcHAuY2FuYWx5c3QuY29tIiwidHlwZSI6ImFwcGxpY2F0aW9uIiwidXVpZCI6IjMyODZkZWRmLTVjYzktNGJiNy04MTRjLTI0OWIxZWIyMjUyZiJ9.huaTYZWul7ZSvK5KHSBBA9wELE12Me5_JQCdB9wm1MU'

    # Check if ticker is in bloomberg format
    if not(' US' in ticker.upper() or ' CN' in ticker.upper()):
        ticker = ticker.upper()+' US'

    csin, model_version = get_csin_and_model_for_ticker(ticker)

    base_url = 'https://mds.canalyst.com/api'

    # Authentication string
    headers = {'Authorization': f'Bearer {token}'}

    # Set up to get company list
    endpoint_path = f'/equity-model-series/{csin}/equity-models/{model_version}/historical-data-points/'

    # Parameters to pass
    params = {'page_size': 500,
            'csin': csin,
            'model_version': model_version,
            'time_series_name': field
            }

    target_url = base_url + endpoint_path
    r = requests.get(
            target_url,
            headers = headers,
            params = params,
            )

    # Grab the key fields from results
    d = pd.json_normalize(r.json()['results'])

    if d.empty:
        # Try new field name without RIS, instead IS
        params = {'page_size': 500,
                'csin': csin,
                'model_version': model_version,
                'time_series_name': field.replace('RIS', 'IS')
                }

        target_url = base_url + endpoint_path
        r = requests.get(
                target_url,
                headers = headers,
                params = params,
                )
        d = pd.json_normalize(r.json()['results'])

    if d.empty:
        print(f"Can't find {field} you requested to for {ticker}")
        print(f"For debugging purposes csin and model number are: {csin} and {model_version}")
        print(f"Target url is : {target_url}")
        print(f"Return response is : {r.json()}")
        logger.info(f'Cant find {field} or IS version of field for {csin} and {model_version} for {ticker}')
        return pd.Series(index = pd.date_range('2013-01-01', periods = 30, freq = 'Q'), data = np.array([np.nan] * 30)), pd.Series(index = pd.date_range('2009-01-01', periods = 11, freq = 'Y'), data = np.array([np.nan] * 11)),

    # Catch if the untis can be converted to millions or should stay as is
    indollars = d['time_series.unit.symbol'].str.contains('$', regex = False)
    inpercent = d['time_series.unit.symbol'].str.contains('%', regex = False)
    d.value = d.value.astype(np.float)

    if indollars.any(axis = 0):
        d.value = d[indollars].value / 1e6

    if inpercent.any(axis = 0):
        d.value = d[inpercent].value / 1e2


    d = d.set_index('period.name')

    # Convert dates to pandas type dates and split dataframes into quarterlies and fiscals
    q = d[d.index.str.startswith('Q')].copy()
    f = d[d.index.str.startswith('F')].copy()
    q.index = q.index.str.split('-').str.get(1) +  q.index.str.split('-').str.get(0)
    f.index = f.index.str.replace('FY', '')

    # Convert index to real pandas datetime
    q.index = pd.to_datetime(q.index)
    f.index = pd.to_datetime(f.index)

    # Sort the series from earliest to latest at bottom
    q.sort_index(inplace = True)
    f.sort_index(inplace = True)

    # Append the LTM onto f depending on type: bs = balance sheet; rate = rates (e.g. %)
    if ltm_type == 'bs':
        f = f.append(q.iloc[-1])
    elif ltm_type == 'rate':
        f = f.append(q.rolling(4).mean().iloc[-1])
    else:
        f = f.append(q.rolling(4).sum().iloc[-1])

    return q.value ,f.value

def get_canalyst_fscore(tickers):
    """
    This is the beginning of getting the fscores off the canalyst api only
    """

    import requests
    from    getdata_325 import  get_master_screen_sheets, get_key_stats, getasheet, get_historic_prices
    import statistics
    import datetime as dt
    import FundamentalAnalysis as fa
    from screen1 import get_canalyst_ep

    # Set up logger
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    log_file_handler = logging.FileHandler('can_fscore.log')
    log_formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(name)s:%(message)s')
    log_file_handler.setFormatter(log_formatter)
    logger.addHandler(log_file_handler)

    # ttf is 't'hree 't'wenty 'f'ive
    ttfdf = pd.read_excel('fscores.xlsx').set_index('symbol')

    # Read all the canalyst tickers
    cans = pd.read_excel('universe.xlsx').set_index('tickers.Bloomberg')

    # Create a return df
    returndf = pd.DataFrame()

    # If only got one string instead of a list, turn string into list
    if isinstance(tickers, str):
        tickers = tickers.strip('][').split(',')

    for ticker in tickers:
        print(f"Getting data for {ticker}...")

        try:
            if not( " US" in ticker or " CN" in ticker):
                ticker= ticker.upper() + " US"
        except:
            logger.warning(f'Ticker is not good: {yahoo_ticker}')
            continue

        # Set up a new dataframe just for this company
        df = pd.DataFrame()


        try:
            # Get Yahoo insider stats
            # If ticker is CN, then add .TO to yahoo ticker
            if " CN" in ticker:
                yahoo_ticker = ticker.split(' ')[0] + '.TO'
            else:
                yahoo_ticker = ticker.split(' ')[0]

            tgt = f'https://finance.yahoo.com/quote/{yahoo_ticker}/insider-transactions?p={yahoo_ticker}'
            try:
                inside = pd.read_html(tgt)[0]
                logger.info(f'Got insider transactions for {yahoo_ticker}')
            except:
                logger.error(f'Get insider stats from yahoo failed for {yahoo_ticker}. Setting inside to empty dataframe')
                inside = pd.DataFrame()

            # get the other main stock indicators from Yahoo
            try:
                key_stats = get_key_stats(yahoo_ticker)
                logger.info(f'Got yahoo key stats for {yahoo_ticker}')
            except:
                logger.warning(f'Get key stats failed for {yahoo_ticker}')
                continue

            try:
                # Get the historical price data
                hist = get_historic_prices(yahoo_ticker)

                # Get company description and other profile data
                api_key = "c350f6f5a4396d349ee4bbacde3d5999"
                profile = fa.profile(yahoo_ticker, api_key).T

                logger.info(f'Creating fscore for {ticker}')
                df.loc[0,'symbol'] = ticker.split(' ')[0]
                df['bloomberg_ticker'] = ticker
                df['csin'], df['model_number'] = get_csin_and_model_for_ticker(ticker)
                df['name'] = cans.name[ticker]
                df['date_of_data'] = pd.to_datetime(dt.datetime.today())
                df['price'] =  hist.last('1D')['Close'][0]
                logger.info(f'Got historical market data')
            except:
                logger.info(f'Failed to get historical market data for {ticker}')
                continue

            # Revenue and adjusted EBITDA

            # Get the revenue and adjust EBITDA from canalyst (in millions)
            qrevenue, revenue = get_can_series(ticker, 'MO_RIS_REV', 'sum')
            qebitda, ebitda = get_can_series(ticker, 'MO_RIS_EBITDA_Adj', 'sum')
            qgp, gp = get_can_series(ticker, 'MO_IS_GP', 'sum')
            qni, ni = get_can_series(ticker, 'MO_IS_NI_ContinOp', 'sum')
            qebit, ebit = get_can_series(ticker, 'MO_RIS_EBIT', 'sum')
            qda,da = get_can_series(ticker, 'MO_RIS_DA', 'sum')
            qint, inte = get_can_series(ticker,'MO_RIS_IE', 'sum')
            qebt, ebt = get_can_series(ticker, 'MO_RIS_EBT', 'sum')
            qtax_current_rate, tax_current_rate = get_can_series(ticker, 'MO_RIS_TaxRate_Current', 'rate')
            qtax_deferred_rate, tax_deferred_rate = get_can_series(ticker, 'MO_RIS_TaxRate_Deferred', 'rate')
            revenue_growth = (revenue / revenue.shift(3)) ** (1 / 3) - 1
            ebitda_margin = ebitda / revenue
            gm = gp / revenue
            # estimate SGA as difference between gross profit and EBITDA; this is cash expense mostly
            sga = gp - ebitda
            sgam  = sga / revenue
            tax_rate = (tax_current_rate + tax_deferred_rate)

            df['revenue_ltm'] = revenue[-1]
            df['revenue_growth_3'] = revenue_growth[-1]
            df['revenue_growth_max'] = revenue_growth[-5:].max()
            df['ebitda_ltm'] = ebitda[-1]
            df['ebitda_avg_3'] = ebitda[-3:].mean()
            df['ebitda_avg_5'] = ebitda[-5:].mean()
            df['ebitda_ago_5'] = ebitda[-5]
            df['ebitda_margin_ltm'] = ebitda_margin[-1]
            df['ebitda_margin_high_5'] = ebitda_margin[-5:].max()
            df['gross_profit_ltm'] = gp[-1]
            df['gm_ltm'] = gm[-1]
            df['gm_high_5'] = gm[-5:].max()
            df['ebit_ltm'] = ebit[-1]
            df['ebit_ago_5'] = ebit[-5]
            df['da_ltm'] = da[-1]
            df['interest_expense_ltm'] = inte[-1]
            df['sgam_ltm'] = sgam[-1]
            df['sgam_low_5']= sgam[-5:].min()
            df['tax_rate_ltm'] = tax_rate[-1]

            logger.info(f'Got main income statement facts')

            # Market related facts

            # Read from key_stats for fresh data
            df['ev'] = key_stats.ev[yahoo_ticker]
            df['market_cap'] = key_stats.market_cap[yahoo_ticker]
            df['so'] = key_stats.so[yahoo_ticker]
            df['price_change_52'] = key_stats.price_change_52[yahoo_ticker] # TODO from hist?
            df['price_change_ytd'] = df.price / hist.last('1Y')['Close'][0] - 1 # choose a relative time period that is comparable eg. three months, LTM, or something
            df['price_change_last_Q'] = df.price / hist.last('1Q')['Close'][0] -1 # Added to put in a relatve lagging period
            df['pe'] = pd.to_numeric(key_stats.pe_ltm[yahoo_ticker])
            df['ep_multiple'] = 10

            try:
                short_columns = [i for i in key_stats.columns if 'Short' in i] # find the short interest columns in key_stats
                df['short_interest_ratio'] = pd.to_numeric(key_stats.loc[yahoo_ticker,short_columns[0]])
            except:
                df['short_interest_ratio'] = np.nan

            df['insider_ownership_total'] = pd.to_numeric(key_stats.insider_percent[yahoo_ticker])
            df['adv_avg_months_3'] = pd.to_numeric(key_stats.vol_avg_3_mo[yahoo_ticker])
            df['adv_as_percent_so'] = df.adv_avg_months_3 / df.so

            # Read from yahoo insiders
            try:
                df['net_insider_purchase_6'] = pd.to_numeric(inside.loc[inside.index[-1], 'Shares'].replace('%', '')) / 100
                insiders_selling = inside.iloc[4, 1]
                if isinstance(insiders_selling, str):
                    insiders_selling = pd.to_numeric(inside.iloc[4, 1].replace('%', ''), errors = 'coerce')/ 100
                df['insiders_selling_ltm'] = insiders_selling
            except:
                logger.warning(f'get insiders failed for {ticker}')
                df['net_insider_purchase_6'] = np.NAN
                df['insiders_selling_ltm'] = np.nan

            logger.info(f'Got key_stats data including insiders')

            # Balance sheet items

            # Get the total debt, cash, net debt, etc. from canalyst (in millions)
            qdebt, debt = get_can_series(ticker, 'MO_BSS_Debt', 'bs')
            qcash, cash = get_can_series(ticker, 'MO_BSS_Cash', 'bs')

            df['total_debt_ltm'] = debt[-1]
            df['cash_ltm'] = cash[-1]
            df['net_debt_ltm'] = df.total_debt_ltm - df.cash_ltm

            # Total Shareholer's equity
            qse, se = get_can_series(ticker, 'MO_BS_SE', 'bs')
            df['total_book_equity'] = se[-1]

            # Invested Capital TODO check how canalyst caluclates it
            ic = (debt - cash) + se
            df['ic_ltm'] = ic[-1]
            df['ic_ago_5'] = ic[-5]
            df['ic_ago_3'] = ic[-3]
            df['ic_delta_3'] = df.ic_ltm = df.ic_ago_3
            logger.info(f'Got Balance Sheet items')


            # Cash Flow related items

            # Get the key cash flow lines from canalyst (in millions)
            qcfo, cfo = get_can_series(ticker, 'MO_CFS_CFO', 'sum')
            qcapex, capex = get_can_series(ticker, 'MO_CFSum_Capex', 'sum')
            qicf, icf = get_can_series(ticker, 'MO_CFS_CFI', 'sum')
            qocf, ocf = get_can_series(ticker, 'MO_CFS_CFO', 'sum')
            qacq, acq = get_can_series(ticker, 'MO_CFSum_Acquisition', 'sum')
            qdiv, div = get_can_series(ticker, 'MO_CFSum_Divestiture', 'sum')
            qdividends, dividends = get_can_series(ticker, 'MO_CFSum_Dividend', 'sum')
            dividend_growth_3 = (dividends / dividends.shift(3)) ** (1 / 3) - 1
            capex_to_revenue_avg_3 = (capex / revenue)[-3:].mean()
            #qbb, fbb = get_can_series(ticker, 'MO_CFS_Buybacks')
            fcfe = cfo + capex

            df['fcfe_ltm'] = fcfe[-1]
            df['fcfe_avg_3'] = fcfe[-3:].mean()
            df['fcfe_to_marketcap'] = df.fcfe_ltm / df.market_cap
            df['fcfe_low_5'] = fcfe[-5:].min()
            df['icf_ltm'] = ic[-1]
            df['icf_avg_3'] = ic[-3:].mean()
            df['ocf_ltm'] = ocf[-1]
            df['acq_cf_ltm'] = acq[-1]
            df['acq_cf_sum_3'] = acq[-3:].sum()
            df['capex_ltm'] = capex[-1]
            df['capex_avg_3'] = capex[-3:].mean()
            df['capex_ago_5'] = capex[-5]
            df['capex_to_revenue_avg_3'] = capex_to_revenue_avg_3
            df['dividend_growth_3'] = dividend_growth_3[-1]
            #df['buybacks_cf_ltm'] = qbb.rolling(4).sum()[-1]
            #df['buybacks_cf_sum_3'] = qbb.rolling(4).sum().rolling(3).sum()[-1]
            df['ev_to_ebitda_ltm'] = df.ev / df.ebitda_ltm
            df['net_debt_to_ebitda_ltm'] = df.net_debt_ltm / df.ebitda_ltm
            df['ebitda_to_interest_coverage'] = df.ebitda_ltm / df.interest_expense_ltm

            logger.info(f'Got cash flow items')

            # Combined Items

            roic = ebit * (1 - tax_rate) / ic
            surplus_cash_as_percent_of_price = (cash - debt) / df.so[0] / df.price[0]

            df['roic_ltm'] = roic[-1]
            df['roic_high_5'] = roic[-5:].max()
            df['roic_avg_5']= roic[-5:].mean()
            df['surplus_cash_as_percent_of_price']= surplus_cash_as_percent_of_price[-1]
            df['icf_avg_3_to_fcf'] = df.icf_avg_3 / df.fcfe_ltm
            df['icf_to_ocf'] = df.icf_ltm / df.ocf_ltm
            df['capex_to_ocf'] = df.capex_ltm / df.ocf_ltm

            logger.info(f'Created ROICs')

            # EP items
            ep = (ebitda - capex) * ( 1 - tax_rate )
            df['ep_ltm'] = ep[-1]
            df['ep_avg_3'] = ep[-3:].mean()
            df['ep_ago_5'] = ep[-5]
            df['ep_market_cap'] = df.ep_ltm * df.ep_multiple - df.net_debt_ltm
            df['ep_value_from_fcfe'] = df.fcfe_avg_3 * 5
            df['ep_value_from_ebitda'] = (
                            (df.ebitda_margin_high_5 - df.ebitda_margin_ltm) * df.revenue_ltm
                            * df.ep_multiple
                            * (1 - df.tax_rate_ltm)
                            )
            df['ep_roic'] = df.ep_ltm / df.ic_ltm
            df['ep_delta_3'] = ep[-1] - ep[-3]
            df['ep_value_from_ic'] = (df.ic_delta_3
                * df.roic_high_5
                * df.ep_multiple
                - df.ic_delta_3
                )
            df['ep_total_est_value'] = (
                    df.ep_market_cap
                    + df.ep_value_from_fcfe
                    + df.ep_value_from_ebitda
                    + df.ep_value_from_ic
                    )

            df['description'] = profile.description[0]
            df['country'] = cans.country_code[ticker]

            # Put in the past experience flags
            try:
                df['sector'] = ttfdf.sector[yahoo_ticker]
                df['business'] = ttfdf.business[yahoo_ticker]
                df['short_sector'] = ttfdf.short_sector[yahoo_ticker]
                df['tamale_status'] = ttfdf.tamale_status[yahoo_ticker]
                df['status'] = df.tamale_status
                df['last_work'] = ttfdf.last_work[yahoo_ticker]
                df['sagard_peers'] = pd.to_numeric(ttfdf.sagard_peers[yahoo_ticker])
                df['market_leader'] = pd.to_numeric(ttfdf.market_leader[yahoo_ticker])
                df['triggers'] = ttfdf.triggers[yahoo_ticker]
            except:
                df['sector'] = cans.industry[ticker]
                df['business'] = cans.sector[ticker]
                df['short_sector'] = cans.sub_sector[ticker]
                df['tamale_status'] = pd.NA
                df['status'] = df.tamale_status
                df['last_work'] = pd.NA
                df['sagard_peers'] = 0
                df['market_leader'] = 0
                df['triggers'] = pd.NA
            logger.info(f'Finished basic status info for {ticker}')

            # Run full ep model flat and normal recover
            revenue_flat = [0, 0, 0, 0, 0]
            f, i = get_canalyst_ep(ticker, revenue_scenario = revenue_flat)
            try:
                df['sell_price'] = f.T.value_per_share[5]
                df['implied_ebitda_multiple'] = f.T.ev[5] / f.T.ebitda[5]
                df['ep_today'] = f.T.value_per_share[1]
                df['buy_price_ten_percent'] =df['sell_price'] / ((1 + i.ep_discount[0]) ** 5)
            except:
                df['sell_price'] = df.ep_total_est_value / df.so
                df['implied_ebitda_multiple'] = pd.NA
                df['ep_today'] = df.ep_ltm / df.so
                df['buy_price_ten_percent'] =df['sell_price'] / ((1 + .10) ** 5)
            df['ep_irr'] = ((df['sell_price'] /df['price']) ** ( 1 / 5)) -1


            # Trade Metrics
            logger.info(f'Created ep items')

        except:
            print(f'Getting record for {ticker} failed')
            continue

        returndf = returndf.append(df)
        print(f'Got and appended {ticker}')

    return returndf


def get_basic_screener(df):
    """
    takes a df with index being symbols and returns a df with
    market cap and other metrics from yahoo finance in it.
    """

    from getdata_325 import get_key_stats
    import pandas as pd

    # Create a return df
    returndf = pd.DataFrame()

    for ticker in df.index:
        print(f"Getting key stats for {ticker}...")

        try:
            key_stats = get_key_stats(ticker)
        except:
            print(f"Failed to get key stats for {ticker}")
            continue

        # Append the key stats file to the return df
        returndf = returndf.append(key_stats)

    return returndf

