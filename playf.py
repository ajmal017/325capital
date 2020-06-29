#! /usr/bin/env python3
from screen1 import *
import seaborn as sns
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import re
import itertools
import FundamentalAnalysis as fa

# Set up some convenience settings
pd.set_option('display.max_rows', 200)
pd.set_option('display.max_seq_items', 200)

# Get the latst fscores from fscores.xlsx
# This sheet is populated using build_fscores_excel.py
# It also uses Fundamental Analysis toolkit so have the api_key ready
api_key = "c350f6f5a4396d349ee4bbacde3d5999"
filenames = ['fscores.xlsx']
sheets = {'Sheet1':[0, 'A:ED', 1609]}
d = getasheet(filenames, sheets, 'symbol')

# Split out the most wanted sectors
short_sector_wanted = ['TMT',
 'Healthcare',
 'Industrials',
 'Consumer Cyclical',
 'Commercial Service',
 'Technology',
 'Construction',
 'Communication Services',
 'Consumer Product',
 'Utilities',
 'Retail',
 'Consumer Defensive']

short_sector_not_wanted = ['Financial Services',
        'Ag Chem and Materials',
        'Energy',
        'Basic Materials',
        'Real Estate'
        ]

sector_not_wanted = ['Biotechnology',
        'Capital Markets'
        ]

TESTS = ['VALUATION_test', 'SBM_test', 'PUOC_test', 'BS_risks_test', 'TRADE_test']
valuation_tests = [
   'pe_to_mid_cycle_ratio_test',
   'ev_to_ebitda_ltm_test',
   'price_change_52_test'
   ]
sbm_tests = [
    'roic_high_5_test',
    'dividend_growth_3_test',
    'gm_ltm_test',
    'em_margin_ltm_test',
    'sgam_ltm_test',
    'revenue_growth_3_test',
    'revenue_growth_max_test',
    'market_leader_test'
    ]

puoc_tests = [
    'capex_to_revenue_avg_3_test',
    'roic_change_from_ic_test',
    'surplus_cash_as_percent_of_price_test',
    'additional_debt_from_ebitda_multiple_per_share_test',
    'icf_avg_3_to_fcf_test',
    'icf_to_ocf_test',
    'equity_sold_test',
    'financing_acquired_test',
    'capex_to_ocf_test'
    ]
bs_risks_tests = [
    'icf_and_ocf_negative_test',
    'net_debt_to_ebitda_ltm_test',
    'ebitda_to_interest_coverage_test',
    ]
trade_tests = [
    'short_interest_ratio_test',
    'insider_ownership_total_test',
    'insiders_can_get_out_quickly_test',
    'adv_avg_months_3_test',
    'float_test',
    'insiders_selling_ltm_test'
    ]
experience_tests = [
        'short_sector',
        'tamale_status',
        'last_work',
        'sagard_peers'
        ]
# screen for wanted spaces
b = d[d.short_sector.isin(short_sector_wanted)].copy()
b = b[~b.sector.isin(sector_not_wanted)].copy()

# screeners for 235 actives
actives = b[b.last_work == 'Active'].copy()

