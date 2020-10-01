# Screen tree attempt

## Is the company top quartile ROIC? 
(d.roic > d.roic.quantile(q = .75))

    Yes: 
        ### Is it on track to remain so? 
        (d.revenue_growth_3 >= d.revenue_growth_3.quantile(q = .5))
        (d.base_return >= .1)
        (d.ebitda_margin_ltm > 0.9 * d.ebitda_margin_high_5)
        (d.net_debt_to_ebitda_ltm < 3)
        (d.ocf_ltm > d.capex_ltm)
            Yes: 
                ### Can we invest at a reasonable return/valuation
                (d.base_return >= .2)
                (d.ev_to_ebitda_ltm < 8)
                (d.price_change_52 <= d.price_change_52.quantile(q = .5)
                (d.market_leader > 0)
                Yes: = high priority
                No: = monitor
            No: 
                ### Can we intervene and fix trajectory? 
                (d.price_opportunity_at_em_high > 1.3)
                (d.roic_change_from_r < 0)
                (d.market_leader > 0)
                Yes: = engage management
                No: = montior 
    No: 
        ### Does it have potential to be top quartile? 
        #### Did it once have high ROIC? 
        (d.roic_high_5 >= d.roic.quantile(q = .75)) 
        Yes:
            ### Are the reasons for low ROIC now fixable? (e.g. not IC related only)? 
            (d.price_opp_at_roic_high > 1.3)
            (d.roic_change_from_ic >= 0)
            (d.price_opportunity_at_em_high > 1.3)
            Yes: = engage management
            No: = pass
        No:
            = pass

## Is the company a leader
