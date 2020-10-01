import sys
import pandas as pd

ticker = sys.argv[1]
directory = '/home/michael/Documents/325capital/CanalystModels/'

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
        'Margin Analysis'                   : 'margin',
        'Income Statement - As Reported'    : 'is',
        'Adjusted Numbers - As Reported'    : 'adj_is',
        'Revised Income Statement'          : 'ris',
        'Cash Flow Summary'                 : 'cf_sum',
        'Balance Sheet Summary'             : 'bs_sum',
        'Valuation'                         : 'valuation',
        'Cumulative Cash Flow Statement'    : 'cum_cf',
        'Cash Flow Statment'                : 'cf',
        'Working Capital Forecasting'       : 'wc',
        'Balance Sheet'                     : 'bs',
        'Model Checks'                      : 'model_checks',
        'Other Tables'                      : 'other_tables'
        }

# set initial section index to 'Misc' to capture variability of the models in the initial sections
current_section = 'misc'

# loop through the column list and create a corresponding list of the section names
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
fields = temp_model.index
std_field = fields.str.lower()
std_field = std_field.str.replace(' ', '_')
std_field = temp_model.section + '_' + std_field
temp_model['std_field'] = std_field

# reset index and then set indexe to 'std_field'
# possible to set second index of 'section', but cell selection seems to get much more complicated
#temp_model.reset_index()
temp_model = temp_model.set_index('std_field')

# set index and column titles
#temp_model.index.names = ['field','section']
temp_model.columns.names = ['period']

model = temp_model.T #transpose the model so that the periods become the row index

cols = pd.Series(clean_model.columns) #create list of indexed column names in preparation for renaming duplicates
for dup in cols[cols.duplicated()].unique():
    cols[cols[cols == dup].index.values.tolist()] = [dup + '.' + str(i) if i != 0 else dup for i in range(sum(cols == dup))] #left side creates an array of the column numbers with the duplicate names
clean_model.columns=cols # rename the columns with the cols list.

# list of column names to change
std_names = {
        'Net Revenue'                   : 'net_revenue',
        'Gross Profit'                  : 'gross_profit',
        'EBITDA'                        : 'ebitda',
        'Adjusted EBITDA.1'             : 'adj_ebitda',
        'Adjusted EBITDA (No Adjustements)' : 'adj_ebitda',
        'Adjusted EBITDA (No Adjustments).1' : 'adj_ebitda', 
        'D&A'                           : 'd&a',
        'EBIT'                          : 'ebit',
        'Interest Expense'              : 'interest_exp',
        'Interest expense'               : 'interest_exp',
        'Operating Cash Flow before WC' : 'ocf_before_wc',
        'Capex'                         : 'capex',
        'Acquisitions'                  : 'acquisitions',
        'Divestiture'                   : 'divestitures',
        'Dividend Paid'                 : 'dividends',
        'Net Debt Issuance (Repayment)' : 'net_debt_issued',
        'Net Share Issuance (Buybacks)' : 'net_shares_issued',
        'Common stock repurchases'      : 'stock_repurchases',
        'Repurchases of common stock in the open market' : 'stock_repurchases',
        'Repurchases of common stock'   : 'stock_repurchases',
        'Common stock issuance'         : 'stock_issuance',
        'Proceeds from issuance of common stock' : 'stock_issuance',
        'Cash'                          : 'cash',
        'Debt'                          : 'debt',
        'Net CFO.1'                     : 'cfo',
        'Total SE'                      : 'shareholder_equity'
        }

# update column headers to standards defined in std_names
std_model = clean_model.rename(columns=std_names)
print('Standard column names are in place')

# if stock_issuance column missing, then set it to 0
#if 'stock_issuance' not in std_model:
#    std_model['stock_issuance'] = 0

# net share capital
if 'net_shares_issued' not in std_model.columns.tolist():
    std_model['net_shares_issued'] = std_model.stock_repurchases + std_model.stock_issuance

# net debt issued
if 'net_debt_issued' not in std_model.columns.tolist():
    std_model['net_debt_issued'] = std_model.debt - std_model.debt.shift(1)

# check for missing columns
checklist = list(std_names.values())
model_columns = std_model.columns.tolist()
missing = set(checklist).difference(model_columns)
print('The following columns are missing')
print(missing)

# display standard fields from most recent fiscal period
#std_name_list = list(std_names.values())
#print('Key data from the most recent fiscal period {0}'.format(mrfp_dict[ticker]))
#print(std_model.loc[mrfp_dict[ticker]][std_name_list])

# split into two dataframes, one for quarters and one for fiscal years
std_model_q = std_model[std_model.index.str.startswith('Q')]
std_model_fy = std_model[std_model.index.str.startswith('F')]

# define key calculations

# revenue growth
std_model_q['net_revenue_ttm'] = std_model_q.net_revenue.rolling(4).sum()
std_model_q['net_revenue_growth_3_yr'] = ( std_model_q.net_revenue_ttm / std_model_q.net_revenue_ttm.shift(12) )**(1/3) - 1

# sources and uses of cash over last 3 years
# free cash flow
std_model_q['fcf'] = std_model_q['cfo'] + std_model_q['capex']
std_model_q['fcf_ttm'] = std_model_q.fcf.rolling(4).sum()
std_model_q['fcf_3_yrs'] = std_model_q.fcf.rolling(12).sum()
# M & A
std_model_q['ma'] = std_model_q['acquisitions'] + std_model_q['divestitures']
std_model_q['ma_ttm'] = std_model_q.ma.rolling(4).sum()
std_model_q['ma_3_yrs'] = std_model_q.ma.rolling(12).sum()
# shareholder cash flows
std_model_q['shareholders'] = std_model_q['dividends'] + std_model_q['net_shares_issued']
std_model_q['shareholders_ttm'] = std_model_q.shareholders.rolling(4).sum()
std_model_q['shareholders_3_yrs'] = std_model_q.shareholders.rolling(12).sum()
# debt cash flows
std_model_q['net_debt_issued_ttm'] = std_model_q.net_debt_issued.rolling(4).sum()
std_model_q['net_debt_issued_3_yrs'] = std_model_q.net_debt_issued.rolling(12).sum()

# Net Debt, excluding operating lease liability
std_model_q['net_debt'] = std_model_q.debt - std_model_q.cash

# earnings power
std_model_q['ep'] = ( std_model_q.ebitda + std_model_q.capex ) * .7
std_model_q['ep_ttm'] = std_model_q.ep.rolling(4).sum()
std_model_q['capex_ttm'] = std_model_q.capex.rolling(4).sum()

# estimated market value
std_model_q['est_market_cap'] = std_model_q.ep_ttm * 10 - std_model_q.net_debt

# est market value from 3-year average free cash flow
std_model_q['avg_fcf_3_yrs'] = std_model_q.fcf_3_yrs / 3
std_model_q['value_from_fcf'] = std_model_q.avg_fcf_3_yrs * 10

# est market value from return to peak EBITDA margins
std_model_q['adj_ebitda_ttm'] = std_model_q.adj_ebitda.rolling(4).sum()
std_model_q['net_revenue_ttm'] = std_model_q.net_revenue.rolling(4).sum()
std_model_q['adj_ebitda_margin_ttm'] = std_model_q['adj_ebitda_ttm'] / std_model_q['net_revenue_ttm']
std_model_q['adj_ebitda_margin_high_5_yrs'] = std_model_q.adj_ebitda_margin_ttm.rolling(20).max()
std_model_q['value_from_ebitda_margin'] = ( std_model_q.adj_ebitda_margin_high_5_yrs - std_model_q.adj_ebitda_margin_ttm ) * std_model_q.net_revenue_ttm * 10 * .7

# value from achieving peak 5-year ROIC on last 3 year change in IC
std_model_q['ic'] = std_model_q.net_debt + std_model_q.shareholder_equity
std_model_q['avg_ic'] = ( std_model_q.ic + std_model_q.ic.shift(2) + std_model_q.ic.shift(3) + std_model_q.ic.shift(4) ) / 4
std_model_q['roic_ttm'] = std_model_q.ep_ttm / std_model_q.avg_ic 
std_model_q['roic_high_5_yrs'] = std_model_q.roic_ttm.rolling(20).max()
std_model_q['change_ic_3_yrs'] = std_model_q.ic - std_model_q.ic.shift(12)
std_model_q['change_ep_3_yrs'] = std_model_q.ep_ttm - std_model_q.ep_ttm.shift(12)
std_model_q['change_ep_change_ic_3_yrs'] = std_model_q.change_ep_3_yrs / std_model_q.change_ic_3_yrs
std_model_q['value_from_ic'] = std_model_q.change_ic_3_yrs * std_model_q.roic_high_5_yrs * 10 - std_model_q.change_ic_3_yrs

# set display columns for potential value summary
display_value_summary = ['net_revenue_ttm', 'adj_ebitda_ttm', 'capex_ttm', 'ep_ttm', 'net_revenue_growth_3_yr', 'roic_ttm', 'net_debt', 'est_market_cap', 'avg_fcf_3_yrs', 'value_from_fcf', 'adj_ebitda_margin_ttm', 'adj_ebitda_margin_high_5_yrs', 'value_from_ebitda_margin', 'change_ep_3_yrs', 'change_ic_3_yrs', 'roic_high_5_yrs', 'value_from_ic', 'change_ep_change_ic_3_yrs']

print(std_model_q.loc[mrfp_dict[ticker]][display_value_summary])
