#! /usr/bin/env python3

# screen_tree.py
# This file is an attempt to produce masks to create a cascade
# of screening decisions in a tree and thus bucket the companies
# in useful screen groups

# First get some imports
import pandas as pd
# Get some easy definitions that we already are using
from playf import TESTS, valuation_tests, sbm_tests, puoc_tests, trade_tests, bs_risks_tests, experience_tests
from playf import short_sector_wanted, short_sector_not_wanted, sector_not_wanted, business_not_wanted
import matplotlib.pyplot as plt
import sys

# Set up some convenience settings
plt.style.use('325.mplstyle')

# Set an output option when looking at output
pd.set_option('display.float_format', lambda x: '%.2f' % x)

# Get the main database from fscores.xlsx
d = pd.read_excel('fscores.xlsx')
d = d.set_index('symbol')

# Add in Michael Braners quick and dirty ep
d['fcf_avg_3'] = d.icf_avg_3 / d.icf_avg_3_to_fcf
d['ep'] = (d['ebitda_ltm']-d['capex_ltm']) * .7
d['ep_market_cap'] = d.ep * d.ep_multiple - d.net_debt_ltm + d.ep * 5
d['base_return'] = (d.ep_market_cap/d.market_cap)**.2-1
d['ic_change_5'] = d.ic - d.ic_ago_5
d['ebiat_change_5'] = (d.ebit - d.ebit_ago_5) * .7
d['return_on_growth'] = d.ebiat_change_5 / d.ic_change_5
d['price_opp_current_ep'] = (d.ep * 10 - d.net_debt_ltm) / d.market_cap
d['price_opp_avg_fcf'] = d.fcf_avg_3 * 5 / d.market_cap
d['price_opp_from_growth'] = d.ic_change_5 * d.roic_high_5 * 10 - d.ic_change_5
d['roic_trend'] = (d.roic - d.roic_ago_5)

roic_test_hurdle = .1

# Add in Michael's masks
roic_up = (d.roic_trend >= 0)
roic_high = (d.roic_avg_5 > roic_test_hurdle) & (
    d.roic_high_5 > roic_test_hurdle)
roic_med = (d.roic_avg_5 <= roic_test_hurdle) & (
    d.roic_high_5 > roic_test_hurdle)
roic_low = (d.roic_high_5 <= roic_test_hurdle)
roic_down = (d.roic_trend < 0)
base10 = (d.base_return >= .1)
high_debt = (d.net_debt_to_ebitda_ltm > 3)
valuation = d.base_return > .2
quality_revenue = d.revenue_growth_3 > 0

# B is the short database that filters out the sectors we care about
b = d[d.short_sector.isin(short_sector_wanted)].copy()
b = b[~b.sector.isin(sector_not_wanted)].copy()
b = b[~b.business.isin(business_not_wanted)]
b = b[b.ev <= 2000]

# Pull the latest live tests to compare companies to
live_tests = {
    # arbitrary
    'ev_to_ebitda_ltm_test': 8,
    # < median
    'pe_to_mid_cycle_ratio_test': (b.pe / b.pe_mid_cycle).quantile(q=0.5),
    # < median
    'price_change_52_test': b.price_change_52.quantile(q=0.5),
    # < median
    'price_change_last_Q_test': b.price_change_last_Q.quantile(q=0.5),

    # > top_quartile
    'roic_high_5_test': b.roic_high_5.quantile(q=.75),
    # > median
    'gm_ltm_test': b.gm_ltm.quantile(q=0.5),
    # > median
    'dividend_growth_3_test': b.dividend_growth_3.quantile(q=0.5),
    # > top_quartile
    'ebitda_margin_ltm_test': b.ebitda_margin_ltm.quantile(q=.75),
    # < median
    'sgam_ltm_test': b.sgam_ltm.quantile(q=0.5),
    # > median
    'revenue_growth_3_test': b.revenue_growth_3.quantile(q=0.5),
    # > 14% arbitray
    'revenue_growth_max_test': .14,
    # based on Sagard research yes or no
    'market_leader_test': 1,

    # > median
    'capex_to_revenue_avg_3_test': b.capex_to_revenue_avg_3.quantile(q=0.5),
    # < 0 (meaning none of the roic change related to ic)
    'roic_change_from_ic_test': 0,
    # > top_quartile
    'surplus_cash_as_percent_of_price_test': b.surplus_cash_as_percent_of_price.quantile(q=.75),
    # > 0
    'additional_debt_from_ebitda_multiple_per_share_test': 0,
    # > 1
    'icf_avg_3_to_fcf_test': 1,
    # > top_quartile
    'icf_to_ocf_test': (b.icf_ltm / b.ocf_ltm).quantile(q=.75),
    # > top_quartile
    'equity_sold_test': b.equity_sold.quantile(q=.75),
    # > median
    'financing_acquired_test': b.financing_acquired.quantile(q=0.5),
    # > median
    'capex_to_ocf_test': b.capex_to_ocf.quantile(q=0.5),

    # greater than original Sagard test. current June 2020 median is 1.975
    'net_debt_to_ebitda_ltm_test': 3,
    # > median
    'ebitda_to_interest_coverage_test': b.ebitda_to_interest_coverage.quantile(q=0.5),

    # > median
    'short_interest_ratio_test': b.short_interest_ratio.quantile(q=0.5),
    # > top_quartile
    'insider_ownership_total_test': b.insider_ownership_total.quantile(q=.75),
    # > top_quartile
    'insiders_can_get_out_quickly_test': (b.insider_ownership_total / b.adv_as_percent_so).quantile(q=.75),
    # < median
    'adv_avg_months_3_test': b.adv_avg_months_3.quantile(q=0.5),
    # < bottom_quartile
    'float_test': b.float.quantile(q=0.25),
    # > median
    'insiders_selling_ltm_test': b.insiders_selling_ltm.quantile(q=0.5),

    # > 30% price opportunity
    'price_opp_at_em_high_test': 1.3,
    # > 20% price opportunity
    'price_opp_at_sgam_low_test': 1.2,
    # > 20% price opportunity
    'price_opp_at_roic_high_test': 1.2,
}

# Some masks to pull priority lists out of the main database
# Quality of Business - High/med/low
tax_rate = .3

# Michael's tree
good_roic = (b.roic >= roic_test_hurdle)
stable_GM = (b.gm_ltm / b.gm_high_5 >= .9)
stable_EM = (b.ebitda_margin_ltm / b.ebitda_margin_high_5 >= .9)
stable_revenue = (b.revenue_growth_3 > -b.revenue_growth_3.quantile(q=.1))
high_quality = good_roic & stable_GM & stable_EM & stable_revenue
entry_ep = (b.ep_irr_sector >= .1)
core_ep = (b.ep_irr_sector >= .2)
revenue_investments_working = (b.revenue_growth_3 == b.revenue_growth_max)
generates_enough_cash = (b.surplus_cash_as_percent_of_price > .05) | (
    b.ocf_ltm / b.capex_ltm > 2)
can_borrow_enough = (b.net_debt_to_ebitda_ltm < 3)
ic_increasing = (b.ic > b.ic_ago_5)
ic_decreasing = (b.ic < b.ic_ago_5)
sbm = (b.SBM_test >= b.SBM_test.quantile(q=.75))
valuation = (b.VALUATION_test >= b.VALUATION_test.quantile(q=.75))
trade = (b.TRADE_test >= b.TRADE_test.quantile(q=.75))
bsrisks = (b.BS_risks_test >= b.BS_risks_test.quantile(q=.75))
market_leader = b.market_leader_test


# For those that failed roic quality test is it that they have an opportunity
# to get back to past glory?
could_be_good_roic = (b.roic_high_5 >= roic_test_hurdle)

# Was it that they failed on using too much ic or failed to produce r
too_much_ic = (abs(b.roic_change_from_ic) > abs(b.roic_change_from_r))

# Next distinguish between growth companies above average and margin improvement companies
growers = (b.revenue_growth_3 > b.revenue_growth_3.quantile(q=.75))

# Next on performance opportunity focus on ebitda and sga for now
fixers = (b.ebitda_margin_ltm < b.ebitda_margin_high_5)

# Do we have knowledge of the company or not?
knowledge = (b.tamale_status.isin(
    ['Active', 'Monitor', 'Montior', 'Pending', 'Invested']))

show = ['name', 'roic', 'revenue_ltm', 'revenue_growth_3', 'ebitda_ltm', 'ev_to_ebitda_ltm',
        'tamale_status', 'price_opp_at_em_high', 'price', 'base_return', 'business']


# create some short-cut masks to correspond to the mekko big buckets
# rh  roic high,  rr = roic rising rl = roic low rf = roic falling
rhrr = (roic_high & ~roic_down)
rhrf = (roic_high & roic_down)
rlrr = (~roic_high & ~roic_down)
rlrf = (~roic_high & roic_down)
wasrh = (b.roic_high_5 >= roic_test_hurdle)

I = b[rlrr & wasrh & too_much_ic]
J = b[rlrr & wasrh & ~too_much_ic]
K = b[rlrf & wasrh & too_much_ic]
L = b[rlrf & wasrh & ~too_much_ic]

actives = b[b.last_work == 'Active']
