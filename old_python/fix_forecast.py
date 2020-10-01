down = [-.2, -.07, .08, .035, .035]

ep_down = pd.DataFrame()
for i in d.index:
    print('working on ', i)
    try:
        forecast, inputs = get_ep(ticker = i, revenue_scenario = down)
        ep_down.loc[i,'sell_price'] = forecast.T.value_per_share[5]
        ep_down.loc[i,'ep_irr'] = ((ep_down.loc[i,'sell_price'] /d.loc[i,'price']) ** ( 1 / 5)) -1
        ep_down.loc[i,'buy_price_ten_percent'] =ep_down.loc[i,'sell_price'] / ((1 + inputs.ep_discount[0]) ** 5)
        ep_down.loc[i,'implied_ebitda_multiple'] = forecast.T.ev[5] / forecast.T.ebitda[5]
        ep_down.loc[i,'ep_today'] = forecast.T.value_per_share[1]
        print('got ', i)
    except:
        continue



ep_reg = pd.DataFrame()
for i in d.index:
    print('working on ', i)
    try:
        forecast, inputs = get_ep(ticker = i)
        ep_reg.loc[i,'sell_price'] = forecast.T.value_per_share[5]
        ep_reg.loc[i,'ep_irr'] = ((ep_reg.loc[i,'sell_price'] /d.loc[i,'price']) ** ( 1 / 5)) -1
        ep_reg.loc[i,'buy_price_ten_percent'] =ep_reg.loc[i,'sell_price'] / ((1 + inputs.ep_discount[0]) ** 5)
        ep_reg.loc[i,'implied_ebitda_multiple'] = forecast.T.ev[5] / forecast.T.ebitda[5]
        ep_reg.loc[i,'ep_today'] = forecast.T.value_per_share[1]
        print('got ', i)
    except:
        continue

ep_sector = pd.DataFrame()
for i in d.index:
    print('working on ', i)
    try:
        forecast, inputs = get_ep(ticker = i, revenue_scenario = Rscens[d.loc[i, 'short_sector']])
        ep_sector.loc[i,'sell_price'] = forecast.T.value_per_share[5]
        ep_sector.loc[i,'ep_irr'] = ((ep_sector.loc[i,'sell_price'] /d.loc[i,'price']) ** ( 1 / 5)) -1
        ep_sector.loc[i,'buy_price_ten_percent'] =ep_sector.loc[i,'sell_price'] / ((1 + inputs.ep_discount[0]) ** 5)
        ep_sector.loc[i,'implied_ebitda_multiple'] = forecast.T.ev[5] / forecast.T.ebitda[5]
        ep_sector.loc[i,'ep_today'] = forecast.T.value_per_share[1]
        print('got ', i)
    except:
        continue
