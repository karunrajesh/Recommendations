import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import visdcc
import plotly.express as px
import pandas as pd
import pickle
import networkx as nx


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

with open('ani_recs.pickle', 'rb') as handle:
    ani_recs = pickle.load(handle)

g = nx.Graph(ani_recs)
animes = list(g.nodes())
animes.append("All")

df = pd.DataFrame({
    'AniList': animes
})


layout = html.Div([
      visdcc.Network(id = 'net',
                     options = dict(height= '600px', width= '100%')),
      dcc.Dropdown(id = "Dropdown",
                   options=[
                       {'label': i, 'value': i} for i in df['AniList'].unique()
                   ],
                   value = "All"
                   )
])

@app.callback(
    Output('net', 'data'),
    [Input('Dropdown', 'value')])
def myfun(x):
    if(x == "All"):
        return g
    node_list = set(x)
    for neighbor in g.neighbors(x):
        node_list.add(neighbor)
        for next_neighbor in g.neighbors(neighbor):
            node_list.add(next_neighbor)
    sub_g = nx.subgraph(g, node_list)
    return sub_g
"""
@app.callback(
    Output('net', 'options'),
    [Input('color', 'value')])
def myfun(x):
    return {'nodes':{'color': x}}
"""
if __name__ == '__main__':
    app.run_server(debug=True)
