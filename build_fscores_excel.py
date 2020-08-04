#! /usr/bin/env python3
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from graphics_325 import getasheet, palette325, series_bar, category_bar
from getdata_325 import get_historic_prices, get_fidelity_sheets
from screen1 import get_fscore
import pandas as pd
import datetime as dt
import sys
import re

# Set up some convenience settings
pd.set_option('display.max_rows', 999)
pd.set_option('display.max_seq_items', 999)
plt.style.use('325.mplstyle')

# This file was written to get all the fscores for all the
# tickers in a fidelity screener run in May 2020.  The fidelity screener
# looked at all names between 100M and 1.5B in north america and us.
# This file has never been run successfully.  It saves an excel record of its
# work in fscores??.xlsx
# This file was called scratchpad1.py and has been renamed to build_fscores_excel.py
# This note was written on June 12, 2020

# Which ticker you want the score for
# Get the fidelity data
filenames = ['../sc1.xls', '../sc2.xls',
             '../sc3.xls', '../sc4.xls', '../sc5.xls']
for filen in filenames:

    f = []
    f.append(filen)

    fidelity = get_fidelity_sheets(f)
    df = get_fscore(fidelity.index)

    filenumber = re.search('\d', filen)[0]
    df.to_excel('fscores_{}.xlsx'.format(filenumber))
