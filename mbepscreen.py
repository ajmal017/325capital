run playf

irexclude=pd.read_csv('irexclude.csv')

irlist = b[~b.business.isin(irexclude.business)]


irlist['EP']=(irlist['ebitda_ltm']-irlist['capex_ltm']) * .7
irlist['EstMktCap']=irlist.EPx10-irlist.net_deb_ltm+irlist.ocf_ltm * 5
irlist['BaseReturn']=(irlist.EstMktCap/irlist.market_cap)**.2-1

epreturn = irlist[irlist.BaseReturn > .2]

roic = [epreturn.roic_avg_5 > .1]


