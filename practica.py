import dash 
from dash import dcc     
from dash import html 
from dash import Input, Output
import plotly.graph_objs as go
import pandas as pd


df = pd.read_csv('tabla_final.csv')
df = df.sort_values("Strike")

df_call = df[df["Tipo_Opcion"] == "call"]
df_put = df[df["Tipo_Opcion"] == "put"]


app = dash.Dash() 
app.layout = html.Div(children =[ 
    html.H1("Dash Opciones"), 
     dcc.Dropdown(
                df['Venc_Opciones'].unique(),
                df['Venc_Opciones'][0],
                id='crossfilter-xaxis-column',
            ),
    dcc.Graph( 
        id ="example", 
        figure ={ 
            'data':[ 
                       {'x': df_call["Strike"], 
                        'y': df_call["volatilidad"], 
                        'type':'line',  
                        'name':'Call'}, 
                       {'x':df_put["Strike"],  
                        'y':df_put["volatilidad"],  
                        'type':'line', 
                        'name':'Puts'} 
                   ], 
            'layout':{ 
                'title':'Volatility Skew'
            } 
        } 
    ) 
]) 

@app.callback(
    Output('example', 'figure'),
    Input('crossfilter-xaxis-column', 'value'))
def update_graph(xaxis_column_name):

    df_call_nuevo = df[(df["Venc_Opciones"] == xaxis_column_name) & (df["Tipo_Opcion"] == "call")]
    df_put_nuevo = df[(df["Venc_Opciones"] == xaxis_column_name) & (df["Tipo_Opcion"] == "put")]
    fig = go.Figure(data=[go.Scatter(x=df_call_nuevo["Strike"], y=df_call_nuevo["volatilidad"], name="Call"), 
    go.Scatter(x=df_put_nuevo["Strike"], y=df_put_nuevo["volatilidad"], name="Put")])


    return fig


app.run_server() 