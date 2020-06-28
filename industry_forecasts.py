#! /usr/bin/env python3

# Import required libraries and helper modules
from screen1 import getasheet
import pandas as pd
import os
import matplotlib.pyplot as plt


# Set up some convenience settings
pd.set_option('display.max_rows', 200)
pd.set_option('display.max_seq_items', 200)

# Get the industry sheet and start looking at it
filenames = ["US Comparative Industry__13_05_2020.xlsx"]
sheets = {"Sheet1":[1939,"C:AT", 1685]}
industry = getasheet(filenames, sheets, 'Industry Classification')

sic_pattern = r'^\((.+)\)'
name_pattern = r'\) (.+)$'
industry['sic_code'] = industry.index.str.extract(r'^\((.+)\)', expand = False)
industry['industry_name'] = industry.index.str.extract(r'\) (.+)$', expand = False)
industry.set_index('sic_code', inplace = True)

fig, ax1 = subplots()


