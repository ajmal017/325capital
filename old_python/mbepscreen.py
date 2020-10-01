import pandas as pd

pd.set_option('display.max_rows', None)
pd.set_option('display.max_seq_items', None)

curruniv = pd.read_csv('mbtemp.csv', index_col = 'symbol')

irexclude=pd.read_csv('irexclude.csv')
irlist = curruniv[~curruniv.business.isin(irexclude.business)].copy()

irlist['fcf_avg_3'] = irlist.icf_avg_3 / irlist.icf_avg_3_to_fcf

irlist['EP']=(irlist['ebitda_ltm']-irlist['capex_ltm']) * .7
irlist['EstMktCap']=irlist.EP * irlist.ep_multiple - irlist.net_debt_ltm + irlist.EP * 5
irlist['BaseReturn']=(irlist.EstMktCap/irlist.market_cap)**.2-1
irlist['ic_change_5'] = irlist.ic - irlist.ic_ago_5
irlist['ebiat_change_5'] = (irlist.ebit - irlist.ebit_ago_5) * .7
irlist['return_on_growth'] = irlist.ebiat_change_5 / irlist.ic_change_5


irlist['price_opp_current_ep'] = (irlist.EP * 10 - irlist.net_debt_ltm) / irlist.market_cap
irlist['price_opp_avg_fcf'] = irlist.EP * 5 / irlist.market_cap
irlist['price_opp_from_growth'] = irlist.ic_change_5 * irlist.roic_high_5 * 10 - irlist.ic_change_5 

roic_high = (irlist.roic_avg_5 > .08) & (irlist.roic_high_5 > .08)
roic_med = (irlist.roic_avg_5 <= .08) & (irlist.roic_high_5 > .08)
roic_low = (irlist.roic_high_5 <= .08)

irlist['roic_trend'] = (irlist.roic - irlist.roic_ago_5)
roic_up = (irlist.roic_trend >= 0)
roic_down = (irlist.roic_trend < 0)

base10 = (irlist.BaseReturn >= .1)
base0 = (irlist.BaseReturn < .1) & (irlist.BaseReturn >= 0r)

high_debt = (irlist.net_debt_to_ebitda_ltm > 3)

valuation = irlist.BaseReturn > .2
quality_revenue = irlist.revenue_growth_3 > 0

display = ['name', 'business', 'roic_high_5', 'roic_avg_5', 'roic', 'roic_ago_5', 'roic_trend', 'BaseReturn', 'net_debt_to_ebitda_ltm']

# look at price_opp_at_em_high rather than roic_high to account for overpaying to buy assets; would be better to check change in EBIAT / change in IC
display_price_opp = ['name', 'business', 'market_cap', 'net_debt_ltm', 'EP', 'EstMktCap', 'price_opp_current_ep', 'price_opp_avg_fcf', 'ebitda_margin_ltm', 'ebitda_margin_high_5', 'price_opp_at_em_high', 'ic_change_5', 'ebiat_change_5', 'return_on_growth', 'roic', 'roic_high_5', 'price_opp_at_roic_high']

display_ep = ['name', 'business', 'market_cap', 'ebitda_ltm', 'capex_ltm', 'EstMktCap', 'net_debt_ltm', 'EP', 'price_opp_current_ep', 'price_opp_avg_fcf']
