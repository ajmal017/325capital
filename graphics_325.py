# Graphics_325.py
# This file holds a large list of useful functions used in 325 capital
# Plotting.  Originally in screen1.py, these function provide for 2X2, line, bar,
# And other graphics using matplotlib and seaborn libraries
# This note was written on August 04, 2020

# Get the required packages
from matplotlib.ticker import (PercentFormatter)
import pandas as pd
import numpy as np
import pickle
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
import itertools
import re

# Set up some convenience settings
pd.set_option('display.max_rows', 200)
pd.set_option('display.max_seq_items', 200)

# Set up a personal palette
palette325 = [
    "#2C3E50",
    "#5E832F",
    "#C00000",
    "#E74C3C",
    "#3498DB",
    "#2980B9",
    "#ECF0F1",
    "#FF9800",
    "#F54F29",
    "#000000"]


def category_bar(ax, data_labels, values, title):
    # This function creates bars even when variables are not continuous
    # eg. they are defined as categories in the dataframe

    xlocs = np.arange(len(data_labels))
    g = ax.scatter(xlocs, values)
    ax.set_xticks(xlocs)
    ax.set_xticklabels(data_labels, rotation=0)
    ax.set_title(title)

    return ax


def n_stacked_bar(ax, data_labels, values, title, percent, segment_labels=[]):
    # This is a New stacked bar that puts data labels in the right place
    # And also puts in the segment labels on the last bar

    import math

    # Set up lists to hold the bottom and total labels
    poses = list(np.zeros(len(data_labels)))
    negs = list(np.zeros(len(data_labels)))
    totals = list(np.zeros(len(data_labels)))

    # Work through each series in values and graph them
    for i, series in enumerate(values):

        # For each count and value (v) in series check if nan or Inf and replace with 0
        for k, v in enumerate(series):
            if math.isnan(v):
                series[k] = 0
            if math.isinf(v):
                series[k] = 0

        # Update bottoms to be right for each data_value
        bottoms = [poses[i] if series[i] >= 0 else negs[i]
                   for i, v in enumerate(series)]

        # Get x locations for each bar and graph it
        xlocs = np.arange(len(data_labels))
        g = ax.bar(xlocs, series, bottom=bottoms, align='center')

        h = 0
        w = 0

        # Add the value label for each bar
        for j, rect in enumerate(g):
            h = rect.get_height()
            w = rect.get_width()

            # Fix labels if they are in percent form according to flag percent in arguments
            if percent:
                value_label = "{:4.1f}%".format(series[j] * 100)
            else:
                value_label = "{:4,.1f}".format(series[j])

            # Put in the label
            ax.annotate(
                value_label,
                xy=(rect.get_x() + w / 2, bottoms[j] + h / 2),
                ha='center',
            )

        # put in the segment label
        ax.annotate(
            segment_labels[i],
            xy=(xlocs[-1] + w / 2, bottoms[-1] + h/2),
        )

        # update the poses and negs
        poses = [bottoms[i] + series[i] if series[i] >= 0 else poses[i]
                 for i, v in enumerate(series)]
        negs = [bottoms[i] + series[i] if series[i] < 0 else negs[i]
                for i, v in enumerate(series)]
        totals = [totals[i] + series[i] for i, v in enumerate(series)]

    # Calculate the top and bottom of the axes based on the totals
    high = max(max(poses), 0) * 1.25
    low = min(0, min(negs), -high/5) * 1.25

    # Put in the total labels
    # offset is just some space to put the label in the right place
    offset = abs(high - low) / 20
    for i in range(len(data_labels)):
        if totals[i] < 0:
            offset = -abs(offset)
        else:
            offset = abs(offset)

        if totals[i] < poses[i]:
            # get the middle of the first bar
            spaceloc = 1/len(xlocs) / 2
            offset = spaceloc * 0.8
            ax.axhline(totals[i], xmin=(xlocs[i] + 1)*spaceloc - offset,
                       xmax=(xlocs[i] + 1) * spaceloc + offset, linestyle=':')

        if percent:
            total_label = "{:3.1f}%".format(totals[i])
        else:
            total_label = "{:3.1f}".format(totals[i])
        ax.annotate(
            total_label,
            xy=(i, totals[i] + offset),
            ha='center',
            va='top',
            color='black'
        )

    # Set x bar locations (e.g. a simple count) and put in the x-labels
    ax.set_xticks(xlocs)
    ax.set_xticklabels(data_labels, rotation=0)

    # Set the y limits according to high and low
    ax.set_ylim(bottom=low, top=high)

    # Adjust y axis format if in perecents based on percent flag in arguments
    if percent:
        ax.yaxis.set_major_formatter(
            PercentFormatter(xmax=1, decimals=0, symbol="%"))
    ax.set_title(title)

    return ax


def compare_series_bar(ax, data_labels, value_list, title, percent):
    # This creates a plot of side by side bars with different colors and
    # labels the tops

    xlocs = np.arange(len(data_labels))
    number_of_series = len(value_list)
    width = 0.45 / number_of_series
    high = max(max(max(value_list)), percent*0.25) * 1.35
    low = min(0, min(min(value_list)) * 2, -high/5)

    for j, values in enumerate(value_list):
        for i, v in enumerate(values):
            if(not isinstance(v, float)) & (not isinstance(v, int)):
                values[i] = 0

        x_locations = xlocs + (j * width)
        g = ax.bar(x_locations, values, width=0.45, align='center')

        for i, rect in enumerate(g):
            height = rect.get_height()
            width = rect.get_width()
            label_fix = abs(high-low)/50
            if values[i] < 0:
                label_fix = -label_fix
            if percent:
                value_label = "{:4.1f}%".format(values[i] * 100)
            else:
                value_label = "{:4,.1f}".format(values[i])

            ax.annotate(
                value_label,
                xy=(rect.get_x() + width / 2, height + label_fix),
                ha='center'
            )

    ax.set_xticks(xlocs + width / number_of_series)
    ax.set_xticklabels(data_labels, rotation=0, size='smaller')
    # Not sure I need this here so commenting it out
    # ax.set_ylim(bottom = low, top = high)
    if percent:
        ax.yaxis.set_major_formatter(
            PercentFormatter(xmax=1, decimals=0, symbol="%"))
    ax.set_title(title)

    return ax


def series_bar(ax, data_labels, values, title, percent):
    # This function plots a simple series with the labels on each bar

    for i, v in enumerate(values):
        if (not isinstance(v, float)):
            values[i] = 0

    high = max(max(values), percent*0.25) * 1.35
    low = min(0, min(values) * 2, -high/5)

    xlocs = np.arange(len(data_labels))
    g = ax.bar(xlocs, values, width=0.45, align='center')

    for i, rect in enumerate(g):
        height = rect.get_height()
        width = rect.get_width()
        label_fix = abs(high-low) / 50

        if values[i] < 0:
            label_fix = -label_fix
        if percent:
            value_label = "{:4.1f}%".format(values[i] * 100)
        else:
            value_label = "{:4,.1f}".format(values[i])

        ax.annotate(
            value_label,
            xy=(rect.get_x() + width / 2, height + label_fix),
            ha='center'
        )
    ax.set_xticks(xlocs)
    ax.set_xticklabels(data_labels, rotation=0, size='smaller')
    # Not sure I need this here so commenting it out
    # ax.set_ylim(bottom = low, top = high)
    if percent:
        ax.yaxis.set_major_formatter(
            PercentFormatter(xmax=1, decimals=0, symbol="%"))
    ax.set_title(title)

    return ax


def series_line(*, ax, data_label, values, title, percent):
    # This function creates a line graph with the values
    # plotted along each line

    for i, v in enumerate(values):
        if (not isinstance(v, float)):
            values[i] = 0

    high = max(max(values), percent*0.25) * 1.35
    low = min(0, min(values) * 2, -high/5)

    g = ax.plot(values)
    xlocs = ax.get_xticks()

    for i, x in enumerate(xlocs):

        label_fix = abs(high-low) / 30
        if v < 0:
            label_fix = -label_fix

        if percent:
            value_label = "{:4.1f}%".format(values[i] * 100)
        else:
            value_label = "{:4,.1f}".format(values[i])

        ax.annotate(
            value_label,
            xy=(x, values[i] + label_fix),
            ha='center',
            fontsize='x-small',
        )

    # set the line label
    ax.annotate(
        s=data_label,
        xy=(xlocs[-1], values[-1]),
        fontsize='small',
    )

    if percent:
        ax.yaxis.set_major_formatter(
            PercentFormatter(xmax=1, decimals=0, symbol="%"))
    ax.set_title(title)

    return ax


def stacked_bar(ax, x, data_labels, values, title):
    # This is the old stacked bar without segment values
    # written into the last bar

    import math

    for i, v in enumerate(values):
        if math.isnan(v):
            values[i] = 0

    high = max(sum(values), max(values)) * 1.25
    low = min(0, min(values)) * 1.25

    for i, value in enumerate(values):

        if i == 0:
            bottom = 0
        else:
            if values[i-1] < 0:
                bottom = 0
            else:
                bottom = values[i-1]

        ax.bar(
            x=x,
            height=value,
            bottom=bottom,
            width=0.4,
            align='center'
        )
        ax.annotate(
            "{}\n {:4.1f}X".format(data_labels[i], value),
            xy=(x, bottom + (value / 2)),
            ha='center',
            color='white'
        )

    ax.annotate(
        "{}\n {:4.1f}X".format("Valuation:", sum(values)),
        xy=(x, high / 1.2),
        ha='center',
        color='black'
    )

    ax.set_xticks([x])
    ax.set_xticklabels(title)
    ax.set_ylim(bottom=low, top=high)
    ax.set_title(title)

    return ax


def scat(df, x, y, h, al):
    # this function creates a simple scatter plot
    # with a hue and puts labels on each dot

    import itertools

    # set up plot space
    fig = plt.figure()
    ax = plt.axes()

    # select the data given the limts we wanted
    #xmask = (df[x] > al[0]) & (df[x] < al[1])
    #dftemp = df[xmask]

    #ymask = (dftemp[y] > al[2]) & (dftemp[y] < al[3])
    #dftemp = dftemp[ymask]
    dftemp = df

    plt.xlim(al[0], al[1])
    plt.ylim(al[2], al[3])

    huepalette = dict(zip(set(dftemp[h]), itertools.cycle(palette325)))

    chart = sns.scatterplot(x=x, y=y, data=dftemp, hue=h, palette=huepalette)
    chart.set_ylabel(y, rotation='horizontal', position=(0, 1.05))
    chart.set_xticks(np.linspace(al[0], al[1], 5))
    chart.set_yticks(np.linspace(al[2], al[3], 5))

    for i in range(0, dftemp.shape[0]):
        chart.annotate(
            xy=(dftemp[x][i]*1.05, dftemp[y][i]-0.02), s=dftemp.index[i])

    return ax


def bubb(df, x, y, h, al):
    # This function creates a bubble size with h and also
    # puts labels on each bubble. But will take continous data
    # and graph each one without a range. to get a bucketed range,
    # use contscat

    # set up plot space
    fig = plt.figure()
    ax = plt.axes()

    # select the data given the limts we wanted
    # xmask = (df[x] > al[0]) & (df[x] < al[1])
    # dftemp = df[xmask]

    # ymask = (dftemp[y] > al[2]) & (dftemp[y] < al[3])
    # dftemp = dftemp[ymask]

    chart = sns.scatterplot(ax=ax, x=x, y=y, data=df, size=h, hue=h)
    chart.set_ylabel(y, rotation='horizontal', position=(0, 1.05))
    chart.set_xticks(np.linspace(al[0], al[1], 5))
    chart.set_yticks(np.linspace(al[2], al[3], 4))

    for i in range(0, df.shape[0]):
        chart.annotate(
            s=df.index[i],
            xy=(df[x][i]*1.05, df[y][i]-0.02),
            horizontalalignment='left',
            fontsize=5,
            color='grey',
            weight='light'
        )

    plt.xlim(al[0], al[1])
    plt.ylim(al[2], al[3])

    return ax


def contbubb(df, x, y, h, al):
    # This function is like a bubble chart but takes continuous
    # data for h and makes buckets out of it for easier
    # viewing rather than an individual color for each inidividual value

    # set up plot space
    fig = plt.figure()
    ax = plt.axes()

    # select the data given the limts we wanted
    xmask = (df[x] > al[0]) & (df[x] < al[1])
    dftemp = df[xmask]

    ymask = (dftemp[y] > al[2]) & (dftemp[y] < al[3])
    dftemp = dftemp[ymask]

    plt.xlim(al[0], al[1])
    plt.ylim(al[2], al[3])

    chart = sns.scatterplot(x=x, y=y, data=dftemp, hue=h)
    chart.set_ylabel(y, rotation='horizontal', position=(0, 1.05))
    chart.set_xticks(np.linspace(al[0], al[1], 5))
    chart.set_yticks(np.linspace(al[2], al[3], 4))

    for i in range(0, dftemp.shape[0]):
        chart.text(
            dftemp[x][i]+.15,
            dftemp[y][i]-0.02,
            dftemp.index[i],
            horizontalalignment='left',
            fontsize=5,
            color='grey',
            weight='light')

    return ax


def twoplots(df, name, x, y, z, t, al, xlabel, ylabel, l):
    # twoplots produces two subplots with dimensions from a dataframe
    # x = x, y = y, z = hue, t = size, xlabel is xaxis, ylabel is y axis
    # l is true or false for include legend or not.

    # tey to run real matplot lib
    fig, (ax1, ax2) = plt.subplots(nrows=1, ncols=2, sharey=True)
    plt.style.use('325')

    # set up the plot
    # plt.figure(figsize=(4,4.8))

    # set the axis limits by creating a smaller dataset
    # xmask = (df[x] > al[0]) & (df[x] < al[1])
    # dftemp = df[xmask]
    #
    # ymask = (dftemp[y] > al[2]) & (dftemp[y] < al[3])
    # dftemp = dftemp[ymask]

    dftemp = df

    ax1.set_xlim(al[0], al[1])
    ax2.set_xlim(al[0], al[1])
    ax1.set_ylim(al[2], al[3])
    ax2.set_ylim(al[2], al[3])

    # plot each marker in a different color
    for experience in dftemp[z].unique():
        scatter1 = ax1.scatter(
            dftemp.loc[dftemp[z] == experience, x],
            dftemp.loc[dftemp[z] == experience, y],
            c=palette325[experience],
            s=dftemp.loc[dftemp[z] == experience, t] * 100)
        if (experience == 2 or experience == 1):
            scatter2 = ax2.scatter(
                dftemp.loc[dftemp[z] == experience, x],
                dftemp.loc[dftemp[z] == experience, y],
                c=palette325[experience],
                s=dftemp.loc[dftemp[z] == experience, t] *
                100)
    # put in labels
    for i in range(0, dftemp.shape[0]):
        # xoffset = 0.20
        xoffset = 0

        ax1.annotate(
            xy=(dftemp[x][i] + xoffset, dftemp[y][i]),
            s=dftemp.index[i],
            horizontalalignment='left', fontsize=5, color='grey', weight='light')

        if (dftemp[z][i] == 1 or dftemp[z][i] == 2):
            ax2.annotate(
                xy=(dftemp[x][i] + xoffset, dftemp[y][i]),
                s=dftemp.index[i],
                horizontalalignment='left', fontsize=5, color='grey',
                weight='light')

    # plot the figures with vertical and horizontal lines
    ax1.axvline(x=3)
    ax2.axvline(x=3)
    ax1.axhline(y=8)
    ax2.axhline(y=8)

    if l == True:
        handles, labels = scatter1.legend_elements(prop="sizes", alpha=0.5)
        legend2 = ax2.legend(
            handles,
            labels,
            loc="upper right",
            title=t)

    ax1.set_xlabel(xlabel, fontweight="light")
    ax2.set_xlabel(ylabel, fontweight="light")
    ax1.set_ylabel(
        "EV to EBITDA (LTM)",
        position=(
            0,
            1.1),
        rotation="horizontal",
        fontweight="light",
        ha="left")
    # ax1.yaxis.set_major_formatter(PercentFormatter(xmax = 1, decimals = 0, symbol = "%"))

    plt.savefig(
        '/mnt/c/Users/anilk/OneDrive/Desktop/{}.png'.format(
            name),
        dpi=600)

    return plt


def industry_facets(df):
    sns.set(style="ticks")
    # Initialize a grid of plots with an Axes for each walk
    grid = sns.FacetGrid(df, col=z, hue=z, palette=palette325,
                         col_wrap=5, height=1.5)

    # Draw a line plot to show the trajectory of each random walk
    grid.map(plt.scatter, x, y, marker="o")

    grid.map(plt.axhline, y=8, ls=":", c=".5")
    grid.map(plt.axvline, x=3, ls=":", c=".5")

    # Adjust the tick positions and labels
    grid.set(xlim=(al[0], al[1]), ylim=(al[2], al[3]))

    # Adjust the arrangement of the plots
    grid.fig.tight_layout(w_pad=1)

    plt.show()


def aplots(df, name, x, y, z, t, al, xlabel, ylabel, l):
    # aplots is an old function to test running graphs. I keep it to
    # remember some formatting that was nice in case I want to use it
    # again.
    # x = x, y = y, z = hue, t = size, xlabel is xaxis, ylabel is y axis
    # l is true or false for include legend or not.

    # tey to run real matplot lib
    fig, ax1 = plt.subplots(nrows=1, ncols=1, sharey=True)
    plt.style.use('325')

    # set up the plot
    # plt.figure(figsize=(4,4.8))

    # set the axis limits by creating a smaller dataset
    # xmask = (df[x] > al[0]) & (df[x] < al[1])
    # dftemp = df[xmask]
    #
    # ymask = (dftemp[y] > al[2]) & (dftemp[y] < al[3])
    # dftemp = dftemp[ymask]

    dftemp = df

    ax1.set_xlim(al[0], al[1])
    ax1.set_ylim(al[2], al[3])

    # plot each marker in a different color
    scatter1 = ax1.scatter(
        dftemp[x],
        dftemp[y],
        c=palette325)

    # put in labels
    for i in range(0, dftemp.shape[0]):
        # xoffset = 0.20
        xoffset = 0

        ax1.annotate(
            xy=(dftemp[x][i] + xoffset, dftemp[y][i]),
            s=dftemp.index[i],
            horizontalalignment='left', fontsize=5, color='grey', weight='light')

    # plot the figures with vertical and horizontal lines
    ax1.axvline(x=3)
    ax1.axhline(y=8)

    if l == True:
        handles, labels = scatter1.legend_elements(prop="sizes", alpha=0.5)
        legend1 = ax1.legend(
            handles,
            labels,
            loc="upper right",
            title=t)

    ax1.set_xlabel(xlabel, fontweight="light")
    ax1.set_ylabel(
        "EV to EBITDA (LTM)",
        position=(
            0,
            1.1),
        rotation="horizontal",
        fontweight="light",
        ha="left")
    # ax1.yaxis.set_major_formatter(PercentFormatter(xmax = 1, decimals = 0, symbol = "%"))

    plt.savefig(
        '/mnt/c/Users/anilk/OneDrive/Desktop/{}.png'.format(
            name),
        dpi=600)

    return plt
