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


# Get the main database from fscores.xlsx
d = pd.read_excel('fscores.xlsx')
d = d.set_index('symbol')

# Add in Michael Braners quick and dirty ep
d['ep'] = d.ebitda_ltm - d.capex_ltm * .7
d['estmktcap'] = d.ep - d.net_debt_ltm+d.ocf_ltm * 5
d['basereturn'] = (d.estmktcap/d.market_cap) ** .2 - 1

# B is the short database that filters out the sectors we care about
b = d[d.short_sector.isin(short_sector_wanted)].copy()
b = b[~b.sector.isin(sector_not_wanted)].copy()
b = b[~b.business.isin(business_not_wanted)]
b = b[b.ev <= 2000]

# Pull the latest live tests to compare companies to
live_tests = {
    # less than June 2020 median is 7.19. High qartile is 12.33, low quartile is -5.31
    'ev_to_ebitda_ltm_test': 8,
    # less than  June 2020 low quartile is .533632, high q is 1.49
    'pe_to_mid_cycle_ratio_test': (b.pe / b.pe_mid_cycle).quantile(q=0.5),
    # less than June 2020 median, low quartile is -.3875, high q is .182
    'price_change_52_test': b.price_change_52.quantile(q=0.5),
    # less than  June 2020 low q, median is .2952, high q is .596285
    'price_change_last_Q_test': b.price_change_last_Q.quantile(q=0.5),

    # greater than June 2020 top quartile
    'roic_high_5_test': b.roic_high_5.quantile(q=.75),
    # greater than  June 2020 top quartile,.555943 median = .345134
    'gm_ltm_test': b.gm_ltm.quantile(q=0.5),
    # greater than June 2020 median Top quartile is 0.011755
    'dividend_growth_3_test': b.dividend_growth_3.quantile(q=0.5),
    # greater than June 2020 Top quartile, median is .0659
    'ebitda_margin_ltm_test': b.ebitda_margin_ltm.quantile(q=.75),
    # greater than  June 2020 median, low quartile = .108991 high q = .439870
    'sgam_ltm_test': b.sgam_ltm.quantile(q=0.5),
    # greater than  June 2020 median. Top quartile = .450341
    'revenue_growth_3_test': b.revenue_growth_3.quantile(q=0.5),
    'revenue_growth_max_test': .14,  # greater than original Sagard test
    # greater than market leader score will be a year if so or 0 if NOT
    'market_leader_test': 1,

    # greater than June 2020 top quartile, median = .028490
    'capex_to_revenue_avg_3_test': b.capex_to_revenue_avg_3.quantile(q=0.5),
    'roic_change_from_ic_test': 0,  # less than
    # greater than June 2020 top quartile is .123063, median is -.113380
    'surplus_cash_as_percent_of_price_test': b.surplus_cash_as_percent_of_price.quantile(q=.75),
    'additional_debt_from_ebitda_multiple_per_share_test': 0,  # greater than
    'icf_avg_3_to_fcf_test': 1,  # greater than
    # greater than  June 2020 high quartile .142, median is -.274591
    'icf_to_ocf_test': (b.icf_ltm / b.ocf_ltm).quantile(q=.75),
    # greater than June 2020 top quartile
    'equity_sold_test': b.equity_sold.quantile(q=.75),
    # greater than June 2020 median
    'financing_acquired_test': b.financing_acquired.quantile(q=0.5),
    # greater than June 2020 median.  High quartile is .396726
    'capex_to_ocf_test': b.capex_to_ocf.quantile(q=0.5),

    # greater than original Sagard test. current June 2020 median is 1.975
    'net_debt_to_ebitda_ltm_test': 3,
    # less than June 2020 median
    'ebitda_to_interest_coverage_test': b.ebitda_to_interest_coverage.quantile(q=0.5),

    # greater than June 2020 top quartile 7.26, median = 3.92
    'short_interest_ratio_test': b.short_interest_ratio.quantile(q=0.5),
    # greater than June 2020 top quartile .182050, median = .0607
    'insider_ownership_total_test': b.insider_ownership_total.quantile(q=.75),
    # greater than June 2020 top quartile
    'insiders_can_get_out_quickly_test': (b.insider_ownership_total / b.adv_as_percent_so).quantile(q=.75),
    # less than June 2020 median
    'adv_avg_months_3_test': b.adv_avg_months_3.quantile(q=0.5),
    # less than June 2020 lowest quartile
    'float_test': b.float.quantile(q=0.25),
    # less than June 2020 median; lowest quartile is 0
    'insiders_selling_ltm_test': b.insiders_selling_ltm.quantile(q=0.5),

    'price_opp_at_em_high_test': 1.3,  # greater than June 2020 median is 0.909
    'price_opp_at_sgam_low_test': 1.2,  # greater than June 2020 median is 0.9837
    # greater than June 2020 median is 1.167, high quartile is 1.5
    'price_opp_at_roic_high_test': 1.2,
}

# Some masks to pull priority lists out of the main database
# First define some simple tree levels:
# All companies:
# High quality  vs. Not Highquality
# - define based on roic_high_5 > top quartile
# - higher than average on sbm_tests
good_roic = (b.roic >= b.roic.quantile(q=.75)) & (
    b.SBM_test >= b.SBM_test.quantile(q=.5))

market_leader = b.market_leader_test

# For those that failed roic quality test is it that they have an opportunity
# to get back to past glory?
could_be_good_roic = (b.roic_high_5 >= b.roic_high_5.quanitle(
    q=.5)) & (b.roic_high_5_test)

# Was it that they failed on using too much ic or failed to produce r
too_much_ic = (b.roic_change_from_ic_test)

# Next distinguish between growth companies above average and margin improvement companies
growers = (b.revenue_growth_3 > b.revenue_growth_3.quantile(q=.5)) & (
    b.revenue_growth_max_test)

# Next on performance opportunity focus on ebitda and sga for now
fixers = (b.price_opp_at_em_high_test > 1) & (
    b.price_opp_at_sgam_low_test > 1)

# Do we have knowledge of the company or not?
knowlege = (b.tamale_status.isin(
    ['Active', 'Monitor', 'Montior', 'Pending', 'Invested']))
