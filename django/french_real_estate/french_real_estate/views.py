from django.shortcuts import render
import numpy as np
import pandas as pd
import plotly.express as px


def my_view(request):
    # Your NumPy and Pandas code here
    data = {'Column1': [1, 2, 3, 4], 'Column2': [5, 6, 7, 8]}
    df = pd.DataFrame(data)
    mean_column1 = np.mean(df['Column1'])

    # Plotly figure
    fig = px.scatter(df, x='Column1', y='Column2', title='Scatter Plot')

    context = {'mean_column1': mean_column1, 'plot_div': fig.to_html(full_html=False)}
    return render(request, 'test/test.html', context)