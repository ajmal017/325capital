
#! /usr/bin/env python3
import pandas as pd


# This script stiches the results of build_fscores_excel into a single file and saves
# The resulting file as fscores_new.xlsx.  Then user has to go and save the old one as
# wished and rename fscores_new into fscores
# This note was written on August 10,2020

# Get each sheet that was saved by build_fscores_excel
f1 = pd.read_excel('fscores_1.xlsx')
f2 = pd.read_excel('fscores_2.xlsx')
f3 = pd.read_excel('fscores_3.xlsx')
f4 = pd.read_excel('fscores_4.xlsx')
f5 = pd.read_excel('fscores_5.xlsx')


# stitch them into one dataframe called f
f = pd.concat([f1, f2, f3, f4, f5])

# make sure index is set to symbol
f = f.set_index('symbol')

# save the file as fscores_new.xlsx
f.to_excel('fscores_new.xlsx')
