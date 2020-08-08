import pandas as pd

pd.set_option('display.max_rows', None)
pd.set_option('display.max_seq_items', None)

curruniv = pd.read_csv('mbtemp.csv', index_col = 'symbol')

irexclude=pd.read_csv('irexclude.csv')
irlist = curruniv[~curruniv.business.isin(irexclude.business)]

irlist['EP']=(irlist['ebitda_ltm']-irlist['capex_ltm']) * .7
irlist['EstMktCap']=irlist.EP*10-irlist.net_debt_ltm+irlist.ocf_ltm * 5
irlist['BaseReturn']=(irlist.EstMktCap/irlist.market_cap)**.2-1

irlist['price_opp_current_ep'] = (irlist.EP * 10 - irlist.net_debt_ltm) / irlist.market_cap
irlist['price_opp_current_ocf'] = irlist.ocf_ltm * 5 / irlist.market_cap

roic_high = (irlist.roic_avg_5 > .08) & (irlist.roic_high_5 > .08)
roic_med = (irlist.roic_avg_5 <= .08) & (irlist.roic_high_5 > .08)
roic_low = (irlist.roic_high_5 <= .08)

irlist['roic_trend'] = (irlist.roic - irlist.roic_ago_5 >=0)
roic_up = (irlist.roic_trend >= 0)
roic_down = (irlist.roic_trend < 0)

base10 = (irlist.BaseReturn >= .1)

high_debt = (irlist.net_debt_to_ebitda_ltm > 3)

valuation = irlist.BaseReturn > .2
quality_revenue = irlist.revenue_growth_3 > 0

display = ['name', 'business', 'roic_high_5', 'roic_avg_5', 'roic', 'roic_ago_5', 'roic_trend', 'BaseReturn', 'net_debt_to_ebitda_ltm']
display_price_opp = ['name', 'business', 'price_opp_current_ep', 'price_opp_current_ocf', 'price_opp_at_em_high', 'price_opp_at_roic_high']
