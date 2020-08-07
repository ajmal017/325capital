import pandas as pd

pd.set_option('display.max_rows', None)
pd.set_option('display.max_seq_items', None)

curruniv = pd.read_csv('mbtemp.csv', index_col = 'symbol')

irexclude=pd.read_csv('irexclude.csv')
irlist = curruniv[~curruniv.business.isin(irexclude.business)]

irlist['EP']=(irlist['ebitda_ltm']-irlist['capex_ltm']) * .7
irlist['EstMktCap']=irlist.EP*10-irlist.net_debt_ltm+irlist.ocf_ltm * 5
irlist['BaseReturn']=(irlist.EstMktCap/irlist.market_cap)**.2-1

roic = irlist.roic_avg_5 > .08
valuation = irlist.BaseReturn > .2
quality_revenue = irlist.revenue_growth_3 > 0
quality_wc = irlist

display = ['name', 'business', 'roic_avg_5', 'BaseReturn']


