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
from pyvis.network import Network
import dash_cytoscape as cyto

external_stylesheets = [dbc.themes.MINTY]

# with open('ani_recs.pickle', 'rb') as handle:
#     ani_recs = pickle.load(handle)
# with open('watch_on.pickle', 'rb') as handle:
#     watch_on = pickle.load(handle)
# with open('ani_recs_new.pickle', 'rb') as handle:
#     ani_recs_new = pickle.load(handle)
with open('ani_recs_cleaned_06_05.pickle', 'rb') as handle:
    anime_recs = pickle.load(handle)


def create_ani_network(net_dict):
    edges_dict = {k : v["MAL Recs"] for (k, v) in net_dict.items()}
    nx_obj = nx.Graph(edges_dict)
    color_map = {}
    size_map = {}
    for node in nx_obj.nodes:
        try:
            color_to_add = net_dict[node]["Color"]
        except:
            color_to_add = "black"
        color_map[node] = {"color":color_to_add}
        size = 5 * len(nx_obj.edges(node)) + 10
        size_map[node] = {"size":size}
    nx.set_node_attributes(nx_obj, color_map)
    nx.set_node_attributes(nx_obj, size_map)
#     node_dict = {}
#     i = 0
#     for node in nx_obj.nodes:
#         print(node)
#         node_dict[node['id']] = i
#         i += 1
#     node_test_dict = {node_dict[k]:v for k,v in net_dict.items()}
    nx.set_node_attributes(nx_obj, net_dict)
    return nx_obj

g = create_ani_network(anime_recs)

def convert_to_pyvis(nx_obj):
    g = Network(height=800, width=800, notebook=True)
    # g.toggle_hide_edges_on_drag(False)
    # g.barnes_hut()
    g.from_nx(nx_obj)
    return g

def convert_to_cyto(G):
    cy = nx.cytoscape_data(G)

    # 4.) Add the dictionary key label to the nodes list of cy
    for n in cy["elements"]["nodes"]:
        for k, v in n.items():
            v["label"] = v.pop("value")

    # # 5.) Add the coords you got from (2) as coordinates of nodes in cy
    # for n, p in zip(cy["elements"]["nodes"], pos.values()):
    #     n["pos"] = {"x": int(p[0] * SCALING_FACTOR), "y": int(p[1] * SCALING_FACTOR)}

    # 6.) Take the results of (3)-(5) and write them to a list, like elements_ls
    elements = cy["elements"]["nodes"] + cy["elements"]["edges"]
    return elements
# elements = convert_to_cyto(g)

# g = nx.Graph(ani_recs_new)
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

### ADD COLORS INTO THE VISDCC
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = dbc.Container(
    [
    html.H1("Anime Recommendation Selector"),
    html.Hr(),
    html.Div([
    dbc.Row([
        dbc.Col(dbc.Container([html.Div(dcc.Dropdown(id = "Dropdown",
                options=[{'label': i, 'value': i} for i in df['AniList'].unique()],
                value = "All")),
                html.Div(id = 'dt')]),width=5),
        dbc.Col(html.Button('Reset',id='reset_button', n_clicks=0), width = 3)
    ]
    ),
    dbc.Row(
        [

            dbc.Col(html.P(id = 'stats', style={'whiteSpace': 'pre-wrap'}), width = 2),
            dbc.Col(
                visdcc.Network(id = 'net', selection = {'nodes':[], 'edges':[]}, options = dict(height= '600px',
                                                width= '100%',
                                                physics = {"forceAtlas2Based": {"springLength": 100},
                                                           "minVelocity": 0.75,"solver": "forceAtlas2Based"},
                                                interaction = {"hover": True,
                                                                "keyboard": {"enabled": True},
                                                               "navigationButtons": True,
                                                               "selectConnectedEdges": False},
                                                layout = {"improvedLayout":True})), width =7),
            dbc.Col(html.P(id = 'description', style={'whiteSpace': 'pre-wrap'}), width = 3),
        ]),
    html.Div(id = 'nodes'),
    html.Div(id = 'edges'),
    ])
    #html.Div(id = 'dt'),])
    ],
    fluid=True,
)
@app.callback(Output('Dropdown','value'),
             [Input('reset_button','n_clicks')])
def update(reset):
    return 'All'
@app.callback(
    Output('net', 'data'),
    [Input('Dropdown', 'value')])
def myfun(x):
    df_func = pd.DataFrame({
        'AniList': list(g.nodes())
    })

    if(x == "All"):
        # data = {'nodes': [{'id': i, 'label': i} for i in df_func['AniList'].unique()],
        #         'edges': [{'id': str(edge[0]) + "-" + str(edge[1]), 'from': edge[0], 'to': edge[1]} for edge in
        #                   g.edges()]
        #         }
        g_pyvis = convert_to_pyvis(g)
        data = {'nodes': g_pyvis.nodes,
                'edges': [{'id': str(edge['from']) + " - " + str(edge['to']), 'from': edge['from'], 'to': edge['to']}
                          for edge in g_pyvis.edges]
                }
        #data = convert_to_cyto(g)
        return data
    node_list = set(x)
    for neighbor in g.neighbors(x):
        node_list.add(neighbor)
        for next_neighbor in g.neighbors(neighbor):
            node_list.add(next_neighbor)
    sub_g = nx.subgraph(g, node_list)
    g_pyvis = convert_to_pyvis(sub_g)
    # data = convert_to_cyto(sub_g)
    # data = {'nodes': sub_g.nodes,
    #         'edges': [{'id': str(edge[0]) + "-" + str(edge[1]), 'from': edge[0], 'to': edge[1]} for edge in
    #                   sub_g.edges()]
    #         }
    data = {'nodes': g_pyvis.nodes,
            'edges': [{'id': str(edge['from']) + " - " + str(edge['to']), 'from': edge['from'], 'to': edge['to']}
                      for edge in g_pyvis.edges]
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
    Output('description', 'children'),
    [Input('net', 'selection')])
def descrfunc(x):
    s = 'Description : '
    if len(x['nodes']) > 0 :
        s += str(anime_recs[x['nodes'][0]]['Description'])
    return s

@app.callback(
    Output('stats', 'children'),
    [Input('net', 'selection')])
def statsfunc(x):

    # There's a better way to do this...
    s = 'Selected : '
    if len(x['nodes']) > 0 :
        s += str(x['nodes'][0])
        s += '\n'
        s += 'Episodes : '
        s += str(anime_recs[x['nodes'][0]]['Episodes'])
        s += '\n'
        s += 'Aired : '
        s += str(anime_recs[x['nodes'][0]]['Season']) + " " + str(anime_recs[x['nodes'][0]]['Year'])
        s += '\n'
        s += 'Genres : '
        s += str(anime_recs[x['nodes'][0]]['Genre'])
        s += '\n'
        s += 'Available at : '
        s += str(anime_recs[x['nodes'][0]]['Stream Sites'])
    return s

@app.callback(
    Output('edges', 'children'),
    [Input('net', 'selection')])
def edgefunc(x):
    s = 'Selected edges : '
    if len(x['edges']) > 0 : s = [s] + [html.Div(i) for i in x['edges']]
    return s


# To update with full table
# @app.callback(
#     Output('dt', 'children'),
#     [Input('net', 'selection')])
# def createDT(x):
#     node = x['nodes'][0]
#     neighbors = g[node]
#     spacer = ", "
#     total_list = [spacer.join(watch_on[n]) for n in neighbors]
#     """
#     if(node in ani_recs.keys()):
#         recs_total = [ani_recs[node][n] for n in list(neighbors)]
#         data = {'Recommendations': list(neighbors), '# Recs': recs_total}
#         df = pd.DataFrame(data)
#         return generate_html_table(df)
#     """
#     data = {'Recommendations': list(neighbors), 'Watch At': total_list}
#     df = pd.DataFrame(data)
#     #table = dbc.Table.from_dataframe(df, striped=True, bordered=True, hover=True)
#     return generate_html_table(df)

# Create function for tags

# Create function for anime description

if __name__ == '__main__':
    app.run_server(debug=True)

