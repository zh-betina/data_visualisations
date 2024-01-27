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

def prepare_transactions_per_month(data):
    month_transactions_nb = data.groupby(["Date mutation", "Voie"]).size().to_frame('Count')
    month_transactions_nb.reset_index(inplace=True)
    nb_trans=month_transactions_nb.groupby(month_transactions_nb['Date mutation'].dt.to_period("M")).size().reset_index(name='Count')
    return nb_trans

def heatmap_seasonality():
    nb_trans_2022=prepare_transactions_per_month(data_2022)
    nb_trans_2020=prepare_transactions_per_month(data_2020)

    nb_trans_2022['Date mutation'] = nb_trans_2022['Date mutation'].astype(str)
    nb_trans_2020['Date mutation'] = nb_trans_2020['Date mutation'].astype(str)

    heatmap_data_2022 = nb_trans_2022.pivot_table(index='Date mutation', values='Count', aggfunc='sum')
    heatmap_data_2020 = nb_trans_2020.pivot_table(index='Date mutation', values='Count', aggfunc='sum')

    fig, axes = plt.subplots(1, 2, figsize=(13, 8))

    sns.heatmap(heatmap_data_2022, cmap='YlGnBu', annot=True, fmt='.0f', cbar_kws={'label': 'Nombre total des transactions'}, ax=axes[0])
    axes[0].set_title('La saisonnalité des achats immobilières en France 2022 (Heatmap)')
    axes[0].set_ylabel('Mois')

    sns.heatmap(heatmap_data_2020, cmap='YlGnBu', annot=True, fmt='.0f', cbar_kws={'label': 'Nombre total des transactions'}, ax=axes[1])
    axes[1].set_title('La saisonnalité des achats immobilières en France 2020 (Heatmap)')
    axes[1].set_ylabel('Mois')

    plt.tight_layout()

    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    plt.close()

    img = base64.b64encode(buffer.read()).decode('utf-8')

    return {'img': img,
            'alt': 'Heatmap',
            'title': '',
            'descr': 'La saisonnalité des achats immobilières en France'
        }

def fill_area_plot():
    nb_trans_2020=prepare_transactions_per_month(data_2022)
    nb_trans_2022=prepare_transactions_per_month(data_2020)

    fig, ax = plt.subplots(figsize=(15, 8))

    plt.fill_between(nb_trans_2020["Date mutation"].dt.strftime('%B'), nb_trans_2020['Count'], label='2020', alpha=0.7, color="darkblue")
    plt.fill_between(nb_trans_2022["Date mutation"].dt.strftime('%B'), nb_trans_2022['Count'], label='2022', alpha=0.2, color="lightblue")

    plt.grid(axis='x', linestyle='--', alpha=1)

    plt.xlabel('Mois')
    plt.ylabel('Nombre de transactions')
    plt.title('Comparaison des tandences pour les transactions immobilières effectuées par mois (2020 et 2022)')

    plt.legend()

    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    plt.close()

    img = base64.b64encode(buffer.read()).decode('utf-8')
    
    return {'img': img,
            'alt': 'Fill area', 
            'title': '',
            'descr': 'Comparaison des tandences pour les transactions immobilières effectuées par mois (2020 et 2022)'
            }

def prepare_type_building_prefer(data):
    immob_type=data.dropna(subset=['Type local'])
    immob_type["Date mutation"] = pd.to_datetime(immob_type["Date mutation"], format='%d/%m/%Y')
    immob_type.set_index("Date mutation", inplace=True)

    count_per_month_type = immob_type.groupby([immob_type.index.month, 'Type local']).size().unstack().reset_index()
    return count_per_month_type

def building_type_barplot():
    count_per_month_type_2020=prepare_type_building_prefer(data_2020)
    count_per_month_type_2022=prepare_type_building_prefer(data_2022)

    plt.figure(figsize=(12, 6))

    bar_width = 0.2
    gap_width = 0.1
    index = np.arange(len(count_per_month_type_2020['Date mutation']))

    # Bars for 2020
    plt.bar(index - (bar_width + gap_width), count_per_month_type_2020['Appartement'], bar_width, color="#8d6b94", label='Appartement (2020)')
    plt.bar(index, count_per_month_type_2020['Maison'], bar_width, color="#114b5f", label='Maison (2020)')

    # Bars for 2022
    plt.bar(index + gap_width, count_per_month_type_2022['Appartement'], bar_width, color="#b185a7", label='Appartement (2022)')
    plt.bar(index + (bar_width + gap_width), count_per_month_type_2022['Maison'], bar_width, color="#73d2de", label='Maison (2022)')

    plt.title('Comparison de preference de type d achat')
    plt.xlabel('Mois')
    plt.ylabel('Nombre')
    plt.legend()
    plt.xticks(index + (bar_width + gap_width) / 2, count_per_month_type_2020['Date mutation'])  # Adjust x-ticks to center bars

    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    plt.close()

    img = base64.b64encode(buffer.read()).decode('utf-8')

    return {'img': img,
            'alt': 'Bar plots',
            'title': '',
            'descr': "Preference de type d'achat entre appartement et maison, en 2022 et 2020 par mois"
        }

def prepare_real_estate_rate():
    file_path = os.path.join(settings.BASE_DIR, 'french_real_estate', 'static', 'data', 'taux.txt')
    with open(file_path, 'r') as file:
        file_content = file.read()

    lines = [line.strip() for line in file_content.split('\n') if line.strip()]
    lines = [el.split(':') for el in lines]

    taux_immo = pd.DataFrame(lines, columns=['Period', 'Avg_rate'])
    taux_immo['Avg_rate'] = pd.to_numeric(taux_immo['Avg_rate'].str.replace('%', '').str.replace(',', '.').str.strip())
    taux_immo['Period'] = pd.to_datetime(taux_immo['Period'].str.strip(), format='%m-%Y')
    return taux_immo

def estate_rate_lineplot():
    taux_immo=prepare_real_estate_rate()
    taux_immo['Year'] = taux_immo['Period'].dt.year
    taux_immo['Month'] = taux_immo['Period'].dt.month

    monthly_avg = taux_immo.groupby(['Year', 'Month'])['Avg_rate'].mean().reset_index()

    fig = px.line(monthly_avg, x='Month', y='Avg_rate', color='Year',
              labels={'Avg_rate': 'Taux', 'Month': 'Mois'},
              title='Taux moyenne à court terme (ESTER) - 2020 vs 2022',
              line_group='Year', render_mode='svg')

    fig.update_layout(xaxis_title='Mois',
                yaxis_title='Taux',
                legend_title='Année',
                plot_bgcolor='rgba(0, 0, 0, 0)',
                paper_bgcolor='rgba(255, 255, 255, 0.7)'
                )
    
    return {'fig': fig.to_html(full_html=False),
            'alt': 'Lineplot - taux immobilier', 
            'title': '',
            'descr': "Le taux à court terme de la zone euro (ESTER) - 2020 vs 2022"
            }


### responses to GET
def linecharts(request):
    context={'items': 
               [
                   fill_area_plot(),
                   estate_rate_lineplot()
                ],
               'title': 'Line charts'
            }
    return render(request, 'visualisations/index.html', context)

def heatmaps(request):
    context={'items': 
               [heatmap_seasonality()],
               'title': 'Heatmaps'
            }
    return render(request, 'visualisations/index.html', context)

def barplots(request):
    context={'items': 
               [building_type_barplot()],
               'title': 'Barplots'
            }
    return render(request, 'visualisations/index.html', context)