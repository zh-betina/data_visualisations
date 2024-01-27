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

data_2022=cache.get("data_2022")
data_2020=cache.get("data_2020")

def prepare_commune_data():
    columns=["Code departement","Code commune", "Commune", "Surface terrain"]
    surface_terrain_commune = data_2022.loc[data_2022["Code departement"] == 14, columns]
    communes = surface_terrain_commune[surface_terrain_commune["Code departement"] == 14].groupby("Code commune")["Commune"].first().reset_index()
    surface_terrain_commune=surface_terrain_commune[surface_terrain_commune["Code departement"] == 14].groupby("Code commune")["Surface terrain"].sum().reset_index()
    surface_terrain_commune = pd.merge(surface_terrain_commune, communes, on='Code commune', how='inner')
    surface_terrain_commune['Surface terrain_ha'] = surface_terrain_commune['Surface terrain'] / 10_000
    top10 = surface_terrain_commune.sort_values(by='Surface terrain_ha', ascending=False)
    return top10

def plot_sunburst_commune():
    top10=prepare_commune_data().head(10)
    fig = px.sunburst(top10, path=['Commune'],
                  values='Surface terrain',
                  title='Sunburst Chart de 10 top communes avec la plus grande surface terrain vendue',
                  color='Surface terrain_ha',
                  hover_data=['Code commune'],
                  color_continuous_scale='Viridis',
                  width=800, height=800)

    fig.update_layout(
        plot_bgcolor='rgba(0, 0, 0, 0)',
        paper_bgcolor='rgba(255, 255, 255, 0.7)'
    )
    
    return {'fig': fig.to_html(full_html=False),
            'alt': 'Carte', 
            'title': '',
            'descr': f'Sunburst Chart de 10 top communes avec la plus grande surface terrain vendue en 2020 dans le 14'
            }


## responses to GET requests
def piecharts(request):
    context={'items': 
               [plot_sunburst_commune()],
               'title': 'Sunburst Chart de 10 top communes avec la plus grande surface terrain vendue dans le 14'
            }
    return render(request, 'visualisations/index.html', context)
