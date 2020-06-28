#! /usr/bin/env python3
# read packages
from screen1 import getasheet,palette325, series_bar, stacked_bar,category_bar, get_historic_prices, get_yahoo_labels, n_stacked_bar
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import datetime as dt

# Set up some convenience settings
pd.set_option('display.max_rows', 200)
pd.set_option('display.max_seq_items', 200)
plt.style.use('325.mplstyle')

# This file calculates the returns of Sagard's track record based
# on the values of invested capital, gains, and tehrefore net gains.
# IT was meant to be used to fill fields in a powerpoitn file for
# presentation in May, 2020 for DUMAC.
# this file is still accurate but requires the right table to be set up in
# the Sagard track record master as noted in teh sheet pull below.
# This file is fine, but not immediately useful and therefore deprecatd.
# This note was written on June 12, 2020

# get the track record cash flows.
filenames = ['../../Returns/Sagard Track Record Master.xlsx']
sheets = {'Cash Flows':[20,'C:AS',106]}
cf = getasheet(filenames, sheets, 'Date in Month')
sheets = {'Mekko Graphics':[642,'C:AS',5]}
names = getasheet(filenames, sheets, 'Ticker')

# Put the status and cash flows together for each ticker
cd = pd.concat([cf, names], axis = 0).T
cd['IRR'] = cd['IRR'].astype(np.float)
cd = cd.infer_objects()

statusdf = cd.groupby('Status').sum().T

# create some masks
cores = cd['Status'] == 'Core'
entries = cd['Status'] == 'Entry'

core_investments = statusdf.loc[statusdf['Core'] <= 0,'Core'].sum()
core_receipts = statusdf.loc[statusdf['Core'] > 0, 'Core'].sum()
entry_investments = statusdf.loc[statusdf['Entry'] <= 0,'Entry'].sum()
entry_receipts = statusdf.loc[statusdf['Entry'] > 0,'Entry'].sum()

fig, axs  = plt.subplots(nrows = 1, ncols = 2)
fig.suptitle("Sagard Investment Returns by Allocation Type")

values = [0.173338979, 0.324151129]
data_labels = ["Cores", "Entries"]
percent = False
series_bar(axs[0], data_labels,values,'IRRs', True)

values = [core_investments + core_receipts, entry_investments + entry_receipts]
series_bar(axs[1], data_labels, values, 'Gains', False)
plt.show()


print('Core investments, receipts, gain, and MoM\n')
print('{:8.2f} {:8.2f} {:8.2f} {:8.2f}'.format(core_investments, core_receipts, core_receipts/core_investments, core_investments + core_receipts))
print('Entry investments, receipts, gain, and MoM\n')
print('{:8.2f} {:8.2f} {:8.2f} {:8.2f}'.format(entry_investments, entry_receipts, entry_receipts/entry_investments, entry_investments + entry_receipts))


print('Cores\n',cd.loc[cores, 'IRR'].describe())
print('Entries\n',cd.loc[entries, 'IRR'].describe())
