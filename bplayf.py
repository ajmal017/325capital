#! /usr/bin/env python3
import seaborn as sns
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import re
import bql
import bqviz as bqv
bq = bql.Service()

# Set up some convenience settings
pd.set_option('display.max_rows', 200)
pd.set_option('display.max_seq_items', 200)

# Read the main database into d
kwargs = {'io': '325Universe.xlsx',
 'sheet_name': 'Sheet1',
 'na_filter': True}

d = pd.read_excel(**kwargs)
d = d.set_index('ticker')

reasonable_eps = (d.ep_total_to_market_cap >= 1.5) & (d.ep_total_to_market_cap <= 15)
high_roic_potential = d.roic_high_5 > d.roic_high_5.quantile(q = 0.75)
high_roic_today = d.roic_ltm > d.roic_ltm.quantile(q = .75)
target_industries = (~d.sector.isin(['Retailing', 'Pharmaceuticals & Biotechnology', 'Travel & Leisure'])) & (~d.business.isin(['Retailing', 'Pharmaceuticals & Biotechnology', 'Travel & Leisure']))
ep_display = ['ep_market_cap', 'ep_value_from_fcfe', 'ep_value_from_ebitda', 'ep_value_from_roic', 'ep_total_est_value', 'ep_total_to_market_cap']
display = ['name', 'sector', 'business', 'last_work','revenue_ltm', 'em_ltm', 'ev_to_ebitda_ltm', 'net_debt_to_ebitda_ltm', 'roic_ltm','roic_high_5','ep_total_to_market_cap']
pd.set_option('max_colwidth', 25)
pd.set_option('precision', 2)
pd.set_option('display.float_format', '{:.2f}'.format)
