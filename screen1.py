# Screen1.py
# This file holds a large list of useful functions used in 325 capital
# Screenings.  It used to inlcude all garphics and data getting functions as wellA
# To increase reliability and readability, those graphics and getting data functions
# were moved to graphics_325.py and getdata_325.py on August 04, 2020
# This note was written on August 04, 2020

# Get the required packages
import pandas as pd
import numpy as np

# Set up some convenience settings
pd.set_option('display.max_rows', 200)
pd.set_option('display.max_seq_items', 200)

def get_fscore(tickers):
# fscore.py
# The name of this file is f for FundamentalAnalysis package and score to get a Sagard 4x4 score
# This file calculates the actual Sagard 4X4 score for a ticker
# It uses FundamentalAnalysis python package to retreive data from www.financialmodelingprep.com
# that website requires an api.  The current api key is :
# api_key = "c350f6f5a4396d349ee4bbacde3d5999"

    # Get the required packages
    from    getdata_325 import  get_master_screen_sheets, get_key_stats, getasheet, get_historic_prices
    import  FundamentalAnalysis as fa
    import  numpy as np
    import  pandas as pd
    import  datetime as dt
    import logging
    logging.basicConfig(level  = logging.INFO, filename = 'fscores.log', filemode = 'w')

    # Set up Fundamental Analysis Package
    api_key = "c350f6f5a4396d349ee4bbacde3d5999"

    # Read a 325 Screen Master sheet to get the 325 Capital scores
    # Changed this to read fscores becuase it may not be more uptodate on status 7/6/20
    # change this to read the fscores sheet becuase it should be quicker
    # ttf is 't'hree 't'wenty 'f'ive
    ttfdf = pd.read_excel('fscores.xlsx')
    ttfdf = ttfdf.set_index('symbol')

    # Get a names translation from Yahoo to database_titles
    filenames = ["yahoo_to_database_titles.xlsx"]
    sheets = {"Sheet1": [0, "A:B", 71] }
    names = getasheet(filenames, sheets,'yahoo_name')

    # Create a dictionary of new name mappings for Yahoo columns and rename them
    new_names = dict(zip(names.index,names['database_name']))

    # Create a return df
    returndf = pd.DataFrame()

    # If only got one string instead of a list, just turn the string into a list for the following
    # functions
    if isinstance(tickers, str):
        tickers = tickers.strip('][').split(',')

    for ticker in tickers:
        print("getting data for {}".format(ticker))
        # Set up a dataframe to hold the score
        df = pd.DataFrame()

        try:
            # Get Yahoo insider stats
            tgt = 'https://finance.yahoo.com/quote/{}/insider-transactions?p={}'.format(ticker, ticker)
            try:
                inside = pd.read_html(tgt)[0]
            except:
                logging.warning('get yahoo stats failed: {}'.format(ticker))
                inside = pd.DataFrame()

            # get the other main stock indicators from Yahoo
            try:
                key_stats = get_key_stats(ticker)
                key_stats.rename(columns = new_names, inplace = True)
            except:
                logging.warning('get key stats failed: {}'.format(ticker))
                continue

            # Get the historical price data
            hist = get_historic_prices(ticker)

            # Get the Fundamental Analysis data fields (check if each one loaded or not)
            profile = fa.profile(ticker, api_key)
            if profile.empty:
                logging.warning('get profile failed: {}'.format(ticker))
                continue
            companyName = profile.T.companyName

            inc = fa.income_statement(ticker, api_key, period='annual').T
            if inc.empty:
                logging.warning('get inc failed: {}'.format(ticker))
                continue
            inc.index = pd.to_datetime(inc.index)
            inc.sort_index(inplace = True)

            # Create an LTM column for latest
            # First get quarterly data
            inc_quarters = fa.income_statement(ticker, api_key, period = 'quarter').T
            if inc_quarters.empty:
                logging.warning('get inc quarters failed: {}'.format(ticker))
                continue
            inc_quarters.index = pd.to_datetime(inc_quarters.index)
            inc_quarters.sort_index(inplace = True)

            cf_quarters = fa.cash_flow_statement(ticker, api_key, period = 'quarter').T
            if cf_quarters.empty:
                logging.warning('get cf quarters failed: {}'.format(ticker))
                continue
            cf_quarters.index = pd.to_datetime(cf_quarters.index)
            cf_quarters.sort_index(inplace = True)


            km_quarters = fa.key_metrics(ticker, api_key, period = 'quarter').T
            if km_quarters.empty:
                logging.warning('get key metrics km failed: {}'.format(ticker))
                continue
            km_quarters.index = pd.to_datetime(km_quarters.index)
            km_quarters.sort_index(inplace = True)

            ev_quarters = fa.enterprise(ticker, api_key, period = 'quarter').T
            if ev_quarters.empty:
                logging.warning('get ev quarters failed: {}'.format(ticker))
                continue
            ev_quarters.index = pd.to_datetime(ev_quarters.index)
            ev_quarters.sort_index(inplace = True)

            # Create and ltm mask and get the sums of the income statement into LTM column
            ltm = (inc_quarters.index > '2019-03-01') & (inc_quarters.index <= '2020-03-01')
            ratios = ['grossProfitRatio', 'ebitdaratio', 'operatingIncomeRatio', 'netIncomeRatio']
            inct = inc.T
            inct[pd.to_datetime('2020-03-01')] = inc_quarters[ltm].sum()
            for ratio in ratios:
                inct.loc[ratio,'2020-03-01'] = inc_quarters.loc[inc_quarters.last('2Q').index[0], ratio]
            inc = inct.T
            inc.drop(columns = ['depreciationAndAmortization'], inplace = True)

            bs = fa.balance_sheet_statement(ticker, api_key, period='annual').T
            if bs.empty:
                logging.warning('get bs failed: {}'.format(ticker))
                continue
            bs.index = pd.to_datetime(bs.index)
            bs.sort_index(inplace = True)
            # Set BS ltm to last BS
            bs_quarters = fa.balance_sheet_statement(ticker, api_key, period = 'quarter').T
            if bs_quarters.empty:
                logging.warning('get bs_quarters failed: {}'.format(ticker))
                continue
            bs_quarters.index = pd.to_datetime(bs_quarters.index)
            bs_quarters.sort_index(inplace = True)
            bsltm = bs_quarters.last('1Q')
            bsltm.index = [pd.to_datetime('2020-03-01')]
            bs = bs.append(bsltm)

            km = fa.key_metrics(ticker, api_key, period='annual').T
            if km.empty:
                logging.warning('get km failed: {}'.format(ticker))
                continue
            km.index = pd.to_datetime(km.index)
            km.sort_index(inplace = True)
            kmt = km.T
            kmt[pd.to_datetime('2020-03-01')] = km_quarters.iloc[-1]
            km = kmt.T
            # km comes with enterprise value which we get with ev later
            km.drop(columns = ['enterpriseValue'], inplace = True)

            cf = fa.cash_flow_statement(ticker, api_key, period='annual').T
            if cf.empty:
                logging.warning('get cf failed: {}'.format(ticker))
                continue
            cf.index = pd.to_datetime(cf.index)
            cf.sort_index(inplace = True)
            cft = cf.T

            try:
                cft[pd.to_datetime('2020-03-01')] = cf_quarters[ltm].sum()
            except:
                logging.warning('get cft failed: {}'.format(ticker))
                cft[pd.to_datetime('2020-03-01')] = np.nan
            cf = cft.T

            fr = fa.financial_ratios(ticker, api_key, period='annual').T
            if fr.empty:
                logging.warning('get fr failed: {}'.format(ticker))
                continue
            fr.index = pd.to_datetime(fr.index)
            fr.sort_index(inplace = True)

            fg = fa.financial_statement_growth(ticker, api_key, period='annual').T
            fg.index = pd.to_datetime(fg.index)
            fg.sort_index(inplace = True)
            if fg.empty:
                logging.warning('get fg failed: {}'.format(ticker))
                continue

            ev = fa.enterprise(ticker,api_key,period= 'annual').T
            if ev.empty:
                logging.warning('get ev failed: {}'.format(ticker))
                continue
            ev.index = pd.to_datetime(ev.index)
            ev.sort_index(inplace = True)
            evt = ev.T
            evt[pd.to_datetime('2020-03-01')] = ev_quarters.iloc[-1]
            ev = evt.T

            profile = fa.profile(ticker, api_key).T

            # Put all the data in one-place
            all = pd.concat([inc, bs, km, cf, fr, fg, ev], axis = 'columns')

            # Set up a mask to caluclate averages for the last five years
            # Note that with ltm, the last five years is 6 periods that includes the LTM
            five = (all.index > (pd.to_datetime('2020-03-01') - pd.Timedelta('5Y')))
            three = (all.index > (pd.to_datetime('2020-03-01') - pd.Timedelta('3Y')))
            now = all.index[-1]

            # Prepare all with a few fields that will be used often
            # Protect div by zero
            all.marketCapitalization  = all.marketCapitalization.replace(0, np.nan).interpolate() # ev
            all.revenue  = all.revenue.replace(0, np.nan).interpolate() # inc
            all.ebitdaratio = all.ebitda / all.revenue
            all.grossProfitMargin = all.grossProfit / all. revenue
            all.interestExpense = all.interestExpense.replace(0, np.nan).interpolate() # inc
            all.investedCapital = all.totalDebt + all.commonStock + all.othertotalStockholdersEquity  - all.cashAndShortTermInvestments # bs 062720 changed to remove cash from invested capital
            all.investedCapital = all.investedCapital.replace(0, np.nan).interpolate() # inc
            all.incomeBeforeTax = all.incomeBeforeTax.replace(0, np.nan).interpolate() # inc
            all.totalAssets = all.totalAssets.replace(0, np.nan) # bs
            all['fcfe'] = all.netCashProvidedByOperatingActivities + all.interestExpense + all.capitalExpenditure # cf
            all['fcfe_to_marketcap'] = all.fcfe / all.marketCapitalization # cf, bs

            # convert the dataframe to correct dtypes (let pandas infer correct conversion)
            all = all.convert_dtypes()

            benchmarks = {
                    'debt_to_ebitda_ltm_benchmark' : 3,
                    }

            # Create the score for ticker
            # favor yahoo stats when in doubt
            # First some basic data about the ticker; note first item sets the index as well
            # key_stats from Yahoo key statistcs
            df.loc[0,'symbol'] = ticker
            df['name'] = companyName
            df['date_of_data'] = pd.to_datetime(dt.datetime.today())
            df['price'] =  hist.last('1D')['Close'][0]
            df['revenue_ltm'] = pd.to_numeric(key_stats.revenue_ltm[ticker]) # 062720 Use Yahoo revenue - more comfrotable than FA
            df['revenue_growth_3'] = (1 + all.revenue.pct_change(periods = 4)[five].last('1Y')[0]) ** (1 / 3) - 1 # inc
            df['revenue_growth_max'] = (1 + all.revenue.pct_change(periods = 4)[five].max()) ** ( 1 / 3) - 1 # inc
            df['ebitda_ltm'] = pd.to_numeric(key_stats.ebitda_ltm[ticker])
            df['ev'] = pd.to_numeric(key_stats.ev[ticker])
            df['ev_to_ebitda_ltm'] = df.ev / df.ebitda_ltm
            df['total_debt_ltm'] = all.longTermDebt[now] / 1e6
            df['cash_ltm'] = pd.to_numeric(key_stats.cash_mrq[ticker])
            df['market_cap'] = pd.to_numeric(key_stats.market_cap[ticker])
            df['so'] = pd.to_numeric(key_stats.so[ticker])
            df['net_debt_ltm'] = df.total_debt_ltm - df.cash_ltm
            df['fcfe_ltm'] = all.fcfe[now] / 1e6
            df['fcfe_to_marketcap'] = all.fcfe[now] / all.marketCapitalization[now]
            df['low_fcfe_to_historical'] = df.fcfe_to_marketcap / all[five].fcfe_to_marketcap.max()
            df['ebitda_cagr_to_evx'] = all.ebitda.pct_change(periods = 3)[five].max() / df.ev_to_ebitda_ltm # inc

            try:
                df['net_insider_purchase_6'] = pd.to_numeric(inside.loc[inside.index[-1], 'Shares'].replace('%', ''))
            except:
                logging.warning('get insider purchase failed: {}'.format(ticker))
                df['net_insider_purchase_6'] = np.NAN

            df['price_change_52'] = pd.to_numeric(key_stats.price_change_52[ticker]) # TODO from hist?
            df['price_change_ytd'] = df.price / hist.last('1Y')['Close'][0] - 1 # choose a relative time period that is comparable eg. three months, LTM, or something
            df['price_change_last_Q'] = df.price / hist.last('1Q')['Close'][0] -1 # Added to put in a relatve lagging period
            df['book_value'] = all.totalStockholdersEquity[now] / 1e6 - all.othertotalStockholdersEquity[now] / 1e6 # bs TODO https://www.investopedia.com/terms/b/bookvalue.asp
            df['eps_mid_cycle'] = all.eps[five].median() # inc
            df['pe_mid_cycle'] = all.priceEarningsRatio[five].median() # fr could use peRatio from km
            df['pe'] = pd.to_numeric(key_stats.pe_ltm[ticker])
            df['pe_to_mid_cycle_ratio'] = df.pe / df.pe_mid_cycle

            # Margin related
            df['gm_ltm'] = key_stats.gross_profit_ltm[0] / df.revenue_ltm
            df['gm_high_5'] = all.grossProfitMargin[five].max() # fr
            df['dividend_growth_3'] = all.dividendsperShareGrowth[three].mean() # fg
            df['capex_to_revenue_avg_3'] = all.capexToRevenue[three].mean() # km
            df['ebitda_margin_high_5'] = all.ebitdaratio[three].max() # inc
            df['ebitda_margin_ltm'] = df.ebitda_ltm / df.revenue_ltm
            df['em_high_minus_em_ltm'] = df.ebitda_margin_high_5 - df.ebitda_margin_ltm
            df['gross_profit_ltm'] = pd.to_numeric(key_stats.gross_profit_ltm[ticker])
            df['ev_to_gm_ltm'] = df.ev / df.gross_profit_ltm
            # multiple * ratio of high to low - net debt /shares /last price
            df['ep_multiple'] = 1 / .10 # put in a placeholder in case we want to change it for a ticker
            df['price_opp_at_em_high'] = (
                                   (df.ep_multiple * df.ebitda_margin_high_5 / df.ebitda_margin_ltm # CHANGEd 062720 to EP multiple
                                   * df.ebitda_ltm
                                   - df.net_debt_ltm)
                                   / df.so
                                   / df.price
                                   )
            df['sgam_ltm'] = all.generalAndAdministrativeExpenses[now] / all.revenue[now] # inc
            df['sgam_low_5'] = (all.generalAndAdministrativeExpenses[five] / all.revenue[five]).min() # inc
            # increase in EBIITDA if have lower G&A is df.ebitda_margin + (df.sgam_low_5 - df.sgam_ltm)
            # then use same calc as above for ebitda margin change
            df['price_opp_at_sgam_low'] = (
                                        (((df.ebitda_margin_ltm + (df.sgam_ltm - df.sgam_low_5))
                                        / df.ebitda_margin_ltm
                                        * df.ep_multiple # Changed 062720 from EV multiple to earnings power multiple
                                        * df.ebitda_ltm)
                                        - df.net_debt_ltm)
                                        / df.so
                                        / df.price
                                        )
            # ROIC section
            df['tax_rate'] = all.incomeTaxExpense[now] / all.incomeBeforeTax[now] # inc
            all.roic = all.operatingIncome * (1 - df.tax_rate[0]) / all.investedCapital # inc, bs 062720 Changed to after tax
            df['roic_high_5'] = all.roic[five].max() # km
            df['roic_avg_5'] = all.roic[five].median() # km
            df['roic_ago_5'] = all.roic.last('5Y')[0] # km
            df['roic'] = all.roic[now] # km
            df['roic_ltm_minus_roic_high'] = df.roic - df.roic_high_5
            df['ic'] = all.investedCapital[now] / 1e6 # bs
            # returns are roic * invested capital
            # ebitda is return / (1- tax rate) + DA
            df['da'] = all.depreciationAndAmortization[now] / 1e6 # cf
            df['ebitda_at_roic_high'] = (df.roic * df.ic / (1 - df.tax_rate)) + df.da # 062720 Changed to after tax and remove cash
            df['price_opp_at_roic_high'] = (
                                        (df.ebitda_at_roic_high / df.ebitda_ltm
                                        * df.ep_multiple # Changed 062720 to EP multiple from ev multiple
                                        * df.ebitda_ltm
                                        - df.net_debt_ltm)
                                        / df.so
                                        / df.price
                                        )
            df['ebit'] = all.operatingIncome[now] / 1e6 # inc
            df['ebit_ago_5'] = all.operatingIncome.last('5Y')[0] / 1e6# inc
            df['ic_ago_5'] = all.investedCapital.last('5Y')[0] / 1e6 # inc
            change_in_r =  df.ebit - df.ebit_ago_5
            change_in_ic_inverse = 1 / df.ic - 1 / df.ic_ago_5
            roic_change_from_r = change_in_r * (1 / df.ic_ago_5)
            roic_change_from_ic = df.ebit * change_in_ic_inverse
            total_roic_change = roic_change_from_r + roic_change_from_ic

            df['roic_change_from_r'] = (
                                        roic_change_from_r
                                        / total_roic_change
                                        * df.roic_ltm_minus_roic_high
                                       )
            df['roic_change_from_ic'] = (
                                        roic_change_from_ic
                                        / total_roic_change
                                        * df.roic_ltm_minus_roic_high
                                        )
            # Balance sheet metrics (including debt metrics)
            df['asset_growth'] = all.totalAssets[now] / all.totalAssets.last('5Y')[0] - 1 # bs
            df['surplus_cash_as_percent_of_price'] = (df.cash_ltm - df.total_debt_ltm)/ df.so / df.price
            df['debt_gap_from_ebitda_multiple'] = benchmarks['debt_to_ebitda_ltm_benchmark'] * df.ebitda_ltm  - df.net_debt_ltm
            df['additional_debt_from_ebitda_multiple_per_share'] = df.debt_gap_from_ebitda_multiple / df.so
            df['price_value_from_additional_debt'] = df.additional_debt_from_ebitda_multiple_per_share / df.price
            df['interest_expense_ltm'] = all.interestExpense[now] / 1e6
            df['ebitda_to_interest_coverage'] = df.ebitda_ltm / df.interest_expense_ltm
            df['net_debt_to_ebitda_ltm'] = df.net_debt_ltm / df.ebitda_ltm

            # Cash flow metrics
            df['capex_ltm'] = all.capitalExpenditure[now] / 1e6 # cf
            df['ocf_ltm'] = pd.to_numeric(key_stats.operating_cash_flow_ltm[ticker])
            df['icf_ltm'] = all.netCashUsedForInvestingActivites[now] / 1e6 # cf
            df['icf_avg_3'] = all.netCashUsedForInvestingActivites[three].median() / 1e6 # cf
            df['icf_avg_3_to_fcf'] = df.icf_avg_3 / df.fcfe_ltm
            df['capex_to_ocf'] = df.capex_ltm / df.ocf_ltm
            df['equity_sold'] = all.commonStockIssued[now] / 1e6 # cf
            df['financing_acquired'] = all.otherFinancingActivites[now] / 1e6 # cf
            short_columns = [i for i in key_stats.columns if 'Short' in i] # find the short interest columns in key_stats

            # Trade Metrics
            try:
                df['short_interest_ratio'] = pd.to_numeric(key_stats.loc[ticker,short_columns[0]])
            except:
                df['short_interest_ratio'] = np.nan

            df['insider_ownership_total'] = pd.to_numeric(key_stats.insider_percent[ticker])
            df['adv_avg_months_3'] = pd.to_numeric(key_stats.vol_avg_3_mo[ticker])
            df['adv_as_percent_so'] = df.adv_avg_months_3 / df.so

            try:
                insiders_selling = inside.iloc[4, 1]
                if isinstance(insiders_selling, str):
                    insiders_selling = pd.to_numeric(inside.iloc[4, 1].replace('%', ''), errors = 'coerce')/ 100
                df['insiders_selling_ltm'] = insiders_selling
            except:
                df['insiders_selling_ltm'] = np.nan

            df['capex_to_revenue_avg_3'] = (all.capitalExpenditure[three] / all.revenue[three]).mean() # cf, inc
            df['float'] = pd.to_numeric(key_stats.float[ticker])

            # Put in the past experience flags
            try:
                df['sector'] = ttfdf.sector[ticker]
                df['business'] = ttfdf.business[ticker]
                df['short_sector'] = ttfdf.short_sector[ticker]
                df['tamale_status'] = ttfdf.tamale_status[ticker]
                df['last_work'] = ttfdf.last_work[ticker]
                df['sagard_peers'] = pd.to_numeric(ttfdf.sagard_peers[ticker])
            except:
                df['sector'] = profile.sector[0]
                df['business'] = profile.industry[0]
                df['short_sector'] = profile.sector[0]
                df['tamale_status'] = 'N/A'
                df['last_work'] =  'N/A'
                df['sagard_peers'] = 0

            df.set_index('symbol', inplace = True)

            # Get tests
            # Call tests, but don't send a dataframe becuase we are only working on
            #    one record
            tests = set_tests()['tests']
            df = run_tests(df)

            # Get earnings power elements
            df = run_eps(df, inc = inc, bs = bs, cf = cf)

            returndf = returndf.append(df)
            print('Got and appended {}'.format(ticker))

        except:
            print('overall failure')
            logging.warning('overall failure to load: {}'.format(ticker))
            continue

    return returndf

def get_ep(*, ticker, inc = pd.DataFrame(), bs = pd.DataFrame(), cf = pd.DataFrame(), revenue_scenario = [], ebitda_scenario = []):
# a function that takes a ticker and financials and returns a base case earnings power
# model in forecasts (dataframe) and the assumptions it used in inputs (a dataframe also)
# ticker is a string ticker (e.g. 'GPX'), inc is fa.income_statement, bs is balance sheet, cf is
# cash flow. revenue_scenario is a iterable of 5 growth rates for years 1 through 5 to use
# ebitda_scenario is a list that is multiplied by the ebitda margin to push scenario up or down in total

    from sklearn.linear_model import LinearRegression
    import FundamentalAnalysis as fa
    api_key = "c350f6f5a4396d349ee4bbacde3d5999"

    print('getting forecast with revenue scenario: ', revenue_scenario)
    try:
        # Get the financials for the ticker in question. Focus on annuals for now
        if inc.empty:
            inc = fa.income_statement(ticker, api_key, 'annual').T
            inc.index = pd.to_datetime(inc.index)
            inc.sort_index(inplace = True)

        if bs.empty:
            bs = fa.balance_sheet_statement(ticker, api_key, 'annual').T
            bs.index = pd.to_datetime(bs.index)
            bs.sort_index(inplace = True)

        bs['wc'] = (bs.totalCurrentAssets - bs.cashAndShortTermInvestments) - bs.totalCurrentLiabilities

        if cf.empty:
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
        forecast.loc['ebit'] = forecast.loc['gm'] - forecast.loc['sga'] # Flipped this around from before based on Michael's observation

        # do non-cross-year calcs first
        forecast.loc['da' ] = forecast.loc['revenue'] * inputs['da_to_revenue_5_median'][0] # TODO base this off asset base rather than revenue? PPE? Goodwill issues? ebit + DA - maintenance capex (1-tax) is earnings power
        forecast.loc['ebitda' ] = forecast.loc['ebit'] + forecast.loc['da']  # Flipped this around from before based on Michael's observation

        # if there is an ebitda scenario, apply it
        # note multiplying multiplier by ebitda is same as by ebitda margin since revenue is fixed
        if len(ebitda_scenario) > 1:
            for year in forecast.columns[1:]:
                forecast.loc['ebitda', year] = forecast.loc['ebitda', year] * (ebitda_scenario[year - 1])
        elif len(ebitda_scenario) == 1:
            for year in forecast.columns[1:]:
                forecast.loc['ebitda', year] = forecast.loc['ebitda', year] * (ebitda_scenario[0])

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

        forecast.loc['ep_in_year'] = forecast.loc['earnings_power'] / inputs['ep_discount'][0]

        for year in forecast.columns:
            forecast.loc['tv_value_in_year', year] = forecast.loc['tv', 10] / ( ( 1 + inputs['ep_discount'][0] ) ** ( 10 - year) )

        forecast.loc['ev'] = forecast.loc['ep_in_year'] + forecast.loc['tv_value_in_year'] + forecast.loc['cum_dividends']
        forecast.loc['implied_ebitda_multiple'] = forecast.loc['ev'] / forecast.loc['ebitda']
        forecast.loc['equity_value'] = forecast.loc['ev'] - forecast.loc['net_debt']
        forecast.loc['value_per_share'] = forecast.loc['equity_value'] / inputs['so'][0]

        forecast = forecast.astype(np.float) / 1e6
        forecast.loc['value_per_share'] *= 1e6
        forecast.loc['implied_ebitda_multiple'] *= 1e6
    except:
        print('could not get forecast')
        return None, None

    return forecast, inputs

def run_eps(d_in, inc = pd.DataFrame(), bs = pd.DataFrame(), cf = pd.DataFrame(), ebitda_scenario = []):
    # This function takes an fscore dataframe and adds the ep scores to it
    # used to update a dataframe with new scores on the fly
    # Assumes dataframe has a) tickers as its index
    # It will get the forecasts and return an updated dataframe
    # Also takes and optional ebitda_scenario 1 or 10 multipler list for scenarios

    d = d_in.copy()

    # Save a down forecast if required
    down = [-.2, -.07, .08, .035, .035]

    for i in d.index:
        print('working on ', i)
        try:
            forecast, inputs = get_ep(ticker = i, inc = inc, bs = bs, cf = cf, ebitda_scenario = ebitda_scenario)
            d.loc[i,'sell_price'] = forecast.T.value_per_share[5]
            d.loc[i,'ep_irr'] = ((d.loc[i,'sell_price'] /d.loc[i,'price']) ** ( 1 / 5)) -1
            d.loc[i,'buy_price_ten_percent'] =d.loc[i,'sell_price'] / ((1 + inputs.ep_discount[0]) ** 5)
            d.loc[i,'implied_ebitda_multiple'] = forecast.T.ev[5] / forecast.T.ebitda[5]
            d.loc[i,'ep_today'] = forecast.T.value_per_share[1]
            print('got regular ', i)
        except:
            print('failed regular ', i)

        # Run the down scenarios and store the values
        try:
            forecast, inputs = get_ep(ticker = i, inc = inc, bs = bs, cf = cf, revenue_scenario = down, ebitda_scenario = ebitda_scenario)
            d.loc[i,'sell_price_down'] = forecast.T.value_per_share[5]
            d.loc[i,'ep_irr_down'] = ((d.loc[i,'sell_price_down'] /d.loc[i,'price']) ** ( 1 / 5)) -1
            d.loc[i,'buy_price_ten_percent_down'] =d.loc[i,'sell_price_down'] / ((1 + inputs.ep_discount[0]) ** 5)
            d.loc[i,'implied_ebitda_multiple_down'] = forecast.T.ev[5] / forecast.T.ebitda[5]
            d.loc[i,'ep_today_down'] = forecast.T.value_per_share[1]
            print('got down ', i)
        except:
            print('failed down ', i)

        # first section refers to revenue scenarios by sector
        short_sectors = ['TMT', 'Financial Services', 'Ag Chem and Materials',
               'Commercial Service', 'Healthcare', 'Retail', 'Industrials',
               'Real Estate', 'Consumer Cyclical', 'Technology', 'Energy',
               'Basic Materials', 'Construction', 'Communication Services',
               'Consumer Product', 'Utilities', 'Consumer Defensive',
               'Industrial']

        TMTr = [-.1, .1, .065, .05, .035]
        Finr = [-.1, .08, .065, .04, .035]
        Agr = [-.15, .05, .035, .035, .035]
        ComSvcr = [-.15, .08, .04, .04, .04]
        Healthr = [-.08, .06, .05, .05, .035]
        Retailr = [-.3, .08, .05, .035, .035]
        Indusr = [-.2, -.07, .08, .035, .035]
        REr = [-.15, .05, .035, .035, .035]
        CCr = [-.15, -.05, .10, .05, .035]
        Techr = [-.05, .05, .05, .05, .05]
        Enerr = [-.035, .05, .035,.035,.035]
        Basicr = [-.15, .05, .035, .035, .035]
        Consr = [-.05, .04, .035, .035, .035]
        Commr = [-.05, .05, .05, .05, .05]
        ConsPr = [-.05, .04, .035, .035, .035]
        Utilr = [-.035, .05, .035,.035,.035]
        ConsDr = [-.035, .05, .035,.035,.035]

        rss = [ TMTr , Finr , Agr , ComSvcr , Healthr , Retailr , Indusr , REr , CCr , Techr , Enerr , Basicr , Consr , Commr , ConsPr , Utilr , ConsDr ]

        rscens = dict(zip(short_sectors, rss))

        # sector based covid19 scenario from above
        ep_sector = pd.DataFrame()
        try:
            forecast, inputs = get_ep(ticker = i, inc = inc, bs = bs, cf = cf, revenue_scenario = rscens[d.loc[i, 'short_sector']], ebitda_scenario = ebitda_scenario)
            d.loc[i,'sell_price_sector'] = forecast.T.value_per_share[5]
            d.loc[i,'ep_irr_sector'] = ((d.loc[i,'sell_price_sector'] /d.loc[i,'price']) ** ( 1 / 5)) -1
            d.loc[i,'buy_price_ten_percent_sector'] =d.loc[i,'sell_price_sector'] / ((1 + inputs.ep_discount[0]) ** 5)
            d.loc[i,'implied_ebitda_multiple_sector'] = forecast.T.ev[5] / forecast.T.ebitda[5]
            d.loc[i,'ep_today_sector'] = forecast.T.value_per_share[1]
            print('got sector ', i)
        except:
            print('failed sector ', i)

    return d

def set_tests(b = pd.DataFrame()):
    # This function sets tests and returns the key variables in a dictonary
    # So that calling functions have access to the latest tests
    # If the function is called with a proper dataframe, d, it will calculate
    # live tests based on those and return that.

    TESTS = ['VALUATION_test', 'SBM_test', 'PUOC_test', 'BS_risks_test', 'TRADE_test']
    valuation_tests = [
       'pe_to_mid_cycle_ratio_test',
       'ev_to_ebitda_ltm_test',
       'price_change_52_test'
       ]
    sbm_tests = [
        'roic_high_5_test',
        'dividend_growth_3_test',
        'gm_ltm_test',
        'ebitda_margin_ltm_test',
        'sgam_ltm_test',
        'revenue_growth_3_test',
        'revenue_growth_max_test',
        'market_leader_test'
        ]

    puoc_tests = [
        'capex_to_revenue_avg_3_test',
        'roic_change_from_ic_test',
        'surplus_cash_as_percent_of_price_test',
        'additional_debt_from_ebitda_multiple_per_share_test',
        'icf_avg_3_to_fcf_test',
        'icf_to_ocf_test',
        'equity_sold_test',
        'financing_acquired_test',
        'capex_to_ocf_test'
        ]
    bs_risks_tests = [
        'icf_and_ocf_negative_test',
        'net_debt_to_ebitda_ltm_test',
        'ebitda_to_interest_coverage_test',
        ]
    trade_tests = [
        'short_interest_ratio_test',
        'insider_ownership_total_test',
        'insiders_can_get_out_quickly_test',
        'adv_avg_months_3_test',
        'float_test',
        'insiders_selling_ltm_test'
        ]
    experience_tests = [
            'price_opp_at_em_high_test' ,
            'price_opp_at_sgam_low_test',
            'price_opp_at_roic_high_test',
            ]

    valuation = [
       'pe_to_mid_cycle_ratio',
       'ev_to_ebitda_ltm',
       'price_change_52'
       ]

    sbm = [
        'roic_high_5',
        'dividend_growth_3',
        'gm_ltm',
        'ebitda_margin_ltm',
        'sgam_ltm',
        'revenue_growth_3',
        'revenue_growth_max',
        'market_leader'
        ]

    puoc = [
        'capex_to_revenue_avg_3',
        'roic_change_from_ic',
        'surplus_cash_as_percent_of_price',
        'additional_debt_from_ebitda_multiple_per_share',
        'icf_avg_3_to_fcf',
        'icf_to_ocf',
        'equity_sold',
        'financing_acquired',
        'capex_to_ocf'
        ]

    bs_risks = [
        'icf_and_ocf_negative',
        'net_debt_to_ebitda_ltm',
        'ebitda_to_interest_coverage',
        ]

    trade = [
        'short_interest_ratio',
        'insider_ownership_total',
        'insiders_can_get_out_quickly',
        'adv_avg_months_3',
        'float',
        'insiders_selling_ltm'
        ]

    experience = [
            'price_opp_at_em_high' ,
            'price_opp_at_sgam_low',
            'price_opp_at_roic_high',
            ]

    if b.empty:
        tests = {
                'ev_to_ebitda_ltm_test' : 8, # less than June 2020 median is 7.19. High qartile is 12.33, low quartile is -5.31
                'pe_to_mid_cycle_ratio_test': .85,  # less than  June 2020 low quartile is .533632, high q is 1.49
                'price_change_52_test': -.14725, # less than June 2020 median, low quartile is -.3875, high q is .182
                'price_change_last_Q_test': .051763, # less than  June 2020 low q, median is .2952, high q is .596285

                'roic_high_5_test': .080157, # greater than June 2020 top quartile
                'gm_ltm_test' : .345134, # greater than  June 2020 top quartile,.555943 median = .345134
                'dividend_growth_3_test': .05, # greater than June 2020 median Top quartile is 0.011755
                'ebitda_margin_ltm_test': .130, # greater than June 2020 Top quartile, median is .0659
                'sgam_ltm_test': .217179, # greater than  June 2020 median, low quartile = .108991 high q = .439870
                'revenue_growth_3_test': .124, # greater than  June 2020 median. Top quartile = .450341
                'revenue_growth_max_test': .14, # greater than original Sagard test
                'market_leader_test' : 1, # greater than market leader score will be a year if so or 0 if NOT

                'capex_to_revenue_avg_3_test': .009, # greater than June 2020 top quartile, median = .028490
                'roic_change_from_ic_test' : 0, # less than
                'surplus_cash_as_percent_of_price_test':-.1133, # greater than June 2020 top quartile is .123063, median is -.113380
                'additional_debt_from_ebitda_multiple_per_share_test' : 0, # greater than
                'icf_avg_3_to_fcf_test': 1, # greater than
                'icf_to_ocf_test': -.274591, # greater than  June 2020 high quartile .142, median is -.274591
                'equity_sold_test': 2.55, # greater than June 2020 top quartile
                'financing_acquired_test': 42, # greater than June 2020 median
                'capex_to_ocf_test': .099408, # greater than June 2020 median.  High quartile is .396726

                'icf_and_ocf_negative_test': 0, # should not be the case
                'net_debt_to_ebitda_ltm_test': 3, # greater than original Sagard test. current June 2020 median is 1.975
                'ebitda_to_interest_coverage_test': 3.4, # less than June 2020 median

                'short_interest_ratio_test': 7.26, # greater than June 2020 top quartile 7.26, median = 3.92
                'insider_ownership_total_test': .182050, # greater than June 2020 top quartile .182050, median = .0607
                'insiders_can_get_out_quickly_test': 19.658, # greater than June 2020 top quartile
                'adv_avg_months_3_test': .376, # less than June 2020 median
                'float_test': 14.31, # less than June 2020 lowest quartile
                'insiders_selling_ltm_test': .035, # less than June 2020 median; lowest quartile is 0

                'price_opp_at_em_high_test' : 1.3, # greater than June 2020 median is 0.909
                'price_opp_at_sgam_low_test': 1.2, # greater than June 2020 median is 0.9837
                'price_opp_at_roic_high_test': 1.2, # greater than June 2020 median is 1.167, high quartile is 1.5
                }
    else:
        tests = {
                'ev_to_ebitda_ltm_test' : 8, # less than June 2020 median is 7.19. High qartile is 12.33, low quartile is -5.31
                'pe_to_mid_cycle_ratio_test': (b.pe / b.pe_mid_cycle).quantile(q = 0.5),  # less than  June 2020 low quartile is .533632, high q is 1.49
                'price_change_52_test': b.price_change_52.quantile(q = 0.5), # less than June 2020 median, low quartile is -.3875, high q is .182
                'price_change_last_Q_test': b.price_change_last_Q.quantile(q = 0.5), # less than  June 2020 low q, median is .2952, high q is .596285

                'roic_high_5_test': b.roic_high_5.quantile(q = .75), # greater than June 2020 top quartile
                'gm_ltm_test' : b.gm_ltm.quantile(q = 0.5), # greater than  June 2020 top quartile,.555943 median = .345134
                'dividend_growth_3_test': b.dividend_growth_3.quantile(q = 0.5), # greater than June 2020 median Top quartile is 0.011755
                'ebitda_margin_ltm_test': b.ebitda_margin_ltm.quantile(q = .75), # greater than June 2020 Top quartile, median is .0659
                'sgam_ltm_test': b.sgam_ltm.quantile(q = 0.5), # greater than  June 2020 median, low quartile = .108991 high q = .439870
                'revenue_growth_3_test': b.revenue_growth_3.quantile(q = 0.5), # greater than  June 2020 median. Top quartile = .450341
                'revenue_growth_max_test': .14, # greater than original Sagard test
                'market_leader_test' : 1, # greater than market leader score will be a year if so or 0 if NOT

                'capex_to_revenue_avg_3_test': b.capex_to_revenue_avg_3.quantile(q = 0.5), # greater than June 2020 top quartile, median = .028490
                'roic_change_from_ic_test' : 0, # less than
                'surplus_cash_as_percent_of_price_test':b.surplus_cash_as_percent_of_price.quantile(q = .75), # greater than June 2020 top quartile is .123063, median is -.113380
                'additional_debt_from_ebitda_multiple_per_share_test' : 0, # greater than
                'icf_avg_3_to_fcf_test': 1, # greater than
                'icf_to_ocf_test': ( b.icf_ltm / b.ocf_ltm ).quantile(q = .75), # greater than  June 2020 high quartile .142, median is -.274591
                'equity_sold_test': b.equity_sold.quantile(q = .75), # greater than June 2020 top quartile
                'financing_acquired_test': b.financing_acquired.quantile(q = 0.5), # greater than June 2020 median
                'capex_to_ocf_test': b.capex_to_ocf.quantile(q = 0.5), # greater than June 2020 median.  High quartile is .396726

                'icf_and_ocf_negative_test': 0, # should not be the case
                'net_debt_to_ebitda_ltm_test': 3, # greater than original Sagard test. current June 2020 median is 1.975
                'ebitda_to_interest_coverage_test': b.ebitda_to_interest_coverage.quantile(q = 0.5), # less than June 2020 median

                'short_interest_ratio_test': b.short_interest_ratio.quantile(q = 0.5), # greater than June 2020 top quartile 7.26, median = 3.92
                'insider_ownership_total_test': b.insider_ownership_total.quantile(q = .75), # greater than June 2020 top quartile .182050, median = .0607
                'insiders_can_get_out_quickly_test': (b.insider_ownership_total / b.adv_as_percent_so ).quantile(q = .75), # greater than June 2020 top quartile
                'adv_avg_months_3_test': b.adv_avg_months_3.quantile(q = 0.5), # less than June 2020 median
                'float_test': b.float.quantile(q = 0.25), # less than June 2020 lowest quartile
                'insiders_selling_ltm_test': b.insiders_selling_ltm.quantile(q = 0.5), # less than June 2020 median; lowest quartile is 0

                'price_opp_at_em_high_test' : 1.3, # greater than June 2020 median is 0.909
                'price_opp_at_sgam_low_test': 1.2, # greater than June 2020 median is 0.9837
                'price_opp_at_roic_high_test': 1.2, # greater than June 2020 median is 1.167, high quartile is 1.5
                }


    # Set up a return dictionary with all the test defintions
    returndict = {
            'TESTS': TESTS,
            'valuation_tests': valuation_tests,
            'valuation': valuation,
            'sbm_tests': sbm_tests,
            'sbm': sbm,
            'puoc_tests': puoc_tests,
            'puoc': puoc,
            'bs_risks_tests': bs_risks_tests,
            'bs_risks': bs_risks,
            'trade_tests': trade_tests,
            'trade': trade,
            'experience_tests': experience_tests,
            'experience': experience,
            'tests' : tests
            }

    return returndict

def run_tests(df_in = pd.DataFrame(), tests = []):
    # This function takes a datafraame of scores and runs tests on it.
    # And returns the updated dataframe with new tests run
    # It assumes the input dataframe has all the right data in it already

    from getdata_325 import get_master_screen_sheets

    if df_in.empty:
        print ('Cant run tests - datafrme is empty')
        return None

    df = df_in.copy()

    # tests
    # Get the tests to use from set_tests. Don't send in a dataframe for live tests
    #   Note: set_tests returns a dict with 'tests' key as the main tests list
    if len(tests) == 0:
        tests = set_tests()['tests']

    ttfdf = get_master_screen_sheets('Screen Mar 2020')

    for i in df.index:
        try:
            # valuation tests
            df.loc[i,'ev_to_ebitda_ltm_test'] = df.loc[i,'ev_to_ebitda_ltm'] <= tests['ev_to_ebitda_ltm_test']
            df.loc[i,'pe_to_mid_cycle_ratio_test']  = df.loc[i,'pe_to_mid_cycle_ratio'] <= tests['pe_to_mid_cycle_ratio_test']
            df.loc[i,'price_change_52_test'] = df.loc[i,'price_change_52'] <= tests['price_change_52_test']
            valuation_tests = [
                    'pe_to_mid_cycle_ratio_test',
                    'ev_to_ebitda_ltm_test',
                    'price_change_52_test'
                    ]
            # When getting average, fill NAs with 0
            df.loc[i,'VALUATION_test'] = sum(df.loc[i,valuation_tests].fillna(0)) / len(valuation_tests)

            # superior business model tests
            df.loc[i,'roic_high_5_test'] = df.loc[i,'roic_high_5'] >= tests['roic_high_5_test']
            df.loc[i,'dividend_growth_3_test'] = df.loc[i,'dividend_growth_3'] >= tests['dividend_growth_3_test']
            df.loc[i,'gm_ltm_test'] = df.loc[i,'gm_ltm'] >= tests['gm_ltm_test']
            df.loc[i,'ebitda_margin_ltm_test'] = df.loc[i,'ebitda_margin_ltm'] >= tests['ebitda_margin_ltm_test']
            df.loc[i,'sgam_ltm_test'] = df.loc[i,'sgam_ltm'] <= tests['sgam_ltm_test']
            df.loc[i,'revenue_growth_3_test'] = df.loc[i,'revenue_growth_3'] > tests['revenue_growth_3_test']
            df.loc[i,'revenue_growth_max_test'] = df.loc[i,'revenue_growth_3'] > tests['revenue_growth_max_test']
            try:
                df.loc[i,'market_leader_test'] = ttfdf.market_leader_test[i] >= tests['market_leader_test']
                df.loc[i,'market_leader'] = 1
            except:
                df.loc[i,'market_leader_test'] = False
                df.loc[i,'market_leader'] = 0

            sbm_tests = [
                'roic_high_5_test',
                'dividend_growth_3_test',
                'gm_ltm_test',
                'ebitda_margin_ltm_test',
                'sgam_ltm_test',
                'revenue_growth_3_test',
                'revenue_growth_max_test',
                'market_leader_test'
                ]
            df.loc[i,'SBM_test'] = sum(df.loc[i,sbm_tests].fillna(0)) / len(sbm_tests)

            # poor use of cash tests / watch-outs (lower is better)
            df.loc[i,'capex_to_revenue_avg_3_test'] = df.loc[i,'capex_to_revenue_avg_3'] >= tests['capex_to_revenue_avg_3_test']
            df.loc[i,'roic_change_from_ic_test'] = df.loc[i,'roic_change_from_ic'] <= tests['roic_change_from_ic_test']
            df.loc[i,'surplus_cash_as_percent_of_price_test'] = df.loc[i,'surplus_cash_as_percent_of_price'] >= tests['surplus_cash_as_percent_of_price_test']
            df.loc[i,'additional_debt_from_ebitda_multiple_per_share_test'] = df.loc[i,'additional_debt_from_ebitda_multiple_per_share'] >= tests['additional_debt_from_ebitda_multiple_per_share_test']
            df.loc[i,'icf_avg_3_to_fcf_test'] = df.loc[i,'icf_avg_3_to_fcf'] >= tests['icf_avg_3_to_fcf_test']
            df.loc[i,'icf_to_ocf'] = df.loc[i,'icf_ltm'] / df.loc[i,'ocf_ltm']
            df.loc[i,'icf_to_ocf_test'] = df.loc[i,'icf_to_ocf'] >= tests['icf_to_ocf_test']
            df.loc[i,'equity_sold_test'] = df.loc[i,'equity_sold'] >= tests['equity_sold_test']
            df.loc[i,'financing_acquired_test'] = df.loc[i,'financing_acquired'] >= tests['financing_acquired_test']
            df.loc[i,'capex_to_ocf_test'] = df.loc[i,'capex_to_ocf'] >= tests['capex_to_ocf_test']
            puoc_tests = [
                'capex_to_revenue_avg_3_test',
                'roic_change_from_ic_test',
                'surplus_cash_as_percent_of_price_test',
                'additional_debt_from_ebitda_multiple_per_share_test',
                'icf_avg_3_to_fcf_test',
                'icf_to_ocf_test',
                'equity_sold_test',
                'financing_acquired_test',
                'capex_to_ocf_test'
                ]
            df.loc[i,'PUOC_test'] = sum(df.loc[i,puoc_tests].fillna(0)) / len(puoc_tests)

            # balance sheet risk tests (lower is better)
            df.loc[i,'icf_and_ocf_negative'] = (df.loc[i,'icf_ltm'] < 0) & (df.loc[i,'ocf_ltm'] < 0)
            df.loc[i,'icf_and_ocf_negative_test'] = (df.loc[i,'icf_ltm'] < 0) & (df.loc[i,'ocf_ltm'] < 0)
            df.loc[i,'net_debt_to_ebitda_ltm_test'] = df.loc[i,'net_debt_to_ebitda_ltm'] >= tests['net_debt_to_ebitda_ltm_test']
            df.loc[i,'ebitda_to_interest_coverage_test'] = df.loc[i,'ebitda_to_interest_coverage'] <= tests['ebitda_to_interest_coverage_test']
            bs_risks_tests = [
                'icf_and_ocf_negative_test',
                'net_debt_to_ebitda_ltm_test',
                'ebitda_to_interest_coverage_test',
                ]
            df.loc[i,'BS_risks_test'] = sum(df.loc[i,bs_risks_tests].fillna(0)) / len(bs_risks_tests)

            # trading issues tests (lower is better)
            df.loc[i,'short_interest_ratio_test'] = df.loc[i,'short_interest_ratio'] >= tests['short_interest_ratio_test']
            df.loc[i,'insider_ownership_total_test'] = df.loc[i,'insider_ownership_total'] >= tests['insider_ownership_total_test']
            df.loc[i,'insiders_can_get_out_quickly'] = df.loc[i,'insider_ownership_total'] / df.loc[i,'adv_as_percent_so']
            df.loc[i,'insiders_can_get_out_quickly_test'] = df.loc[i, 'insiders_can_get_out_quickly'] >= tests['insiders_can_get_out_quickly_test']
            df.loc[i,'adv_avg_months_3_test'] = df.loc[i,'adv_avg_months_3'] <= tests['adv_avg_months_3_test']
            df.loc[i,'float_test'] = df.loc[i,'float'] <= tests['float_test']
            df.loc[i,'insiders_selling_ltm_test'] = df.loc[i,'insiders_selling_ltm'] <= tests['insiders_selling_ltm_test']
            trade_tests = [
                'short_interest_ratio_test',
                'insider_ownership_total_test',
                'insiders_can_get_out_quickly_test',
                'adv_avg_months_3_test',
                'float_test',
                'insiders_selling_ltm_test'
                ]
            df.loc[i,'TRADE_test'] = sum(df.loc[i,trade_tests].fillna(0)) / len(trade_tests)

            # performance improvement opp tests
            df.loc[i,'price_opp_at_em_high_test'] = df.loc[i,'price_opp_at_em_high'] >= tests['price_opp_at_em_high_test']
            df.loc[i,'price_opp_at_sgam_low_test'] = df.loc[i,'price_opp_at_sgam_low'] >= tests['price_opp_at_sgam_low_test']
            df.loc[i,'price_opp_at_roic_high_test'] = df.loc[i,'price_opp_at_roic_high'] >= tests['price_opp_at_roic_high_test']
            pi_tests = [
                'price_opp_at_roic_high_test',
                'price_opp_at_sgam_low_test',
                'price_opp_at_em_high_test',
                ]
            df.loc[i,'PI_test'] = sum(df.loc[i,pi_tests].fillna(0)) / len(pi_tests)
        except:
            print('Cant run tests on input dataframe, check the dataframe and try again')
            return None

    return df

def weight_tests(df_in = pd.DataFrame(), weights = []):
    # This function sets tests and returns the key variables in a dictonary
    # So that calling functions have access to the latest tests
    # If the function is called with a proper dataframe, d, it will calculate
    # live tests based on those and return that.

    TESTS = ['VALUATION_test', 'SBM_test', 'PUOC_test', 'BS_risks_test', 'TRADE_test', 'PI_tests']
    valuation_tests = [
       'pe_to_mid_cycle_ratio_test',
       'ev_to_ebitda_ltm_test',
       'price_change_52_test'
       ]
    sbm_tests = [
        'roic_high_5_test',
        'dividend_growth_3_test',
        'gm_ltm_test',
        'ebitda_margin_ltm_test',
        'sgam_ltm_test',
        'revenue_growth_3_test',
        'revenue_growth_max_test',
        'market_leader_test'
        ]

    puoc_tests = [
        'capex_to_revenue_avg_3_test',
        'roic_change_from_ic_test',
        'surplus_cash_as_percent_of_price_test',
        'additional_debt_from_ebitda_multiple_per_share_test',
        'icf_avg_3_to_fcf_test',
        'icf_to_ocf_test',
        'equity_sold_test',
        'financing_acquired_test',
        'capex_to_ocf_test'
        ]
    bs_risks_tests = [
        'icf_and_ocf_negative_test',
        'net_debt_to_ebitda_ltm_test',
        'ebitda_to_interest_coverage_test',
        ]
    trade_tests = [
        'short_interest_ratio_test',
        'insider_ownership_total_test',
        'insiders_can_get_out_quickly_test',
        'adv_avg_months_3_test',
        'float_test',
        'insiders_selling_ltm_test'
        ]
    pi_tests = [
            'price_opp_at_em_high_test' ,
            'price_opp_at_sgam_low_test',
            'price_opp_at_roic_high_test',
            ]

    valuation = [
       'pe_to_mid_cycle_ratio',
       'ev_to_ebitda_ltm',
       'price_change_52'
       ]

    sbm = [
        'roic_high_5',
        'dividend_growth_3',
        'gm_ltm',
        'ebitda_margin_ltm',
        'sgam_ltm',
        'revenue_growth_3',
        'revenue_growth_max',
        'market_leader'
        ]

    puoc = [
        'capex_to_revenue_avg_3',
        'roic_change_from_ic',
        'surplus_cash_as_percent_of_price',
        'additional_debt_from_ebitda_multiple_per_share',
        'icf_avg_3_to_fcf',
        'icf_to_ocf',
        'equity_sold',
        'financing_acquired',
        'capex_to_ocf'
        ]

    bs_risks = [
        'icf_and_ocf_negative',
        'net_debt_to_ebitda_ltm',
        'ebitda_to_interest_coverage',
        ]

    trade = [
        'short_interest_ratio',
        'insider_ownership_total',
        'insiders_can_get_out_quickly',
        'adv_avg_months_3',
        'float',
        'insiders_selling_ltm'
        ]

    pi = [
            'price_opp_at_em_high' ,
            'price_opp_at_sgam_low',
            'price_opp_at_roic_high',
            ]

    # Weights can be anything, but let's try between 0 and 1
    if len(weights) == 0:
        weights = {
                'ev_to_ebitda_ltm_test'                                  :1, # less than June 2020 median is 7.19. High qartile is 12.33, low quartile is -5.31
                'pe_to_mid_cycle_ratio_test'                             :0, # less than  June 2020 low quartile is .533632, high q is 1.49
                'price_change_52_test'                                   :1, # less than June 2020 median, low quartile is -.3875, high q is .182
                'price_change_last_Q_test'                               :0, # less than  June 2020 low q, median is .2952, high q is .596285

                'roic_high_5_test'                                       :0, # greater than June 2020 top quartile
                'gm_ltm_test'                                            :1, # greater than  June 2020 top quartile,.555943 median = .345134
                'dividend_growth_3_test'                                 :0, # greater than June 2020 median Top quartile is 0.011755
                'ebitda_margin_ltm_test'                                 :1, # greater than June 2020 Top quartile, median is .0659
                'sgam_ltm_test'                                          :0, # greater than  June 2020 median, low quartile = .108991 high q = .439870
                'revenue_growth_3_test'                                  :1, # greater than  June 2020 median. Top quartile = .450341
                'revenue_growth_max_test'                                :0, # greater than original Sagard test
                'market_leader_test'                                     :1, # greater than market leader score will be a year if so or 0 if NOT

                'capex_to_revenue_avg_3_test'                            :1, # greater than June 2020 top quartile, median = .028490
                'roic_change_from_ic_test'                               :0, # less than
                'surplus_cash_as_percent_of_price_test'                  :0, # greater than June 2020 top quartile is .123063, median is -.113380
                'additional_debt_from_ebitda_multiple_per_share_test'    :0, # greater than
                'icf_avg_3_to_fcf_test'                                  :0, # greater than
                'icf_to_ocf_test'                                        :0, # greater than  June 2020 high quartile .142, median is -.274591
                'equity_sold_test'                                       :1, # greater than June 2020 top quartile
                'financing_acquired_test'                                :1, # greater than June 2020 median
                'capex_to_ocf_test'                                      :1, # greater than June 2020 median.  High quartile is .396726
                'icf_and_ocf_negative_test'                              :1, # should not be the case

                'net_debt_to_ebitda_ltm_test'                            :1, # greater than original Sagard test. current June 2020 median is 1.975
                'ebitda_to_interest_coverage_test'                       :1, # less than June 2020 median

                'short_interest_ratio_test'                              :0, # greater than June 2020 top quartile 7.26, median = 3.92
                'insider_ownership_total_test'                           :0, # greater than June 2020 top quartile .182050, median = .0607
                'insiders_can_get_out_quickly_test'                      :1, # greater than June 2020 top quartile
                'adv_avg_months_3_test'                                  :1, # less than June 2020 median
                'float_test'                                             :1, # less than June 2020 lowest quartile
                'insiders_selling_ltm_test'                              :1, # less than June 2020 median; lowest quartile is 0

                'price_opp_at_em_high_test'                              :1, # greater than June 2020 median is 0.909
                'price_opp_at_sgam_low_test'                             :1, # greater than June 2020 median is 0.9837
                'price_opp_at_roic_high_test'                            :1, # greater than June 2020 median is 1.167, high quartile is 1.5
                }

    # Make a copy so that we don't accidentally trash original dataframe
    d = df_in.copy()

    # Go through all the stocks in the data (even if it just one)
    for i in d.index:

        # For each one, calculate a new scores, weighted by the weights
        weighted_score = 0
        weight_sum = 0
        for test in valuation_tests:
            weighted_score += d.loc[i,test] * weights[test]
            weight_sum += weights[test]
        d.loc[i, 'w_val_test'] = weighted_score / weight_sum

        weighted_score = 0
        weight_sum = 0
        for test in sbm_tests:
            weighted_score += d.loc[i,test] * weights[test]
            weight_sum += weights[test]
        d.loc[i, 'w_sbm_test'] = weighted_score / weight_sum

        weighted_score = 0
        weight_sum = 0
        for test in puoc_tests:
            weighted_score += d.loc[i,test] * weights[test]
            weight_sum += weights[test]
        d.loc[i, 'w_puoc_test'] = weighted_score / weight_sum

        weighted_score = 0
        weight_sum = 0
        for test in bs_risks_tests:
            weighted_score += d.loc[i,test] * weights[test]
            weight_sum += weights[test]
        d.loc[i, 'w_bs_risks_test'] = weighted_score / weight_sum

        weighted_score = 0
        weight_sum = 0
        for test in trade_tests:
            weighted_score += d.loc[i,test] * weights[test]
            weight_sum += weights[test]
        d.loc[i, 'w_trade_test'] = weighted_score / weight_sum

        weighted_score = 0
        weight_sum = 0
        for test in pi_tests:
            weighted_score += d.loc[i,test] * weights[test]
            weight_sum += weights[test]
        d.loc[i, 'w_pi_test'] = weighted_score / weight_sum

    return d

