#! /usr/bin/env python3
from screen1 import *
import seaborn as sns
import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import re
import itertools

# Set up some convenience settings
pd.set_option('display.max_rows', 200)
pd.set_option('display.max_seq_items', 200)

# s right now is trying to create an x-y of an
# industry for the 325 score sheet

# Get the data. I have no idea how recently with325 was created. it is old.
filenames = ["with325.xlsx"]
sheets = {"Sheet1": [0, "A:CR", 2179]}
df1 = getasheet(filenames, sheets, 'ticker')

# key masks to graph
industries = ['IT']
include_mask = df1['include?'] == 1
pipeline_mask = df1['325'] > 0
industry_mask = df1['short_industry'].isin(industries)
df2 = df1[include_mask & pipeline_mask & industry_mask]

x = 'net_debt_to_ebitda_ltm'
y = 'ev_to_ebitda_ltm'
z = 'short_industry'
t = 'revenue_growth_yoy'
al = (-5, 8, 0, 15)
name = 'test'
xlabel = 'Net Debt to EBITDA (LTM)'
ylabel = 'EV to EBITDA (LTM)'
l = True

plt.style.use('325.mplstyle')

fig, ax1 = plt.subplots()

huepalette = dict(zip(set(df2[z]), itertools.cycle(palette325)))

ax1.set_title(industries)
ax1.set_xlim(al[0],al[1])
ax1.set_ylim(al[2],al[3])
ax1.axhline(y = 8)
ax1.axvline(x = 3)

for i in df2['325'].unique():
    g =ax1.scatter(x = df2[x], y = df2[y], c = df2[z].map(huepalette), s = df2[t] * 100)

for i in range(0,df2.shape[0]):
    ax1.annotate(s  = df2.index[i], xy = (df2[x][i]+.1, df2[y][i]),
            fontsize=5,
            color='grey',
            weight='light')

if l == True:
    handles, labels =g.legend_elements(prop="sizes", alpha=0.5)
    ax1.legend( handles, labels, loc="upper right", title=t)

plt.savefig("/mnt/c/Users/anilk/OneDrive/Desktop/{}.png".format("industry"), dpi = 600)
