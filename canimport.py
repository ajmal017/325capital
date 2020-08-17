# MRFP.txt is storing most recent fiscal period file_mrfp = open('mrfp.txt', 'r')
MRFP = eval(file_mrfp.read())
file_mrfp.close()

MRFP.update (<ticker> = '<qtr>-<year>')  #to update or add a ticker
file_mrfp = open('mrfp.txt', 'w')
file_mrfp.write( str(MRFP) )
file_mrfp.close()

<ticker>_model = pd.read_excel('path/to/file', sheet_name='Model', header=4, index_col=0)

<ticker> = <ticker>_model.T

df.drop(['<index_name>'], axis=0, inplace=True) #drop junk row

df = df.loc[:,df.columns.notnull()] #drop columns with NULL header

cols = pd.Series(df.columns) #create list of column names in preparation for renaming duplicates
for dup in cols[cols.duplicated()].unique():
    cols[cols[cols == dup].index.values.tolist()] = [dup + '.' + str(i) if i != 0 else dup for i in range(sum(cols == dup))] #left side creates an array of the column numbers with the duplicate names
df.columns=cols # rename the columns with the cols list.

# seperate quarters and fiscal years into independent dataframes
<ticker>Q = df[df.index.str.startswith('Q')]
<ticker>FY = df[df.index.str.startswith('FY')]


df.rename(columns={'<old header>':'new_header'}, inplace=True)  #clean up headers

# remove specific columns when duplicate names exist
<ticker>_col = pd.Series(df.columns)    #indexed list of column names

# rename frequently used columns
<ticker>.rename(columns={'Capital Expenditures.1':'cap_ex'})
'CFO Before WC.1' : 'cfo_before_wc'
'Net CFO.1' : 'net_cfo'
'Acquisitions, net of cash acquired.1':'acquisitions'
'Business divestitures.1':'divestitures'
'Adjusted EBITDA (No Adjustments).1' : 'adj_ebitda'
'Dividends paid.1' : 'dividends'
'Common stock repurchases.1' : 'stock_repurchases'
'Common stock issuance.1' : 'stock_issuance'
'Borrowings of long-term debt, net of issuance costs.1' : 'lt_debt_issued'
'Repayments of long-term debt.1' : 'lt_debt_repaid'
'Borrowings on lines of credit.1' : 'loc_borrowed'
'Repayments on lines of credit.1' : 'loc_repaid'

SCSQ['fcf_3_yrs'] = SCSQ.net_cfo_3_yrs + SCSQ.cap_ex_3_yrs
SCSQ['ma_3_yrs'] = SCSQ.acquisitions_3_yrs + SCSQ.divestitures_3_yrs
SCSQ['shareholders_3_yrs'] = SCSQ.dividends_3_yrs + SCSQ.stock_repurchases_3_yrs + SCSQ.stock_issuance_3_yrs
SCSQ['net_debt_3_yrs'] = SCSQ.lt_debt_repaid_3_yrs + SCSQ.lt_debt_issued_3_yrs + SCSQ.loc_borrowed_3_yrs + SCSQ.loc_repaid_3_yrs

SCSQ['est_change_cash_3_yrs'] = SCSQ.fcf_3_yrs + SCSQ.ma_3_yrs + SCSQ.shareholders_3_yrs + SCSQ.net_debt_3_yrs
SCSQ['actual_change_cash_3_yrs'] = SCSQ.Cash - SCSQ.Cash.shift(12)
'Adjusted EBITDA (No Adjustments)':'adj_ebitda'
SCSQ['net_debt'] = SCSQ.Cash - SCSQ.Debt
SCSQ['est_market_cap'] = SCSQ.ep_ttm * 10 + SCSQ['net_debt']
SCSQ.rename(columns={'Net Revenue' : 'net_revenue'}, inplace=True)
SCSQ['net_revenue_ttm'] = SCSQ.net_revenue.rolling(4).sum()
SCSQ['adj_ebitda_margin_ttm'] = SCSQ.adj_ebitda_ttm / SCSQ.net_revenue_ttm
SCSQ['ebitda_max_5'] = SCSQ.adj_ebitda_margin_ttm.rolling(20).max()
SCSQ['revenue_growth_3'] = ( SCSQ.net_revenue_ttm / SCSQ.net_revenue_ttm.shift(20) )**.2 -1
SCSQ['invested_capital'] = SCSQ.net_debt + SCSQ['Total SE']

display_sources_uses = ['fcf_3_yrs', 'ma_3_yrs', 'shareholders_3_yrs', 'net_debt_3_yrs', 'actual_change_cash_3_yrs']

# add columns for 3 year sources and uses of cash
<ticker>Q['<field>_3_yrs>'] = <ticker>Q.<field>.rolling(12).sum()


df.reset_index(inplace=True)

df.rename(columns={df.columns[0]:'field'}, inplace=True)

df.drop(df.columns[1], axis=1, inplace=True)

df.loc[0, 'field'] = 'period'

df.drop([rownum], inplace=True)

# Create a multi-index for things like 'Income Statement - As Reported'? #

# set column names to first row
df.columns = df.iloc[0]

df.set_index('period', inplace=True)

df.filter(like='MRFP').columns

class TickerData():
    fye = datetime  #fiscal year end
    mrfp = ''   #most recent fiscal period
    mrfy = ''   #most recent complete fiscal year
    pipe_current = ''   #current pipeline stage
    status_current = '' #pending, active, monitor, excluded

# rolling sums
temp = df['<field>'].rolling(4).sum()

# add column with values conditional on another column
df.['<col_name>'] = np.where(df.index.str.startswith('Q'), 'Q', 'F')

# move column to be additional index (e.g. Q or F)
df.set_index('<col_name>', append=True, inplace=True)

# find column numbers of duplicate column names
cols = pd.Series(df.columns)
cols[cols == '<col_name>'].index.values

# add series (to prepare for second column index)
df = df.append(pd.Series(name='section'))

# drop null columns
df = df.loc[:,df.columns.notnull()]

# find columns containing name
df.filter(like='<text>', axis=1)


