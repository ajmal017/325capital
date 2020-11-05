def get_b_score(tickers):
    import pandas as pd
    import numpy as np
    import bql
    import bqviz as bqv

    # Set up the bloomberg service
    bq = bql.Service()

    # Set up the universes I care about
    ttfwatch = bq.univ.members('U30460937-3', type = 'PORT')
    ttfuniverse = bq.univ.members('U30460937-4', type = 'PORT')

    # get the fields one by one
    field_dict = {
        'name' : bq.data.name(),
        'date_of_data' : bq.func.today(),
        'sector' : bq.data.gics_industry_group_name(),
        'business' : bq.data.icb_sector_name(),
        'last_price' : bq.data.px_last(),
        'ev_ltm' : bq.data.curr_entp_val() / 1e6,
        'total_debt' : bq.data.long_term_borrowings_detailed() / 1e6,
        'market_cap' : bq.data.cur_mkt_cap()/ 1e6,
        'ebitda_ltm' : bq.data.ebitda(fa_adjusted = 'Y', fpo = '0')/ 1e6,
        'ebitda_high_5' : bq.func.max(bq.data.ebitda(fa_adjusted = 'Y', fpo = bq.func.range(-5,0)))/ 1e6,
        'ebitda_ntm' : bq.data.ebitda(fa_adjusted = 'Y', fpo = '1')/ 1e6,
        'revenue_ltm' : bq.data.sales_rev_turn(fpo = '0')/ 1e6,
        'revenue_3_ago' : bq.data.sales_rev_turn(fpo = '-3')/ 1e6,
        'revenue_ntm' : bq.data.sales_rev_turn(fpo = '1')/ 1e6,
        'fcfe_ltm' : bq.data.free_cash_flow_equity(fpo = '0') / 1e6,
        'roic_ltm' : bq.data.return_on_inv_capital(fpo = '0') / 1e2 ,
        'roic_high_5' : bq.func.max(bq.data.return_on_inv_capital(fpo = bq.func.range(-5,0))) / 1e2,
        'fcfe_high_5' : (bq.func.max(bq.data.free_cash_flow_equity(fpo = bq.func.range(-5,0))) * (1 - bq.data.is_statutory_tax_rate())) / 1e6,
        'ep_1_ago' : ((bq.data.ebitda(fpo = '-1', fa_adjusted = 'Y') + bq.data.capital_expend(fpo = '-1')) * ( 1 - bq.data.is_statutory_tax_rate())) / 1e6,
        'ep_ltm' : ((bq.data.ebitda(fpo = '0', fa_adjusted = 'Y') + bq.data.capital_expend(fpo = '0')) * ( 1 - bq.data.is_statutory_tax_rate())) / 1e6,
        'cash_ltm' : bq.data.casH_and_marketable_securities(fa_period_type = 'LTM') / 1e6,
        'tax_rate' : bq.func.avg( bq.data.cf_cash_paid_for_tax(fpo = bq.func.range(-5,0)) / bq.data.ebitda(fa_adjusted = 'Y', fpo = bq.func.range(-5,0))) / 1e2,
        'wc_change_3' : (bq.data.non_cash_working_capital(fpo = '0') - bq.data.non_cash_working_capital(fpo = '-2Q'))/1e6,
        'fcfe' :( (bq.data.EBITDA(fa_adjusted = 'Y') - \
                  (bq.func.avg(bq.data.cf_depr_amort(fpo=bq.func.range(-5,0))) / bq.func.avg(bq.data.bs_net_fix_asset(FPO=bq.func.range(-5,0)))) * bq.data.bs_net_fix_asset() \
                  - bq.data.is_net_interest_expense()) \
                * (1 - bq.data.is_statutory_tax_rate()) ) / 1e6,
        'em_ltm' : bq.data.ebitda_margin(fa_adjusted = 'Y') / 1e2,
        'em_high_5' : bq.func.max(bq.data.ebitda_margin(fa_adjusted = 'Y', fpo = bq.func.range(-5,0))) / 1e2,
        'gm_ltm' : bq.data.gross_margin(fa_adjusted = 'Y', fpo = '0') / 1e2,
        'gm_high_5' : bq.func.max(bq.data.gross_margin(fa_adjusted = 'Y', fpo = bq.func.range(-5,0))) / 1e2,
        'sgam_ltm' : bq.data.is_sg_and_a_expense(fa_adjusted = 'Y', fpo = '0') / bq.data.sales_rev_turn(fa_adjusted = 'Y', fpo = '0'),
        'sgam_low_5' : bq.func.min(bq.data.is_sg_and_a_expense(fa_adjusted = 'Y', fpo = bq.func.range(-5,0)) / bq.data.sales_rev_turn(fa_adjusted = 'Y', fpo = bq.func.range(-5,0))),
        'ic_ltm': bq.data.total_invested_capital(fpt = 'LTM') / 1e6,
        'ic_ago_3' : bq.data.total_invested_capital(fpo = '-2',fpt = 'LTM') / 1e6,
        'ceo_tenure' : bq.data.ceo_tenure(),
        'ebit_ltm' : bq.data.ebit(fa_adjusted = 'Y', fpo = '0') / 1e6,
        'ebit_ltm' : bq.data.ebit(fa_adjusted = 'Y', fpo = '0') / 1e6,
        'ni_ltm' : bq.data.net_income(fa_adjusted = 'Y', fpo = '0') / 1e6,
        'da_ltm' : bq.data.cf_depr_amort(fpo = '0') / 1e6,
        'capex_ltm' : bq.data.capital_expend(fpo = '0') / 1e6,
        'ocf_ltm' : bq.data.cf_cash_from_oper(fpo = '0') / 1e6,
        'icf_ltm' : bq.data.cf_cash_from_inv_act(fpo = '0') / 1e6,
        'icf_3_avg' : bq.func.avg(bq.data.cf_cash_from_inv_act(fpo = bq.func.range(-2,0))) / 1e6,
        'short_int_ratio' : bq.data.short_int_ratio(per = 'D') / 1e2,
        'insider_pct' : bq.data.pct_insider_shares_out(per = 'Q') / 1e2,
        'insider_shares_sold_1Q' : bq.data.num_insider_shares_sold(per = 'Q') / 1e6,
        'insider_shares_purch_1Q' : bq.data.num_insider_shares_purch(per = 'Q') / 1e6,
        'adv_3_mo' : bq.data.px_volume(per = 'Q') / 180 / 1e6,
        'so' : bq.data.is_sh_for_diluted_eps(fpt = 'LTM') / 1e6,
        'price_high_52_weeks' : bq.func.max(bq.data.px_last(dates = bq.func.range('-1Y', '0D')))
    }

    # fix the ticker if required
    if not isinstance(tickers, bql.om.bql_item.BqlItem):
        if 'Equity' not in tickers:
            tickers = f'{tickers.upper()} US Equity'

    # make the request
    df = pd.DataFrame()
    for field, dataitem in field_dict.items():
        request = bql.Request(tickers, {field: dataitem})
        response = bq.execute(request)
        df = pd.concat([df, response[0].df()[field]], axis = 'columns', sort  = False)


    df['price_change_52'] = df.last_price / df.price_high_52_weeks - 1
    df['ev_to_ebitda_ltm'] = df.ev_ltm / df.ebitda_ltm
    df['ev_to_ebitda_ntm'] = df.ev_ltm / df.ebitda_ntm
    df['net_debt_ltm'] = df.total_debt - df.cash_ltm
    df['net_debt_to_ebitda_ltm'] = df.net_debt_ltm / df.ebitda_ltm
    df['ep_market_cap_1_ago'] = 10 * df.ep_1_ago * (1 - df.tax_rate)
    df['ep_market_cap'] = 10 * df.ep_ltm * (1 - df.tax_rate)
    df['ep_value_from_fcfe'] = 5 * df.fcfe
    df['ep_value_from_ebitda'] = (df.em_high_5 - df.em_ltm) * 10
    df['ic_change_3'] = df.ic_ltm - df.ic_ago_3
    df['ep_value_from_roic'] = df.roic_high_5 * df.ic_change_3 * 10
    df['ep_total_est_value'] =(
            np.where(df.ep_market_cap > 0, df.ep_market_cap, 0) +
            np.where(df.ep_value_from_fcfe > 0, df.ep_value_from_fcfe, 0) +
            np.where(df.ep_value_from_ebitda > 0, df.ep_value_from_ebitda, 0) +
            np.where(df.ep_value_from_roic > 0, df.ep_value_from_roic, 0)
            )
    df['ep_total_to_market_cap'] = df.ep_total_est_value / df.market_cap
    df['revenue_growth_3'] = (df.revenue_ltm / df.revenue_3_ago) ** (1/3) - 1
    df['revenue_growth_ntm'] = (df.revenue_ntm / df.revenue_ltm) - 1
    df['price_opp_at_em_high'] = (
                           (10 * df.em_high_5 / df.em_ltm
                           * df.ebitda_ltm
                           - df.net_debt_ltm)
                           / df.so
                           / df.last_price
                           )
    df['price_opp_at_sgam_low'] = (
                            (((df.em_ltm + (df.sgam_ltm - df.sgam_low_5))
                            / df.em_ltm
                            * 10
                            * df.ebitda_ltm)
                            - df.net_debt_ltm)
                            / df.so
                            / df.last_price
                            )
    ebitda_at_roic_high = (df.roic_ltm * df.ic_ltm / (1 - df.tax_rate)) + df.da_ltm
    df['price_opp_at_roic_high'] = (
                            (ebitda_at_roic_high / df.ebitda_ltm
                            * 10
                            * df.ebitda_ltm
                            - df.net_debt_ltm)
                            / df.so
                            / df.last_price
                            )
    df['ep_today'] = df.ep_market_cap / df.so
    df['ep_total'] = df.ep_total_est_value / df.so
    df['buy_price_entry'] = df.ep_total / (1 + .10)**5


    df = df.reset_index(0)
    df['ticker'] = df.ID.str.split(' ', expand = True)[0]
    df = df.set_index('ticker')

    return df

