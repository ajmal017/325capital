import sys
import pandas as pd
import yahoo_fin.stock_info as si

ticker = sys.argv[1]
directory = sys.argv[2] if len(sys.argv) >=3 else '/home/michael/Documents/325capital/CanalystModels/'


# load the dictionary with most recent fiscal periods (MRFP)
with open('mrfp.txt') as f:
    mrfp_dict = eval(f.read())
print('MRFP dictionary loaded')

# lookup the MRFP for the ticker.  If missing, prompt for it.
mrfp = mrfp_dict.get(ticker) \
        or input('The most recent fiscal period for {0} is missing\nPlease enter the most recent fiscal period in format QQ-YYYY\n'.format(ticker))
print('The most recent fiscal period for {0} is {1}'.format(ticker, mrfp))

# make sure the ticker is in the dict and save the MRFP dict to a file
mrfp_dict[ticker] = mrfp
with open('mrfp.txt', 'w') as f:
    f.write( str(mrfp_dict) )

# load the dictionary linking tickers to filenames, check to see if ticker in filename dictionary, prompt for it if missing then add to dictionary
with open('modeldict.txt') as f:
    model_dict = eval(f.read())
print('model list loaded')

# lookup the filename for the ticker.  If missing, prompt for it.
model_name = model_dict.get(ticker) \
        or input('The model name for {0} is unknown\nPlease enter the model name, leaving off .xlsx\n'.format(ticker))

# make sure the model name is in the dict and save the modelname dict to a file
model_dict[ticker] = model_name
with open('modeldict.txt', 'w') as f:
    f.write( str(model_dict) )

print('Preparing to import and clean the {0} model from the file "{1}" located in {2}'.format(ticker, model_dict[ticker], directory))

# create a pandas dataframe from the Model sheet of the Canalyst file
path = directory +  model_dict[ticker] + ".xlsx"
can_model = pd.read_excel(path, sheet_name='Model', header=4, index_col=0)
print('The model has been imported')

# drop blank rows
temp_model = can_model[can_model.index.notnull()]

# drop blank columns
temp_model = temp_model.loc[:,~temp_model.columns.str.startswith('Unn')]

# create list of section names in preparation for adding second index
section_names = {
        'Growth Analysis'                   : 'growth',
        'Margin Analysis'                   : 'margin',
        'Segmented Results Breakdown (FS)'  : 'segments',
        'Key Metrics - Backlog (FS)'        : 'backlog',
        'Segmented Results Breakdown - Historical (FS)' : 'segments_historical',
        'Income Statement - As Reported'    : 'is',
        'Adjusted Numbers - As Reported'    : 'adj_is',
        'GAAP EPS'                          : 'eps',
        'Revised Income Statement'          : 'ris',
        'Cash Flow Summary'                 : 'cf_sum',
        'Balance Sheet Summary'             : 'bs_sum',
        'Valuation'                         : 'valuation',
        'Cumulative Cash Flow Statement'    : 'cum_cf',
        'Cash Flow Statement'               : 'cf',
        'Working Capital Forecasting'       : 'wc',
        'Current Assets'                    : 'bs_ca',
        'Current Assets'                    : 'bs_ca',
        'Non-Current Assets'                : 'bs_nca',
        'Current Liabilities'               : 'bs_cl',
        'Non-Current Liabilities'           : 'bs_ncl',
        "Shareholders' Equity"              : 'bs_se',
        'Model Checks'                      : 'model_checks',
        'Other Tables'                      : 'other_tables'
        }

# set initial section index to 'Misc' to capture variability of the models in the initial sections
current_section = 'misc'

# loop through the column list and create a corresponding list of the section names
section_index = []
x = 1
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
fields = fields.str.replace('(','')
fields = fields.str.replace(')','')
fields = temp_model.section.values + '_' + fields
fields_debug = fields.copy()

# take care of any remaining duplicate index items
for dup in fields[fields.duplicated()].unique():
    fields[fields[fields == dup].index.values.tolist()] = [dup + '.' + str(i) if i != 0 else dup for i in range(sum(fields==dup))] #left side items by row no / right side the numbered names
fields_debug2 = fields.copy()

temp_model['std_field'] = fields.values
temp_model_debug = temp_model.copy()
# reset index and then set indexe to 'std_field'
# possible to set second index of 'section', but cell selection seems to get much more complicated
#temp_model.reset_index()
temp_model = temp_model.set_index('std_field')
debug_model1 = temp_model.copy()

# set index and column titles
#temp_model.index.names = ['field','section']
temp_model.columns.names = ['period']

model = temp_model.T #transpose the model so that the periods become the row index

# if stock_issuance column missing, then set it to 0
#if 'stock_issuance' not in model:
#    model['stock_issuance'] = 0

# net share capital
# if 'net_shares_issued' not in model.columns.tolist():
#    model['net_shares_issued'] = model.stock_repurchases + model.stock_issuance

# net debt issued
# if 'net_debt_issued' not in model.columns.tolist():
#    model['net_debt_issued'] = model.debt - model.debt.shift(1)

# split into two dataframes, one for quarters and one for fiscal years
model_q = model[model.index.str.startswith('Q')].copy()
model_fy = model[model.index.str.startswith('F')].copy()

# define key calculations
# series to allow for checks of field names
fields = pd.Series(model_q.columns)

# revenue growth
model_q['net_revenue_ttm'] = model_q.ris_net_revenue.rolling(4).sum()
model_q['net_revenue_growth_3_yr'] = ( model_q.net_revenue_ttm / model_q.net_revenue_ttm.shift(12) )**(1/3) - 1

# sources and uses of cash over last 3 years
# free cash flow
model_q['fcf'] = model_q['cf_net_cfo'] + model_q['cf_sum_capex']
model_q['fcf_ttm'] = model_q.fcf.rolling(4).sum()
model_q['fcf_3_yrs'] = model_q.fcf.rolling(12).sum()
# M & A
model_q['ma'] = model_q['cf_sum_acquisitions'] + model_q['cf_sum_divestiture']
model_q['ma_ttm'] = model_q.ma.rolling(4).sum()
model_q['ma_3_yrs'] = model_q.ma.rolling(12).sum()
# shareholder cash flows
if 'cf_sum_net_share_issuance_buybacks' not in fields.values:
    model_q['cf_sum_net_share_issuance_buybacks'] = model_q.cf_common_stock_repurchases + model_q.cf_common_stock_issuance # consider setting up 'startswith' search then summing in for loop?
model_q['shareholders'] = model_q['cf_sum_dividend_paid'] + model_q['cf_sum_net_share_issuance_buybacks']
model_q['shareholders_ttm'] = model_q.shareholders.rolling(4).sum()
model_q['shareholders_3_yrs'] = model_q.shareholders.rolling(12).sum()
# debt cash flows
# if summary field missing, then create it from source data on cash flow statement
if 'cf_sum_net_debt_issuance_repayment' not in fields.values:
    cols = model_q.columns[model_q.columns.str.startswith('cf_borrowings') | model_q.columns.str.startswith('cf_repayment')].values.tolist()
    colnum = [model_q.columns.get_loc(c) for c in cols]
    colsum = pd.Series(dtype='float')
    for i in colnum:
        if colsum.empty: colsum = pd.Series(model_q.iloc[:,i])
        else: colsum = colsum + pd.Series(model_q.iloc[:,i])
    model_q['cf_sum_net_debt_issuance_repayment'] = colsum
model_q['net_debt_issued_ttm'] = model_q.cf_sum_net_debt_issuance_repayment.rolling(4).sum()
model_q['net_debt_issued_3_yrs'] = model_q.cf_sum_net_debt_issuance_repayment.rolling(12).sum()

# Net Debt, excluding operating lease liability
model_q['net_debt'] = model_q.bs_sum_net_debt

# earnings power
# create any missing fields from source statements
if 'ris_adjusted_ebitda' not in fields.values:
    colname = model_q.columns[model_q.columns.str.startswith('ris_adjusted_ebitda')].values.tolist()
    model_q['ris_adjusted_ebitda'] = model_q[colname]

model_q['ep'] = ( model_q.ris_adjusted_ebitda + model_q.cf_sum_capex ) * .7
model_q['ep_ttm'] = model_q.ep.rolling(4).sum()
model_q['capex_ttm'] = model_q.cf_sum_capex.rolling(4).sum()

# estimated market value
model_q['est_market_cap'] = model_q.ep_ttm * 10 - model_q.bs_sum_net_debt

# est market value from 3-year average free cash flow
model_q['avg_fcf_3_yrs'] = model_q.fcf_3_yrs / 3
model_q['value_from_fcf'] = model_q.avg_fcf_3_yrs * 10

# est market value from return to peak EBITDA margins
model_q['adj_ebitda_ttm'] = model_q.ris_adjusted_ebitda.rolling(4).sum()
model_q['net_revenue_ttm'] = model_q.ris_net_revenue.rolling(4).sum()
model_q['adj_ebitda_margin_ttm'] = model_q['adj_ebitda_ttm'] / model_q['net_revenue_ttm']
model_q['adj_ebitda_margin_high_5_yrs'] = model_q.adj_ebitda_margin_ttm.rolling(20).max()
model_q['value_from_ebitda_margin'] = ( model_q.adj_ebitda_margin_high_5_yrs - model_q.adj_ebitda_margin_ttm ) * model_q.net_revenue_ttm * 10 * .7

# value from achieving peak 5-year ROIC on last 3 year change in IC
model_q['ic'] = model_q.bs_sum_net_debt + model_q.bs_se_total_se
model_q['avg_ic'] = ( model_q.ic + model_q.ic.shift(2) + model_q.ic.shift(3) + model_q.ic.shift(4) ) / 4
model_q['roic_ttm'] = model_q.ep_ttm / model_q.avg_ic
model_q['roic_high_5_yrs'] = model_q.roic_ttm.rolling(20).max()
model_q['change_ic_3_yrs'] = model_q.ic - model_q.ic.shift(12)
model_q['change_ep_3_yrs'] = model_q.ep_ttm - model_q.ep_ttm.shift(12)
model_q['change_ep_change_ic_3_yrs'] = model_q.change_ep_3_yrs / model_q.change_ic_3_yrs
model_q['value_from_ic'] = model_q.change_ic_3_yrs * model_q.roic_high_5_yrs * 10 - model_q.change_ic_3_yrs

# sum of potential values
model_q['total_est_value'] = model_q.est_market_cap + model_q.value_from_fcf + model_q.value_from_ebitda_margin + model_q.value_from_ic

# set display columns for potential value summary
display_value_summary = ['net_revenue_ttm', 'adj_ebitda_ttm', 'adj_ebitda_margin_ttm', 'capex_ttm', 'ep_ttm', 'net_revenue_growth_3_yr', 'roic_ttm', 'net_debt', 'est_market_cap', 'fcf_ttm', 'avg_fcf_3_yrs', 'value_from_fcf', 'adj_ebitda_margin_high_5_yrs', 'value_from_ebitda_margin', 'change_ep_3_yrs', 'change_ic_3_yrs', 'roic_high_5_yrs', 'value_from_ic', 'change_ep_change_ic_3_yrs', 'total_est_value']

# set display for potential value relative to current market cap
yahoo_quote = si.get_quote_table(ticker)
market_cap_units = yahoo_quote['Market Cap'][-1]
market_cap = float(yahoo_quote['Market Cap'][0:-1]) #drop units and convert string to type float
if (market_cap_units == 'B'): market_cap = market_cap * 1000

# print some output
print('\n\n')
print('The model for {0} has been imported'.format(ticker))
print('The current market cap is ${0:,.0f}mm'.format(market_cap))
print('\n')
print(model_q.loc[mrfp_dict[ticker]][display_value_summary])
print('\n')
print('The estimated value from each source:')
print('current ep:\t{0:.1f}x'.format(model_q.est_market_cap[mrfp]/market_cap))
print('avg fcf:\t{0:.1f}x'.format(model_q.value_from_fcf[mrfp]/market_cap))
print('margin:\t\t{0:.1f}x'.format(model_q.value_from_ebitda_margin[mrfp]/market_cap))
print('growth:\t\t{0:.1f}x'.format(model_q.value_from_ic[mrfp]/market_cap))
print('-----------\t----')
print('total:\t\t{0:.1f}x'.format(model_q.total_est_value[mrfp]/market_cap))
