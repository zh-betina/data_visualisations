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
## custom settings
pd.options.mode.chained_assignment = None
pd.set_option('display.float_format', lambda x: '%.3f' % x)

## Préparation données 2022
data_2022 = cache.get('data_2022')
data_2020 = cache.get('data_2020')

def remove_outliers(data, key):
    z_scores=(data["Valeur fonciere"]-data["Valeur fonciere"].mean())/data["Valeur fonciere"].std()
    data_temp=data[abs(z_scores)<=3]
    z_scores=(data_temp["Surface reelle bati"]-data_temp["Surface reelle bati"].mean())/data_temp["Surface reelle bati"].std()
    data_temp_2=data_temp[abs(z_scores)<=3]
    cache.set(key, data_temp_2, timeout=3600)
    return data_temp_2

if data_2022 is None:
    file_path = os.path.join(settings.BASE_DIR, 'french_real_estate', 'static', 'data', 'valeursfoncieres-2022.txt')
    data_2022 = pd.read_csv(file_path, sep="|", decimal=",")
    
    cache.set("data_2022_raw", data_2022, timeout=3600)

    data_2022["Date mutation"]=pd.to_datetime(data_2022.loc[:,"Date mutation"], format="%d/%m/%Y")
    data_2022.fillna(0, inplace=True)
    data_2022=data_2022[data_2022["Valeur fonciere"] > 10]
    data_2022=data_2022[data_2022["Surface reelle bati"] > 10]

    variable2 = pd.to_numeric(data_2022['Valeur fonciere'], errors='coerce')
    variable1 = pd.to_numeric(data_2022['Surface reelle bati'], errors='coerce')
    data_2022['Prix moyen au m2'] = variable2 / variable1

    cache.set('data_2022', data_2022, timeout=3600)

if data_2020 is None:
    file_path = os.path.join(settings.BASE_DIR, 'french_real_estate', 'static', 'data', 'valeursfoncieres-2020.txt')
    data_2020 = pd.read_csv(file_path, sep="|", decimal=",")

    data_2020["Date mutation"]=pd.to_datetime(data_2020.loc[:,"Date mutation"], format="%d/%m/%Y")
    data_2020.fillna(0, inplace=True)
    data_2020=data_2020[data_2020["Valeur fonciere"] > 10]
    data_2020=data_2020[data_2020["Surface reelle bati"] > 10]
    data_2020=remove_outliers(data_2020, 'data_2020')

    cache.set('data_2020', data_2020, timeout=3600)


## Scatter plot pour outliers 2022
def plot_outliers():
    outliers=data_2022.loc[:, ['Valeur fonciere', 'Surface reelle bati']]
    plt.figure(figsize=(10, 12))
    fig = px.scatter(outliers, 
                     x="Valeur fonciere", 
                     y="Surface reelle bati", 
                     color="Valeur fonciere", 
                     hover_data=['Surface reelle bati']
                     )
    fig.update_layout(
        plot_bgcolor='rgba(0, 0, 0, 0)',
        paper_bgcolor='rgba(255, 255, 255, 0.7)'
    )

    img_bytes = fig.to_image(format="png")
    img_base64 = base64.b64encode(img_bytes).decode('utf-8')

    return {'img': img_base64,
            'alt': 'Scatter plot - outliers', 
            'title': 'Qualité de données',
            'descr': "Les outliers, alors les valeurs extremes pour les données foncières 2022"
            }

## Scatter plot without outliers
def plot_no_outliers():
    no_outliers=remove_outliers(data_2022, 'data_2022').loc[:, ['Valeur fonciere', 'Surface reelle bati']]
    plt.figure(figsize=(10, 12))
    fig = px.scatter(no_outliers, 
                     x="Valeur fonciere", 
                     y="Surface reelle bati", 
                     color="Valeur fonciere",
                     hover_data=['Surface reelle bati'])
    fig.update_layout(
        plot_bgcolor='rgba(0, 0, 0, 0)',
        paper_bgcolor='rgba(255, 255, 255, 0.7)'
    )

    img_bytes = fig.to_image(format="png")
    img_base64 = base64.b64encode(img_bytes).decode('utf-8')

    return {'img': img_base64,
            'alt': 'Scatter plot - no outliers', 
            'title': 'Qualité de données',
            'descr': "Après la suppression des outliers avec la méthode z-score"
            }

## Réponse au GET
def visualisations(request):
    context={'items': 
               [plot_outliers(), plot_no_outliers()],
               'title': 'Qualité des données'
            }
    return render(request, 'visualisations/index.html', context)

