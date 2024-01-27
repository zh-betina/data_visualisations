from django.urls import path, include
from .views import maps, visualisations, compare, linecharts, heatmaps, barplots, piecharts, ohlcplots

urlpatterns = [
    path('', visualisations, name="Scatter plots"),
    path('maps', maps, name="Maps"),
    path('tree-map', compare, name="Tree maps"),
    path('line-chart', linecharts, name="Line charts"),
    path('heat-map', heatmaps , name="Heatmaps"),
    path('bar-plot', barplots , name="Barplots"),
    path('pie-chart', piecharts, name="Pie charts"),
    path('ohlc-chart', ohlcplots, name="OHLC charts")
]
