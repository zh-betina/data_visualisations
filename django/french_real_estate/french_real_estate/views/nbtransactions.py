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
import plotly.graph_objects as go

# pd.options.mode.chained_assignment = None
pd.set_option('display.float_format', lambda x: '%.3f' % x)

data_2022=cache.get("data_2022")
data_2020=cache.get("data_2020")
data_2022_filtre = data_2022[(data_2022['Prix moyen au m2'] >= 300) & (data_2022['Prix moyen au m2'] <= 50000) & (data_2022['Type local'] == 'Appartement') & 
                      (data_2022['Surface reelle bati'] > 10) & (data_2022['Nature mutation'] == 'Vente')]
data_2022_filtre.reset_index(drop=True, inplace=True)

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

def prepare_price_m2():
    prix_moyen_par_departement = data_2022_filtre.groupby('Code departement')['Prix moyen au m2'].mean().reset_index()
    return prix_moyen_par_departement

def barplot_price_m2():
    prepare_price_m2().plot(kind='bar', figsize=(18, 10))

    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    plt.close()

    img = base64.b64encode(buffer.read()).decode('utf-8')

    return {'img': img,
            'alt': 'Bar plots',
            'title': '',
            'descr': ""
        }

def prepare_evolution_m2_price():
    df = data_2022_filtre.copy()
    df['Date mutation'] = pd.to_datetime(df['Date mutation'])
    df['Jour de l\'année'] = df['Date mutation'].dt.dayofyear
    nouveau_df = df.groupby('Jour de l\'année')['Prix moyen au m2'].mean().reset_index()
    nouveau_df.columns = ['Jour de l\'année', 'Prix moyen au m2']
    return nouveau_df

def evolution_m2_price_lineplot():
    nouveau_df=prepare_evolution_m2_price()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=nouveau_df['Jour de l\'année'], y=nouveau_df['Prix moyen au m2'],
                         mode='lines+markers', name='Prix moyen au m2'))

    fig.update_layout(title='Évolution du prix moyen du m2 en 2022 en France',
                  xaxis_title='Jour de transaction',
                  yaxis_title='Prix moyen au m2',
                  height=600,  
                  width=1000)
    
    return {'fig': fig.to_html(full_html=False),
            'alt': 'Line chart', 
            'title': '',
            'descr': ''
            }

def terrain_surface_barplot():
    colonne_surface_terrain = 'Surface terrain'
    pourcentage_zero = (data_2022[colonne_surface_terrain] == 0).mean() * 100

    fig, ax = plt.subplots()
    ax.bar(['Surface égale à zéro', 'Autres surfaces'], [pourcentage_zero, 100 - pourcentage_zero])
    ax.set_ylabel('Pourcentage (%)')
    ax.set_title('Pourcentage de terrains avec une surface égale à zéro')

    ax.text(0, pourcentage_zero + 2, f'{pourcentage_zero:.2f}%', ha='center', va='bottom')
    ax.text(1, 100 - pourcentage_zero + 2, f'{100 - pourcentage_zero:.2f}%', ha='center', va='bottom')

    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    plt.close()

    img = base64.b64encode(buffer.read()).decode('utf-8')

    return {'img': img,
            'alt': 'Bar plots',
            'title': '',
            'descr': ""
        }

def principal_rooms_barplot():
    # data_2022=cache.get("data_2022")
    colonne_departement = 'Code departement'
    colonne_nombre_pieces = 'Nombre pieces principales'
    moyenne_pieces_par_departement = data_2022.groupby(colonne_departement)[colonne_nombre_pieces].mean().reset_index()

    plt.figure(figsize=(15, 8))
    sns.barplot(x=colonne_departement, y=colonne_nombre_pieces, data=moyenne_pieces_par_departement, palette="viridis")
    plt.xlabel('Département')
    plt.ylabel('Nombre moyen de pièces')
    plt.title('Nombre moyen de pièces par appartement par département')

    plt.xticks(rotation=45, ha='right')

    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    plt.close()

    img = base64.b64encode(buffer.read()).decode('utf-8')

    return {'img': img,
            'alt': 'Bar plots',
            'title': '',
            'descr': ""
        }

def prepare_local_type():
    data_2022_raw=cache.get("data_2022_raw")
    data_2022_raw['Type local'] = data_2022_raw['Type local'].astype(str)

    type_local_counts = data_2022_raw['Type local'].value_counts(dropna=False, normalize=True).head()
    labels = type_local_counts.index
    colors = ['#ffcc99', '#66b3ff', '#99ff99', '#ff9999', '#fffc52']
    area_proportion = type_local_counts.values * 100

    return labels, colors, area_proportion

def local_type_hbarplot():
    labels, colors, area_proportion=prepare_local_type()
    plt.figure(figsize=(15, 8))
      # Conversion en pourcentage

    plt.barh(labels, area_proportion, color=colors)
    plt.xlabel('Pourcentage')
    plt.title('Répartition de la variable type_local')
    plt.grid(axis='x', linestyle='--', alpha=0.6)

    for index, value in enumerate(area_proportion):
        plt.text(value, index, f'{value:.2f}%', va='center', ha='left', fontsize=10, color='black')

    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    plt.close()

    img = base64.b64encode(buffer.read()).decode('utf-8')

    return {'img': img,
            'alt': 'Bar plots',
            'title': '',
            'descr': ""
        }

def local_type_bar3d():
    labels, colors, area_proportion=prepare_local_type()

    fig = plt.figure(figsize=(12, 10))
    ax = fig.add_subplot(111, projection='3d')

    #coordonnées barres
    bottom = 0
    positions = np.arange(1, len(labels) + 1)
    for label, value, color in zip(labels, area_proportion, colors):
        ax.bar3d(1, bottom, 0, 1, value, 1, shade=True, color=color)
        bottom += value

    ax.set_xlabel('Type Local')
    ax.set_ylabel('Pourcentage')
    ax.set_zlabel('Valeurs simulées')
    ax.set_title('Répartition de la variable type_local (Diagramme en Barres Empilées 3D)')

    #emplacements des étiquettes sur axe x
    ax.set_xticks(positions)
    ax.set_xticklabels(labels)

    ax.view_init(elev=20, azim=-45) 

    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    plt.close()

    img = base64.b64encode(buffer.read()).decode('utf-8')

    return {'img': img,
            'alt': 'Bar plots',
            'title': '',
            'descr': ""
        }

def funnel_chart():
    data_2022_raw=cache.get("data_2022_raw")
    data_2022_raw['Nature mutation'] = data_2022_raw['Nature mutation'].astype(str)
    nature_mutation_counts = data_2022_raw['Nature mutation'].value_counts(dropna=False, normalize=True).head()
    nature_mutation_counts_percent = nature_mutation_counts * 100
    df_funnel = pd.DataFrame({'Labels': nature_mutation_counts.index, 'Values': nature_mutation_counts_percent.values})
    df_funnel = df_funnel.sort_values(by='Values', ascending=False)
    fig = px.funnel(df_funnel, x='Values', y='Labels', title='Répartition de la variable Nature mutation')

    fig.update_layout(xaxis_tickformat='%',
                plot_bgcolor='rgba(0, 0, 0, 0)',
                paper_bgcolor='rgba(255, 255, 255, 0.7)'
                )
    
    return {'fig': fig.to_html(full_html=False),
            'alt': 'Funnel chart', 
            'title': '',
            'descr': ""
            }

def january_barplot():
    data_2022_raw=cache.get("data_2022_raw")
    data_2022_raw['Date mutation'] = pd.to_datetime(data_2022_raw['Date mutation'], errors='coerce')#type datetime

    ventes_janvier = data_2022_raw[(data_2022_raw['Nature mutation'] == 'Vente') & (data_2022_raw['Date mutation'].dt.month == 1)]#ventes mois janvier uniquement

    all_dates = pd.date_range(start='2022-01-01', end='2022-01-31', freq='D')#dataframe date janvier
    all_dates_df = pd.DataFrame({'Date mutation': all_dates})

    ventes_janvier = pd.merge(all_dates_df, ventes_janvier, on='Date mutation', how='left')#fusion données DataFrame

    ventes_par_jour = ventes_janvier.groupby('Date mutation').size().reset_index(name='Nombre de ventes').fillna(0)#compte nombre de ventes et rempli reste par 0

    fig = px.bar(
        ventes_par_jour,
        x='Date mutation',
        y='Nombre de ventes',
        title='Nombre de ventes en France au mois de janvier',
        labels={'Nombre de ventes': 'Nombre de ventes', 'Date mutation': 'Jour du mois'},
    )

    fig.update_layout(xaxis_title='Jour du mois', yaxis_title='Nombre de ventes')

    return {'fig': fig.to_html(full_html=False),
            'alt': 'Barplot', 
            'title': '',
            'descr': ""
        }

def type_77_prepare():
    data_2022_raw=cache.get("data_2022_raw")
    data_2022_raw['Type local'] = data_2022_raw['Type local'].astype(str)
    data_2022_raw['Code departement'] = data_2022_raw['Code departement'].astype(str)

    villes_77_df=data_2022_raw[(data_2022_raw['Code departement'] == '77') & (data_2022_raw['Code postal'].notna())].copy()
    villes_77_df['Type'] = villes_77_df['Type local'].apply(lambda x: 'Appartement' if 'Appartement' in x else ('Maison' if 'Maison' in x else 'Autre'))

    grouped_df = villes_77_df.groupby(['Code postal', 'Commune', 'Type']).size().unstack(fill_value=0)
    grouped_df['Autre'] = grouped_df.sum(axis=1) - grouped_df['Appartement'] - grouped_df['Maison']

    percentage_df = grouped_df.div(grouped_df.sum(axis=1), axis=0) * 100
    return percentage_df

def type_77_barplot():
    percentage_df=type_77_prepare()
    ax = percentage_df.plot(kind='bar', stacked=True, figsize=(12, 6))

    ax.set_xticks([])
    ax.set_xlabel('')
    ax.set_ylabel('Pourcentage')
    ax.set_title('Répartition des types de local par ville dans le département 77')
    ax.legend(title='Type de local', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()

    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    plt.close()

    img = base64.b64encode(buffer.read()).decode('utf-8')

    return {'img': img,
            'alt': 'Bar plots',
            'title': '',
            'descr': ""
        }

# def prepare_commune_linechart():

#     return monthly_vente_neuf_top_10

def commune_linechart():
    data_2022_raw=cache.get("data_2022_raw")
    data_2022_raw['Date mutation'] = pd.to_datetime(data_2022_raw['Date mutation'], errors='coerce')
    data_2022_raw['Code departement']=data_2022_raw['Code departement'].astype(str)

    vente_neuf_92 = data_2022_raw[(data_2022_raw['Nature mutation'] == 'Vente en l\'état futur d\'achèvement') & (data_2022_raw['Code departement'] == '92')]
    monthly_vente_neuf = vente_neuf_92.groupby([vente_neuf_92['Date mutation'].dt.month, 'Commune'])['Nature mutation'].count().reset_index(name='Nombre de ventes')
    monthly_vente_neuf = monthly_vente_neuf.rename(columns={'Date mutation': 'Mois'})
    average_vente_by_commune = monthly_vente_neuf.groupby('Commune')['Nombre de ventes'].mean().reset_index(name='Moyenne de ventes')

    top_10_communes = average_vente_by_commune.nlargest(10, 'Moyenne de ventes')['Commune']

    df = monthly_vente_neuf[monthly_vente_neuf['Commune'].isin(top_10_communes)]
    y_col='Nombre de ventes'
    color_col='Commune'
    fig = px.line(df, x="Mois", y=y_col, color=color_col,
                  width=900,
                  height=600, title=f'{y_col} par mois par {color_col}',
                  color_discrete_sequence=px.colors.cyclical.mygbm)
    fig.update_layout(showlegend=True)

    return {'fig': fig.to_html(full_html=False),
            'alt': 'Line chart', 
            'title': '',
            'descr': ""
        }

def stacked_linechart():
    data_2022_raw=cache.get("data_2022_raw")
    y_col='Nombre de ventes'
    color_col='Commune'
    data_2022_raw['Date mutation'] = pd.to_datetime(data_2022_raw['Date mutation'], errors='coerce')
    data_2022_raw['Code departement']=data_2022_raw['Code departement'].astype(str)

    vente_neuf_92 = data_2022_raw[(data_2022_raw['Nature mutation'] == 'Vente en l\'état futur d\'achèvement') & (data_2022_raw['Code departement'] == '92')]
    monthly_vente_neuf = vente_neuf_92.groupby([vente_neuf_92['Date mutation'].dt.month, 'Commune'])['Nature mutation'].count().reset_index(name='Nombre de ventes')
    monthly_vente_neuf = monthly_vente_neuf.rename(columns={'Date mutation': 'Mois'})
    average_vente_by_commune = monthly_vente_neuf.groupby('Commune')['Nombre de ventes'].mean().reset_index(name='Moyenne de ventes')

    top_10_communes = average_vente_by_commune.nlargest(10, 'Moyenne de ventes')['Commune']

    df = monthly_vente_neuf[monthly_vente_neuf['Commune'].isin(top_10_communes)]

    fig = px.area(df, x="Mois", y=y_col, color=color_col,width=900,
                    height=600, title=f'{y_col} par mois par {color_col}',
                    color_discrete_sequence=px.colors.cyclical.mygbm)
    fig.update_layout(showlegend=True)

    return {'fig': fig.to_html(full_html=False),
            'alt': 'Line chart', 
            'title': '',
            'descr': ""
        }


### responses to GET
def linecharts(request):
    context={'items': 
               [   commune_linechart(),
                   stacked_linechart(),
                   evolution_m2_price_lineplot(),
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
               [
                january_barplot(),
                local_type_hbarplot(),
                local_type_bar3d(),
                type_77_barplot(),
                building_type_barplot(),
                barplot_price_m2(),
                principal_rooms_barplot(),
                terrain_surface_barplot()],
               'title': 'Barplots'
            }
    return render(request, 'visualisations/index.html', context)

def funnelcharts(request):
    context={'items': 
               [funnel_chart()],
               'title': 'Funnel charts'
            }
    return render(request, 'visualisations/index.html', context)