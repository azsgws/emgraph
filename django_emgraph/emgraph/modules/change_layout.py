import networkx as nx
from math import sqrt
def create_dependence_graph(nodes, graph):
    """
    依存関係を示すグラフを作成する。

    Args:
        nodes:全ノードをNodeクラスでまとめたリスト。
        graph:操作する有向グラフ。networkx.DiGraph()

    Return:
    """
    for source in nodes:
        graph.add_node(source.name)
        for target in source.targets:
            graph.add_node(target.name)
            graph.add_edge(source.name, target.name)


"""
spring layout(力学モデルの実装)
"""
def assign_nodes_position_in_spring_layout(nodes):
    """
    全てのノードのx,y座標値をspring layoutの座標にする
    Args:
        nodes: グラフのノード全て
    return:
        spring_graph_pos: spring layoutにした時の全ノードのx,y座標値。辞書型。
    """
    spring_graph = nx.DiGraph()
    create_dependence_graph(nodes, spring_graph)
    spring_graph_pos = nx.spring_layout(spring_graph, seed=1, k=1/sqrt(len(nodes))*1) #2.5

    return spring_graph_pos


"""
kamada kawai layoutの実装
"""
def assign_nodes_position_in_kamada_layout(nodes):
    """
    全てのノードのx,y座標値をkamada kawai layoutの座標にする
    Args:
        nodes: グラフのノード全て
    return:
        kamada_kawai_pos: kamada kawai layoutにした時の全ノードのx,y座標値。辞書型。
    """
    kamada_kawai_graph = nx.DiGraph()
    create_dependence_graph(nodes, kamada_kawai_graph)
    kamada_kawai_pos = nx.kamada_kawai_layout(kamada_kawai_graph)

    return kamada_kawai_pos


"""
spectral layoutの実装
"""

def assign_nodes_position_in_spectral_layout(nodes):
    """
    全てのノードのx,y座標値をspectral layoutの座標にする
    Args:
        nodes: グラフのノード全て
    return:
        spectral_pos: spcetral graphにした時の全ノードのx,y座標値。辞書型。
    """
    spectral_graph = nx.DiGraph()
    create_dependence_graph(nodes, spectral_graph)
    spectral_pos = nx.spectral_layout(spectral_graph)

    return spectral_pos


def update_nodes_position(nodes, nodes_position, ratio=1):
    """
    全ノードの座標値を更新する
    ratioでノード間の倍率を変えることが出来る．
    """
    
    #for name in nodes_position.keys():
        #print(name)
    for n in nodes:
        n.x = nodes_position[n.name][0] * ratio
        n.y = nodes_position[n.name][1] * ratio


def remove_alone_nodes(nodes):
    """
    ソース、ターゲットが一つもないノードを取り除く
    """
    alone_nodes = []
    for n in nodes:
        if n.name == "hidden":
            alone_nodes.append(n)
        if n.name == "schems_1":
            alone_nodes.append(n)
        if n.name == "HIDDEN":
            alone_nodes.append(n)
        if n.name == "SCHEMS_1":
            alone_nodes.append(n)

    print(alone_nodes)
    for n in alone_nodes:
        nodes.remove(n)

    return nodes

"""
layoutの実装終わり
"""

def change_layout_for_dot(nodes):
    """
    graphvizのdotスタイルを適用
    """
    dot_graph = nx.DiGraph()
    create_dependence_graph(nodes, dot_graph)
    dot_graph_pos = nx.nx_pydot.graphviz_layout(dot_graph, prog="dot")

    return dot_graph_pos


def change_layout_for_graphviz_layout(nodes, layout_name):
    """
    graphvizで利用可能なレイアウトを実装する
    """
    layout_name_list = ['dot', 'twopi', 'fdp', 'sfdp', 'circo', 'neato']
    if layout_name not in layout_name_list:
        print("Warning: This function has not 'layout_name' param of ", layout_name)
        layout_name = 'dot'
    graphviz_graph = nx.DiGraph()
    create_dependence_graph(nodes, graphviz_graph)
    graphviz_graph_pos = nx.nx_pydot.graphviz_layout(graphviz_graph, prog=layout_name)

    return graphviz_graph_pos


def change_layout_for_networkx_layout(nodes, layout_name):
    """
    networkxのレイアウトを適用する
    """
    layout_name_list = ['bipartite', 'circular', 'kamada_kawai', 'planar', 'random',
                        'shell', 'spring', 'spectral', 'spiral', 'multipartite']
    if layout_name not in layout_name_list:
        print("Warning: This function has not 'layout_name' param of ", layout_name)
        layout_name = 'random'
    networkx_layout_graph = nx.DiGraph()

    create_dependence_graph(nodes, networkx_layout_graph)
    nodes_pos = set_networkx_layout(layout_name, networkx_layout_graph)

    return nodes_pos


def set_networkx_layout(layout_name, graph):
    if layout_name == 'bipartite':
        return nx.bipartite_layout(graph)  # 使えない
    elif layout_name == 'circular':
        return nx.circular_layout(graph)  # 
    elif layout_name == 'kamada_kawai':  # clustering候補
        return nx.kamada_kawai_layout(graph)
    elif layout_name == 'planar':
        return nx.planar_layout(graph)
    elif layout_name == 'random':
        return nx.random_layout(graph)
    elif  layout_name == 'shell':
        return nx.shell_layout(graph)
    elif layout_name == 'spring':  # clustering候補
        return nx.spring_layout(graph)
    elif layout_name == 'spectral':  # clustering候補
        return nx.spectral_layout(graph)
    elif layout_name == 'spiral':
        return nx.spiral_layout(graph)
    elif layout_name == 'multipartite':
        return nx.mulitpartite_layout(graph)
