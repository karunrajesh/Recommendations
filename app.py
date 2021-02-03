import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import visdcc
import plotly.express as px
import dash_table
import pandas as pd
import pickle
import networkx as nx

external_stylesheets = [dbc.themes.CYBORG]

with open('ani_recs.pickle', 'rb') as handle:
    ani_recs = pickle.load(handle)
with open('watch_on.pickle', 'rb') as handle:
    watch_on = pickle.load(handle)
with open('ani_recs_new.pickle', 'rb') as handle:
    ani_recs_new = pickle.load(handle)

g = nx.Graph(ani_recs_new)
animes = list(g.nodes())
animes.insert(0,"All")


df = pd.DataFrame({
    'AniList': animes
})

def generate_html_table(df):
    #table = dbc.Table.from_dataframe(df, striped=True, bordered=True, hover=True)

    table_header = [html.Tr([html.Th(col) for col in df.columns])]
    table_body = [html.Tr([
        html.Td(df.iloc[i][col]) for col in df.columns
    ]) for i in range(len(df))]
    table = dbc.Table(
        # using the same table as in the above example
        table_header + table_body,
        bordered=True,
        dark=True,
        hover=True,
        responsive=True,
        striped=True,
    )
    return table
    """
    return html.Table(
        # Header
        [html.Tr([html.Th(col) for col in df.columns])] +
        # Body
        [html.Tr([
            html.Td(df.iloc[i][col]) for col in df.columns
        ]) for i in range(len(df))], style={
        'textAlign': 'center',
        'border': '1px solid red',
    })
    """


app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = dbc.Container(
    [
    html.H1("Anime Recommendation Selector"),
    html.Hr(),
    html.Div([
    dbc.Row(
        [
            dbc.Col(dbc.Container([html.Div(dcc.Dropdown(id = "Dropdown",
                options=[{'label': i, 'value': i} for i in df['AniList'].unique()],
                value = "All")),
                html.Div(id = 'dt')]),width=5),
            dbc.Col(visdcc.Network(id = 'net', selection = {'nodes':[], 'edges':[]}, options = dict(height= '600px',
                                                width= '100%',
                                                physics = {"forceAtlas2Based": {"springLength": 100},
                                                           "minVelocity": 0.75,"solver": "forceAtlas2Based"},
                                                interaction = {"hover": True,
                                                                "keyboard": {"enabled": True},
                                                               "navigationButtons": True,
                                                               "selectConnectedEdges": False})), width =7),
        ]),
    html.Div(id = 'nodes'),
    html.Div(id = 'edges'),])
    #html.Div(id = 'dt'),])
    ],
    fluid=True,
)

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
    spacer = ", "
    total_list = [spacer.join(watch_on[n]) for n in neighbors]
    """
    if(node in ani_recs.keys()):
        recs_total = [ani_recs[node][n] for n in list(neighbors)]
        data = {'Recommendations': list(neighbors), '# Recs': recs_total}
        df = pd.DataFrame(data)
        return generate_html_table(df)
    """
    data = {'Recommendations': list(neighbors), 'Watch At': total_list}
    df = pd.DataFrame(data)
    #table = dbc.Table.from_dataframe(df, striped=True, bordered=True, hover=True)
    return generate_html_table(df)

if __name__ == '__main__':
    app.run_server(debug=True)

