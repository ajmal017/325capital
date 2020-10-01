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

down = [-.2, -.07, .08, .035, .035]

short_sectors = ['TMT', 'Financial Services', 'Ag Chem and Materials',
       'Commercial Service', 'Healthcare', 'Retail', 'Industrials',
       'Real Estate', 'Consumer Cyclical', 'Technology', 'Energy',
       'Basic Materials', 'Construction', 'Communication Services',
       'Consumer Product', 'Utilities', 'Consumer Defensive',
       'Industrial']

TMTr = [-.1, .1, .065, .05, .035]
Finr = [-.1, .08, .065, .04, .035]
Agr = [-.15, .05, .035, .035, .035]
ComSvcr = [-.15, .08, .04, .04, .04]
Healthr = [-.08, .06, .05, .05, .035]
Retailr = [-.3, .08, .05, .035, .035]
Indusr = [-.2, -.07, .08, .035, .035]
REr = [-.15, .05, .035, .035, .035]
CCr = [-.15, -.05, .10, .05, .035]
Techr = [-.05, .05, .05, .05, .05]
Enerr = [-.035, .05, .035,.035,.035]
Basicr = [-.15, .05, .035, .035, .035]
Consr = [-.05, .04, .035, .035, .035]
Commr = [-.05, .05, .05, .05, .05]
ConsPr = [-.05, .04, .035, .035, .035]
Utilr = [-.035, .05, .035,.035,.035]
ConsDr = [-.035, .05, .035,.035,.035]

rss = [ TMTr , Finr , Agr , ComSvcr , Healthr , Retailr , Indusr , REr , CCr , Techr , Enerr , Basicr , Consr , Commr , ConsPr , Utilr , ConsDr ]

rscens = dict(zip(short_sectors, rss))


ep_sector = pd.DataFrame()
for i in d.index:
    print('working on ', i)
    try:
        forecast, inputs = get_ep(ticker = i, revenue_scenario = rscens[d.loc[i, 'short_sector']])
        ep_sector.loc[i,'sell_price'] = forecast.T.value_per_share[5]
        ep_sector.loc[i,'ep_irr'] = ((ep_sector.loc[i,'sell_price'] /d.loc[i,'price']) ** ( 1 / 5)) -1
        ep_sector.loc[i,'buy_price_ten_percent'] =ep_sector.loc[i,'sell_price'] / ((1 + inputs.ep_discount[0]) ** 5)
        ep_sector.loc[i,'implied_ebitda_multiple'] = forecast.T.ev[5] / forecast.T.ebitda[5]
        ep_sector.loc[i,'ep_today'] = forecast.T.value_per_share[1]
        print('got ', i)
    except:
        continue
