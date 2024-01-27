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

pd.options.mode.chained_assignment = None
pd.set_option('display.float_format', lambda x: '%.3f' % x)


file_path = os.path.join(settings.BASE_DIR, 'french_real_estate', 'static', 'data', 'departements.geojson')
with open(file_path, 'r') as file:
    geojson = json.load(file)

geo_df=pd.DataFrame({'Code departement':[], 'labels': []})
geo_df=geo_df.astype({"Code departement": 'str', "labels": 'str'})

for i in range(len(geojson['features'])):
    geojson['features'][i]['id'] = i
    geo_df.loc[i, 'Code departement']=geojson['features'][i]['properties']['code']
    geo_df.loc[i, 'labels']=geojson['features'][i]['properties']['nom']

def prepare_data_for_map(data):
    depart_surface_terrain=data.loc[:, ["Code departement", "Surface terrain"]]
    depart_surface_terrain=depart_surface_terrain.groupby("Code departement")["Surface terrain"].sum().reset_index()
    depart_surface_terrain["Code departement"]=depart_surface_terrain["Code departement"].astype(str).str.zfill(width=2)
    depart_surface_terrain= pd.merge(geo_df, depart_surface_terrain, on='Code departement', how='inner')
    return depart_surface_terrain

def get_top_bottom_3(depart_surface_terrain):
    top3 = depart_surface_terrain.nlargest(3, 'Surface terrain')
    bottom3 = depart_surface_terrain.nsmallest(3, 'Surface terrain').sort_values(by='Surface terrain', ascending=True)
    return top3, bottom3


def plot_map(data, year):
    depart_surface_terrain=prepare_data_for_map(data)
    fig = px.choropleth(depart_surface_terrain, geojson=geojson, color="Surface terrain",
                    locations="Code departement", featureidkey="properties.code",
                    projection="mercator"
                   )
    fig.update_geos(fitbounds="locations", visible=False)

    fig.update_layout(
        margin={"r": 0, "t": 0, "l": 0, "b": 10},
        width=800,
        height=700,
        plot_bgcolor='rgba(0, 0, 0, 0)',
        paper_bgcolor='rgba(255, 255, 255, 0.7)'
    )

    return {'fig': fig.to_html(full_html=False),
            'alt': 'Carte', 
            'title': f'Surface terrain vendu {year}',
            'descr': f'Surface terrain total vendu en {year} en France'
            }

def tree_map(data, year):
    custom_colors=px.colors.sequential.Sunset
    depart_surface_terrain=prepare_data_for_map(data)
    top3 = depart_surface_terrain.nlargest(3, 'Surface terrain')
    bottom3 = depart_surface_terrain.nsmallest(3, 'Surface terrain').sort_values(by='Surface terrain', ascending=True)
    top_bottom=pd.concat([top3, bottom3], axis=0)

    fig=px.treemap(top_bottom, path=['labels'], values='Surface terrain',
                 title=f'''
                 Top 3 et derniers 3 departements<br>surface terrain dans les transactions - {year}
                 ''',
                 color_discrete_sequence=custom_colors,
                 width=700, height=500)

    fig.update_layout(font=dict(size=20),
                      plot_bgcolor='rgba(0, 0, 0, 0)',
                      paper_bgcolor='rgba(255, 255, 255, 0.7)')
    
    return {'fig': fig.to_html(full_html=False),
            'alt': 'Tree map', 
            'title': '',
            'descr': ''
            }

## Réponse au GET /maps
def maps(request):
    context={'items': 
               [plot_map(cache.get('data_2022'), "2022"), plot_map(cache.get('data_2020'), "2020")],
               'title': 'Cartes'
            }
    return render(request, 'visualisations/index.html', context)


## Réponse au GET /compare-years
def compare(request):
    context={'items': 
               [tree_map(cache.get('data_2022'), "2022"), tree_map(cache.get('data_2020'), "2020")],
               'title': f'3 top et 3 derniers departements au niveau de surface vendu en 2022 et 2020'
            }
    return render(request, 'visualisations/index.html', context)