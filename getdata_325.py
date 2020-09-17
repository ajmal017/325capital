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
import pickle
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
import itertools
import re

# Set up some convenience settings
pd.set_option('display.max_rows', 900)
pd.set_option('display.max_seq_items', 900)


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
