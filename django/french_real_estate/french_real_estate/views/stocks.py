from django.shortcuts import render
from django.conf import settings
import matplotlib
matplotlib.use('agg')

import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import os
from django.core.cache import cache
import base64
from urllib.request import urlopen
import json
import io
import seaborn as sns
import numpy as np

pd.options.mode.chained_assignment = None
pd.set_option('display.float_format', lambda x: '%.3f' % x)

def prepare_for_ohlc():
    file_path = os.path.join(settings.BASE_DIR, 'french_real_estate', 'static', 'data', 'NXI.PA.csv')
    nexity_data=pd.read_csv(file_path, parse_dates=['Date'])
    nexity_data["type"]="nexity"

    file_path = os.path.join(settings.BASE_DIR, 'french_real_estate', 'static', 'data', 'cac40.csv')
    cac40_data=pd.read_csv(file_path, parse_dates=['Date'])
    cac40_data["type"]="cac40"

    stock_market_data=pd.concat([nexity_data, cac40_data])
    to_exclude=["Date", "type"]
    condition=stock_market_data.drop(to_exclude, axis=1).isnull().all(axis=1)
    stock_market_data=stock_market_data[~condition]
    year_2=2020
    stock_market_data.loc[:,"Date"]=pd.to_datetime(stock_market_data.loc[:, "Date"])
    stock_market_2020 = stock_market_data[stock_market_data.loc[:, "Date"].dt.year == year_2]
    stock_market_2020['Month'] = stock_market_2020['Date'].dt.month
    stock_market_2020['Normalized_Open'] = stock_market_2020.groupby('type')['Open'].transform(lambda x: (x - x.min()) / (x.max() - x.min()))
    return stock_market_2020


def nexity_cac40_plot():
    stock_market_2020=prepare_for_ohlc()
    fig = px.line(stock_market_2020, x='Month', y='Normalized_Open', color='type', line_group='type',
              labels={'Open': 'Open Value', 'Month': 'Mois'},
              title='Des valeurs "Open" par mois (2020)',
              template='plotly_dark')

    fig.add_trace(px.line(stock_market_2020[stock_market_2020['type'] == 'nexity'], x='Month', y='Normalized_Open',
                      labels={'Open': 'Normalized Nexity Open Value'}).data[0])
    fig.update_layout(
        height=500,
        width=800
        )
     
    return {'fig': fig.to_html(full_html=False),
            'alt': 'OHLC charts', 
            'title': '',
            'descr': ''
            }


def ohlcplots(request):
    context={'items': 
               [nexity_cac40_plot()],
               'title': f'Condition sur le marché financière - NEXITY vs CAC40 en 2020'
            }
    return render(request, 'visualisations/index.html', context)
