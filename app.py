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

with open('ani_recs.pickle', 'rb') as handle:
    ani_recs = pickle.load(handle)

g = nx.Graph(ani_recs)
animes = list(g.nodes())
animes.append("All")

df = pd.DataFrame({
    'AniList': animes
})

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div([
      visdcc.Network(id = 'net', options = dict(height= '600px',
                                                width= '100%',
                                                physics = {"forceAtlas2Based": {"springLength": 100},
                                                           "minVelocity": 0.75,"solver": "forceAtlas2Based"},
                                                interaction = {"hover": True,
                                                                "keyboard": {"enabled": True},
                                                               "navigationButtons": True}
)),
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
    df_func = pd.DataFrame({
        'AniList': list(g.nodes())
    })

    if(x == "All"):
        data = {'nodes': [{'id': i, 'label': i} for i in df_func['AniList'].unique()],
                'edges': [{'id': str(edge[0]) + "-" + str(edge[1]), 'from': edge[0], 'to': edge[1]} for edge in
                          g.edges()]
                }
        return data
    node_list = set(x)
    for neighbor in g.neighbors(x):
        node_list.add(neighbor)
        for next_neighbor in g.neighbors(neighbor):
            node_list.add(next_neighbor)
    sub_g = nx.subgraph(g, node_list)
    data = {'nodes': [{'id': i, 'label': i} for i in list(sub_g.nodes())],
            'edges': [{'id': str(edge[0]) + "-" + str(edge[1]), 'from': edge[0], 'to': edge[1]} for edge in
                      sub_g.edges()]
            }
    return data

if __name__ == '__main__':
    app.run_server(debug=True)

