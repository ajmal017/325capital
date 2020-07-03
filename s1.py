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
d = pd.read_excel('fscores.xlsx')
d = d.set_index('symbol')
# Get teh revenues for a series of auto part retailers for 10 years or more
auto_retailers = ['AAP', 'GPC', 'AZO', 'ORLY']
auto_parts = ['MPAA', 'THRM', 'DORM', 'SMP']

# Get their revenues and put into a dataframe
a = pd.DataFrame()
for co in (*auto_retailers, *auto_parts):
    r = fa.income_statement(co, api_key, 'annual').T
    r.revenue = r.revenue / 1e6
    a[co] = r.revenue

a = a.astype(np.float)
a.index = pd.to_datetime(a.index)


