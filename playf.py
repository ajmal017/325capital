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

# screen for wanted spaces
b = d[d.short_sector.isin(short_sector_wanted)]
b = b[~b.sector.isin(sector_not_wanted)]

# screeners for 235 actives
actives = b[b.last_work == 'Active']

