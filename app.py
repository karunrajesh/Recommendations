import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import visdcc
import plotly.express as px
import dash_table
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

def generate_html_table(df):
    return html.Table(
        # Header
        [html.Tr([html.Th(col) for col in df.columns])] +
        # Body
        [html.Tr([
            html.Td(df.iloc[i][col]) for col in df.columns
        ]) for i in range(len(df))])


app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div([
    visdcc.Network(id = 'net', selection = {'nodes':[], 'edges':[]}, options = dict(height= '600px',
                                                width= '100%',
                                                physics = {"forceAtlas2Based": {"springLength": 100},
                                                           "minVelocity": 0.75,"solver": "forceAtlas2Based"},
                                                interaction = {"hover": True,
                                                                "keyboard": {"enabled": True},
                                                               "navigationButtons": True})),
    html.Div(id = 'nodes'),
    html.Div(id = 'edges'),
    html.Div(id = 'dt', style = {'width': '40%'}),
    dcc.Dropdown(id = "Dropdown",
                options=[{'label': i, 'value': i} for i in df['AniList'].unique()],
                value = "All")
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

@app.callback(
    Output('nodes', 'children'),
    [Input('net', 'selection')])
def nodefunc(x):
    s = 'Selected nodes : '
    if len(x['nodes']) > 0 : s += str(x['nodes'][0])
    return s

@app.callback(
    Output('edges', 'children'),
    [Input('net', 'selection')])
def edgefunc(x):
    s = 'Selected edges : '
    if len(x['edges']) > 0 : s = [s] + [html.Div(i) for i in x['edges']]
    return s

@app.callback(
    Output('dt', 'children'),
    [Input('net', 'selection')])
def createDT(x):
    node = x['nodes'][0]
    neighbors = g[node]
    if(node in ani_recs.keys()):
        recs_total = [ani_recs[node][n] for n in list(neighbors)]
        data = {'Recommendations': list(neighbors), '# Recs': recs_total}
        df = pd.DataFrame(data)
        return generate_html_table(df)
    else:
        data = {'Recommendations': list(neighbors)}
        df = pd.DataFrame(data)
        return generate_html_table(df)

if __name__ == '__main__':
    app.run_server(debug=True)

