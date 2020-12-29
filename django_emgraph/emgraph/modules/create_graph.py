"""
依存関係を階層形式で表示する
・階層化の手順
　　1. 階層割当
　　2. 交差削減
　　3．座標決定
"""
import networkx as nx
import json
from collections import defaultdict
import operator
import random
import time
import math
from emgraph.modules import retrieve_environment
from pprint import pprint, pformat
import sys
import os
from emgraph.modules import change_layout
from emgraph.modules import calc_graph
from mizar_graph.settings import GRAPH_DIR
import matplotlib.pyplot as plt


class Node:
    """
    Attributes:
        name: ノードの名前。str()。
        targets: 自身が指しているノードの集合。set()。デフォルトは空集合set()。
        sources: 自身を指しているノードの集合。set()。デフォルトは空集合set()。
        x, y: ノードの座標(x,y)。ともにint()。デフォルトは-1。
        href: ノードのリンク。str()。デフォルトは空列 ""。
        is_dummy: ノードがダミーか否か。bool()。デフォルトはFalse。
    """

    def __init__(self, name, targets=None, sources=None, x=None, y=None, href=None, is_dummy=None):
        self.name = name
        self.targets = set() if targets is None else targets
        self.sources = set() if sources is None else sources
        self.x = -1 if x is None else x
        self.y = -1 if y is None else y
        self.href = "" if href is None else href
        self.is_dummy = False if is_dummy is None else is_dummy

    def __str__(self):
        name = self.name
        targets = self.targets
        sources = self.sources
        x = self.x
        y = self.y
        return f"name: {name}, targets: {targets}, sources: {sources}, (x, y)= ({x}, {y})"


class Stack:
    """
    Attributes:
        items: スタックの内容。list。
    """

    def __init__(self):
        self.items = []

    def is_empty(self):
        """スタック内が空かどうか調べる"""
        return self.items == []

    def push(self, item):
        """スタックに値をプッシュする"""
        self.items.append(item)

    def pop(self):
        """スタックの内容をポップする"""
        return self.items.pop()


class Count:
    """
    関数が何度呼ばれたかをカウントするクラス。
    Attributes:
        count: 関数funcを読んだ回数。int。
        func: 関数オブジェクト。
    """

    def __init__(self, func):
        self.count = 0
        self.func = func

    def __call__(self, *args, **kwargs):
        self.count += 1
        return self.func(*args, **kwargs)

    def reset(self):
        """カウンタをリセットする"""
        self.count = 0


class Error(Exception):
    """
    Exceptionクラスの基底クラス
    """
    pass


class InputCategoryNameError(Error):
    """
    入力されたカテゴリーの名前が存在しないものだった時に投げるエラー
    """

    def __init__(self, expression):
        self.expression = expression


class EmptyCategoryError(Error):
    """
    入力されたファイル内にカテゴリーが存在しないときに投げるエラー
    """

    def __init__(self, expression):
        self.expression = expression


class NotExistLayout(Error):
    """
    入力されたレイアウトが存在しないときに投げるエラー
    """

    def __init__(self, expression):
        self.expression = expression



def create_node_list(input_node_dict):
    """
    input_node_dictをノードオブジェクトにする．
        ・name: input_node_dictのkey。str。
        ・target_nodes: input_node_dictのvalueの第一要素。set()。
        ・source_nodes: target_nodesをもとに作成したsource_nodes。set()。
        ・x, y: -1。int。
        ・href: INPUT_NODE_DICTのvalueの第二要素。str。
        ・is_dummy: False。bool。
    Args:
        input_node_dict: 入力されたノードの関係を示す辞書型データ。
                         ノードの名前をキーに持ち、値としてリストを持つ。リストの要素は次のようになる。
                             第1要素: keyのノードが指すノードの集合。set()
                             第2要素: keyのノードのリンク先URL。str()
    Returns:
        インスタンス化されたノードのリスト。
    """
    nodes = []
    name2node = {}
    # node_dict, nodesの作成
    # k: ノードの名前(str)、v[1]: ノードkのリンクURL(str)
    for k, v in input_node_dict.items():
        n = Node(name=k, href=v["url"])
        name2node[k] = n
        nodes.append(n)

    # targetsの作成
    # k: ノードの名前(str)、v[0]: ノードkがターゲットとするノードの名前(str)の集合
    for k, v in input_node_dict.items():
        for target in v["dependency_articles"]:
            """
            # 未作成のノードを参照している場合は、そのノードを作成しておく
            if target not in name2node:
                n = Node(name=target)
                name2node[target] = n
                nodes.append(n)
            """

            # 存在しないノードへの参照は省く
            if target in name2node:
                name2node[k].targets.add(name2node[target])
            """
            name2node[k].targets.add(name2node[target])
            """

    # sourcesの作成
    # k: ノードの名前(str)、v: ノードkのNodeオブジェクト(object)
    for k, v in name2node.items():
        for target in v.targets:
            target.sources.add(name2node[k])
    return nodes


"""
#1．階層割当(最長パス法)
"""


def assign_level(nodes):
    top_nodes = assign_top_node(nodes)
    for top_node in top_nodes:
        assign_level2node_recursively(nodes, top_node, 0)


def assign_top_node(nodes):
    """
    グラフのルートを決定する。ルート：矢印が出ていない(参照をしていない)ノードである。
　　その後、level2node()でその下の階層のノードを決めていく。
    Args:
        nodes:全ノードをNodeクラスでまとめたリスト。
    Return:
    """
    top_nodes = []
    for top_node in nodes:
        if not top_node.targets:
            top_node.y = 0
            top_node.x = 0
            top_nodes.append(top_node)
    return top_nodes


def assign_level2node_recursively(nodes, target, target_level):
    """
    階層が1以上（y座標が1以上）のノードの階層を再帰的に決定する。階層の割当は次のルールに従う。
    ・まだ階層を割り当てていないノードならば、targetの1つ下の階層に割り当てる。そして、再帰する。
    ・既に座標を割り当てており、その階層が今の階層(assign_node_level)以上高い階層ならば、一つ下の階層に再割当する。
　　・既に階層を割り当てており、その階層が今の階層よりも低い階層ならば、何もしない。
    Args:
        nodes: 全ノードをNodeクラスでまとめたリスト。
        target: ターゲットとなるノード。このノードを指すノードに階層を割り当てていく。
        target_level: targetの階層。targetを指すノードは基本的にこの階層の1つ下の階層に割り当てられる。
    """
    #print(target.name)
    assign_node_level = target_level + 1
    for assign_node in target.sources:
        if assign_node.x < 0:
            assign_node.y = assign_node_level
            assign_node.x = 0
            assign_level2node_recursively(nodes, assign_node, assign_node_level)
        elif assign_node.y <= assign_node_level:
            assign_node.y = assign_node_level
            assign_level2node_recursively(nodes, assign_node, assign_node_level)


def assign_x_sequentially(nodes):
    """
    全てのノードに対して、x座標を割り当てる。
    Args:
        nodes:全ノードをNodeクラスでまとめたリスト。
    """
    y2x = defaultdict(int)
    for node in nodes:
        node.x = y2x[node.y]
        y2x[node.y] += 1


"""
間引き
"""


def pluck_waste_edges(nodes):
    """
    エッジの間引きを行う。
    各ノードのターゲットから、間引いてよいターゲットを見つけ、間引く。
    Args:
        nodes: 間引きを行いたいノード(1個以上)
    Return:
    """
    node2ancestors = dict()  # key=node, value=keyの全祖先
    for node in nodes:
        make_node2ancestors_recursively(node, node2ancestors)
        removable_edge_list = search_removable_edges(node, node2ancestors)
        #print(len(node2ancestors))
        for source, target in removable_edge_list:
            source.targets.remove(target)
            target.sources.remove(source)


def make_node2ancestors_recursively(node, node2ancestors):
    """
    key=node, value=keyの全祖先のノードのセット
    となる辞書を作る。
    Args:
        node: 全祖先を知りたいノード
        node2ancestors: key=ノード, value=keyの全祖先のセット
    Return:
        nodeにターゲットが存在しない：要素がnodeのみのセット
        それ以外：nodeの全祖先のノードのセット
    """
    if not node.targets:
        node2ancestors[node] = set()
        return {node}

    elif node in node2ancestors.keys():
        return node2ancestors[node]

    ancestors = set()
    for target in node.targets:
        if target.name != node.name:
            ancestors = ancestors | {target}
            if target in node2ancestors.keys():
                ancestors = ancestors | node2ancestors[target]
            else:
                ancestors = ancestors | make_node2ancestors_recursively(target, node2ancestors)
    node2ancestors[node] = ancestors
    return ancestors


def search_removable_edges(node, node2ancestors):
    """
    複数回参照するノードへのエッジを見つける．
    Args:
        node: 間引きたいノード(ソース側)。
        node2ancestors: key=nodeのtarget, value=keyの全祖先のノードのセット の辞書。
    Return:
        thin_out_edges: 間引いてよいエッジ(source, target)のリスト。
                            source,targetはともにNodeオブジェクト。
    """
    removable_edges = list()
    # node2ancestorsの中からkeyがnode.targets内に存在するもののみ取ってくる。
    target2ancestors = \
        {target: ancestors for target, ancestors in node2ancestors.items() if target in node.targets}
    target_route_union = make_union_by_dict_value(target2ancestors)
    for target in node.targets:
        if target in target_route_union:
            removable_edges.append((node, target))
    return removable_edges


def make_union_by_dict_value(set_dict):
    """
    valueにsetを持つdictの全valueの和集合を作る．
    Args:
        set_dict: セットを値に持つ辞書
    Return:
        set_union: set_dictの値の和集合
    """
    set_union = set()
    for v in set_dict.values():
        set_union = set_union | v
    return set_union


"""
ダミーノードの作成
"""
def insert_dummy_nodes(nodes): 
    cut_edges_higher_than_1(nodes)
    assign_x_sequentially(nodes)


def cut_edges_higher_than_1(nodes):
    """
    階層が2以上はなれているエッジを見つけ、スタックに格納する。
    その後、スタックの内容をcut_edge()を用いてダミーノードを取得し、
    それをnodesに挿入し、階層差がすべて1になるようにする。
    Args:
        nodes:全ノードをNodeクラスでまとめたリスト。
    Return:
    """
    cut_edge_stack = Stack()
    for target in nodes:
        for source in target.sources:
            if calc_edge_height(source, target) > 1:
                cut_edge_stack.push((source, target))

    while cut_edge_stack.is_empty() is False:
        source, target = cut_edge_stack.pop()
        dummy = cut_edge(source, target)
        # dummyの内容はcut_edges()のReturn:を参照。
        nodes.append(dummy)
        if calc_edge_height(dummy, target) > 1:
            cut_edge_stack.push((dummy, target))


def calc_edge_height(node1, node2):
    """
    node1とnode2の階層差を返す
    Args:
        node1, node2: 階層差を比較するノード。Nodeオブジェクト。
    Return:
         node1, node2の階層差。絶対値でint。
    """
    return abs(node1.y - node2.y)


@Count
def cut_edge(source, target):
    """
    source_nodeとtarget_nodeのエッジを切り、その間にダミーノードを挿入する。
    Args:
        source: target_nodesからtargetを取り除き、間にダミーノードを入れたいノード。Nodeオブジェクト。
        target: source_nodesからsourceを取り除き、間にダミーノードを入れたいノード。Nodeオブジェクト。
    Return:
        dummy: sourceとtargetの間に挿入したダミーノード。階層はsourceの一つ上にする。Nodeオブジェクト。
            属性は次のように設定する。
            name: "dummy1"(数字はインクリメントしていく)。
            targets: 要素がtargetのみの集合。
            sources: 要素がsourceのみの集合。
            x: 0
            y: source.y-1
            href: ""
            is_dummy: True
    """
    assert calc_edge_height(source, target) > 1
    dummy_counter = cut_edge.count
    source.targets.remove(target)
    target.sources.remove(source)
    dummy = Node("dummy" + str(dummy_counter),
                 targets={target},
                 sources={source},
                 x=0,
                 y=source.y - 1,
                 is_dummy=True
                )
    source.targets.add(dummy)
    target.sources.add(dummy)

    return dummy


"""
#2. 交差削減
"""


def reduce_cross(reduce_times, nodes):
    for i in range(reduce_times):
        sort_nodes_by_xcenter(nodes, downward=False)
        sort_nodes_by_xcenter(nodes, downward=True)
        # print(i)


def sort_nodes_by_xcenter(all_nodes, downward):
    """
    重心が小さいノードから左に配置する。
    重心の計算はcalc_xcenter()にて説明。
    上の階層から下の階層へ、もしくは下の階層から上の階層へと操作を行う。
    Args:
        all_nodes:全ノードをNodeオブジェクトでまとめたリスト。
        downward: Trueなら階層の上から下へ操作を行う。Falseなら階層の下から上へと操作を行う。
    Return:
    """
    level2nodes = divide_nodes_by_level(all_nodes)
    if downward:
        for level, nodes in sorted(level2nodes.items()):
            assign_x_by_xcenter(node2xcenter(nodes, from_targets=True))
    else:
        for level, nodes in sorted(level2nodes.items(), key=lambda k: -k[0]):
            assign_x_by_xcenter(node2xcenter(nodes, from_targets=False))


def divide_nodes_by_level(nodes):
    """
    ノードを階層レベルで分類する．
    Args:
        nodes:全ノードをNodeオブジェクトでまとめたリスト。
    Return:
        each_level_nodes: key=階層レベル, value=階層レベルがkeyのノードのリスト　となる辞書。
    """
    each_level_nodes = defaultdict(list)
    for node in nodes:
        each_level_nodes[node.y].append(node)
    return each_level_nodes


def node2xcenter(nodes, from_targets):
    """
    (v1, v2)のタプルのリストを作る。
        v1=Nodeオブジェクト、v2=v1の重心の値(float)
    Args:
        nodes:重心を求めたいNodeオブジェクトのリスト。Nodeオブジェクトの階層は等しいのが好ましい。
        from_targets: True:重心をtargetsを用いて計算する, False:重心をsourcesを用いて計算する。
    Return:
         (v1, v2)となるタプルのリスト。
            v1: Nodeオブジェクト
            v2: 重心の値(float)
    """
    if from_targets:
        return [(node, calc_xcenter(node.targets)) for node in nodes]
    else:
        return [(node, calc_xcenter(node.sources)) for node in nodes]


def calc_xcenter(nodes):
    """
    nodeの重心をターゲットもしくはソースの集合から計算する
    重心の計算
        ターゲット(もしくはソース)が存在する場合：
            重心 = (ターゲット(ソース)のx座標の総和) / (ターゲット(ソース)の数)
        ターゲット（もしくはソース）が存在しない場合：
            重心 = 正の無限大, float('infinity')
    Args:
        nodes: ソートしたい階層のノードのリスト。
    Return:
        重心の値(float)
    """
    if len(nodes) > 0:
        return sum([node.x for node in nodes]) / len(nodes)
    else:
        return float('infinity')


def assign_x_by_xcenter(node2xcenter_tuple):
    """
    タプル(v1, v2)のリストをソートし、それらに順にx座標を割り当てる。
        v1: Nodeオブジェクト
        v2: v1の重心の値(float)
    Args:
        node2xcenter_tuple: (v1, v2) のタプルのリスト(v1, v2は同上)
    Return:
    """
    # 重心の値で昇順にソート重心が等しいなら、ｘが小さいほうから
    sorted_node2xcenter = sorted(node2xcenter_tuple, key=lambda tup: tup[1])  
    sorted_nodes = [node[0] for node in sorted_node2xcenter]
    assign_x_sequentially(sorted_nodes)


"""
交差の計測、エッジの長さの総和の計測
"""


def count_cross_var1(all_nodes):
    """
    交差数を階層ごとに上から下へと数える。
    交差条件
        2つのエッジedge=(s1, t1), other_edge=(s2, t2)において
        ・s1とs2のy座標が等しい
        ・s1のx座標がs2のx座標より小さい
        ・t1のx座標がt2のx座標より大きい
    Args:
        all_nodes:全てのノード。Nodeオブジェクトのリスト。
    Return:
        cross_counter: 交差数(int)
    """
    cross_counter = 0
    level2nodes = divide_nodes_by_level(all_nodes)
    for level, nodes in sorted(level2nodes.items()):
        edges = retrieve_edge(nodes)
        for edge in edges:
            for other_edge in edges:
                # edge[0]: sourceノード, エッジのソース.  edge[1]: targetノード, エッジのターゲット.
                if edge[0].y == other_edge[0].y and edge[0].x < other_edge[0].x and edge[1].x > other_edge[1].x:
                    cross_counter += 1
    return cross_counter


def retrieve_edge(nodes):
    """
    グラフのエッジを取得する。ノードのソースを用いて作成する。
    Args:
        nodes: (ソースが存在する)全ノード
    Return:
        edges:エッジを(source, target)としてタプルで作成し、リストにまとめたもの。
              source, targetはともにNodeオブジェクト。
              edges = [(source1, target1), (source2, target2), ...]
    """
    edges = []
    for node in nodes:
        for source in node.sources:
            edges.append((source, node))
    return edges


def search_edge(edge_set, search_x):
    """
    edge_set内にsourceもしくはtargetにsearch_xをx座標に持つものがあった場合、それらを返す．
    Args:
        edge_set:
        search_x:
    Return:
        set
    """
    search_edges = set()
    for edge in edge_set:
        if edge[1][0] == search_x or edge[0][0] == search_x:
            search_edges.add(edge)
    return search_edges


def count_cross_var3(all_nodes):
    level2nodes = divide_nodes_by_level(all_nodes)
    cross_counter = 0
    for level, nodes in sorted(level2nodes.items()):
        edges = retrieve_edge(nodes)
        sorted_edges = sorted(edges, key=lambda e: e[1].x)  # targetのxでソート
        pop_edges = list()
        while sorted_edges:
            edge = sorted_edges.pop(0)
            pop_edges.append(edge)
            if len(pop_edges) > 1:
                if pop_edges[-2][0].x > pop_edges[-1][0].x and pop_edges[-2][1] != pop_edges[-1][1]:
                    before_index = pop_edges.index(edge)
                    pop_edges = sorted(pop_edges, key=lambda e: e[0].x)  # sourceのxでソート
                    after_index = pop_edges.index(edge)  # edgeじゃなくてedgeと同じxを持つやつ
                    cross_counter += before_index - after_index
    return cross_counter


def calc_edge_length_sum(all_nodes):
    """
    エッジの長さの総和を返す。
    ソースとターゲットの離れ具合を測る。
    Args:
        all_nodes: 総和を求めたいエッジを持つ全ノード。Nodeオブジェクト。
    Return:
        total_edge_length: 全エッジの長さの総和。float。
    """
    total_edge_length = 0.0
    level2nodes = divide_nodes_by_level(all_nodes)
    for level, nodes in sorted(level2nodes.items()):  # levelでループ
        edges = retrieve_edge(nodes)
        for source, target in edges:
            total_edge_length += math.sqrt(pow(source.y - target.y, 2) + pow(source.x - target.x, 2))
    return total_edge_length


"""
ダミーノードの削除
"""


def delete_dummy(all_nodes):
    """
    ダミーノードの削除を行う．
    Args:
        all_nodes: グラフ内の全てのノード
    Return:
        all_nodesからダミーノードを取り除いたもの
    """
    edge_list = retrieve_nodes_connected_by_dummy(all_nodes)
    add_edges(edge_list)
    all_nodes = remove_dummy(all_nodes)
    return all_nodes


def retrieve_nodes_connected_by_dummy(all_nodes):
    """
    ダミーノードで接続されていた正規のノード(is_dummyがFalseのノード)のペアを取得する。
    アルゴリズム
        1. ノードを上の階層から順にみていく。
            1.1. 正規のノードのソースを見て、その中にダミーがあるかを見る
                1.1.1 もしダミーノードがあれば、正規のノードが見つかるまでソースを辿っていく。
                1.1.2 正規のノードに辿り着いたら、辿り始めたノードと辿り着いたノードをタプルにしてリストに追加する。
                      このリストが取得したいノードのペアのリストとなる。
    Args:
        all_nodes: 全ノードのリスト
    Return:
        pair_of_nodes: ダミーノードで接続されていた正規のノードのペアのリスト
    """
    pair_of_nodes = []
    level2nodes = divide_nodes_by_level(all_nodes)
    for level, nodes in sorted(level2nodes.items()):  # 上の階層から下の階層へと探索する
        for node in nodes:
            if node.is_dummy is True:
                continue
            for source in node.sources:
                if source.is_dummy is True:
                    while source.is_dummy is True:
                        source = list(source.sources)[0]
                    pair_of_nodes.append((source, node))
    return pair_of_nodes


def add_edges(edges):
    """
    エッジを追加する．
    エッジのターゲットノードのsourcesにエッジのソースノードを，
    エッジのソースノードのtargetsにエッジのターゲットノードを追加する．

    Args:
        edges: 追加したいエッジのタプル(source, target)が格納されたリスト
    Return:
    """
    for edge in edges:
        edge[0].targets.add(edge[1])  # edge[0]: エッジのsource, edge[1]: エッジのtarget
        edge[1].sources.add(edge[0])


def remove_dummy(all_nodes):
    """
    ダミーノードをall_nodes内から取り除く。
    正規のノード(is_dummyがFalse)のtargets, およびsourcesからダミーノードを取り除く。
    Args:
        all_nodes: 全てのノード
    Return:
        all_non_dummy_nodes: all_nodesからダミーノードを取り除いたもの
    """
    cut_targets = list()
    cut_sources = list()

    # 正規のノードのsources, targetsに存在するダミーを記録する
    for node in all_nodes:
        if node.is_dummy is False:
            cut_targets += retrieve_node_to_dummy(node, from_targets=True)
            cut_sources += retrieve_node_to_dummy(node, from_targets=False)

    # 記録したものを用いて、ダミーとのつながりを切る
    for node, dummy_source in cut_sources:
        node.sources.remove(dummy_source)
    for node, dummy_target in cut_targets:
        node.targets.remove(dummy_target)

    # all_nodes内からダミーノードを取り除いて返す。
    all_non_dummy_nodes = [n for n in all_nodes if n.is_dummy is False]
    return all_non_dummy_nodes


def retrieve_node_to_dummy(node, from_targets):
    """
    nodeのtargetsもしくはsources内のダミーノードを探し、(node, dummy)の形にし、
    リストにまとめて返す。
    Args:
        node: Nodeオブジェクト
        from_targets: ダミーノードをtargetsから探すかどうか
    Return:
        dummy_nodes: (node, dummy)
            node: ダミーノードを持つノード
            dummy: nodeのダミーノード
    """
    dummy_nodes = list()
    connect_nodes = node.targets if from_targets else node.sources
    for connect_node in connect_nodes:
        if connect_node.is_dummy is True:
            dummy_nodes.append((node, connect_node))
    return dummy_nodes


def leave_no_space(all_nodes):
    """
    ダミーがなくなって空いた隙間を詰める
    :param all_nodes:
    :return:
    """
    level2nodes = divide_nodes_by_level(all_nodes)
    count = 0
    for level, nodes in sorted(level2nodes.items()):
        for node in sorted(nodes, key=lambda n: n.x):
            node.x = count
            count += 1
        count = 0


"""
#3. 座標決定
"""


def assign_coordinate(counter, nodes):
    for i in range(counter):
            move_node_closer_to_connected_nodes(all_nodes=nodes, downward=False)  # false
            move_node_closer_to_connected_nodes(all_nodes=nodes, downward=True)  # true
            # print(i)


def move_node_closer_to_connected_nodes(all_nodes, downward):
    """
    ノードのx座標をターゲットもしくはソースに近づくように移動させる。
    更新は各階層ごとに上の階層から下の階層へ、もしくは下の階層から上の階層へと行う。
    更新のために、優先順位や理想x座標を求め、更新は
    update_x_in_priority_order(), update_x2idealx_recursively()
    にて行う。
    Args:
        all_nodes: 全てのノード
        downward: 上の階層から下の階層へ行うかどうか。
                Trueなら上の階層から下の階層へ、Falseなら下の階層から上の階層へと座標更新を行う。
    Return:
    """
    level2nodes = divide_nodes_by_level(all_nodes)
    key = lambda k: k[0] if downward else -k[0]  # 処理の順(上の階層からか、下の階層からか)を設定する
    for level, nodes in sorted(level2nodes.items(), key=key):
        node2priority_dict = node2priority(nodes, downward)
        node2idealx_dict = node2idealx(nodes, downward)
        # """
        if downward is False:
            update_idealx(node2idealx_dict)
        # """
        update_x_in_priority_order(nodes, node2priority_dict, node2idealx_dict)


def node2priority(nodes, from_targets):
    """
    優先度を各ノードに割り当てて、辞書を作成する。
    優先度についてはcalc_priority()にて説明している。
    Args:
        nodes: 優先度を割り当てたいノード
        from_targets: 優先度をターゲットから計算するかどうか。boolean。
    Return:
        {node: priority}となる辞書。key=Nodeオブジェクト, value=keyの優先度
    """
    return {node: calc_priority(node, from_targets) for node in nodes}


def calc_priority(node, from_targets):
    """
    ノードの優先度を返す
    優先度の計算
        ダミーノード：9999999999999999999999999999(大きい値)
        その他：ソースまたはターゲットの個数
    Args:
        node: 優先度を計算したいノード
        from_targets: ダミーノード以外において、Trueならtargetsから、Falseならsourcesから計算する。
    Return:
        計算結果　int
    """
    if node.is_dummy:
        return 9999999999999999999999999999
    return len(node.targets) if from_targets else len(node.sources)


def node2idealx(nodes, from_targets):
    """
    ノードにx座標の理想値を割り当てて、辞書で返す。
    理想値の計算についてはcale_idealx()にて説明している。
    Args:
        nodes: x座標の理想値を知りたいノード
        from_targets: ターゲットから理想値を計算するかどうか。bool。
    Return:
        key=Nodeオブジェクト, value=keyのx座標の理想値 となる辞書
    """
    return {node: calc_idealx(node, from_targets) for node in nodes}


def calc_idealx(node, from_targets):
    """
    ノードの理想のx座標を求める
    理想のx座標の計算
        (ターゲットから求める場合)
        ターゲットがある場合: ターゲットのx座標の平均値
        ない場合: ノードの元々のx座標
        (ソースから求める場合)
        ソースがある場合：ターゲットのx座標の平均値
        ない場合：ノードの元々のx座標
    Args:
        node: x座標の理想値を知りたいノード
        from_targets: ターゲットから計算するかどうか。bool。
    Return:
        計算結果(int)
    """
    # """
    if from_targets:
        return int(sum([target.x for target in node.targets]) / len(node.targets)) if len(node.targets) else node.x
    else:
        return int(sum([source.x for source in node.sources]) / len(node.sources)) if len(node.sources) else node.x
    # """
    """
    if from_targets:
        up_one_targets = [target for target in node.targets if calc_edge_height(node, target) == 1]
        return int(sum([target.x for target in up_one_targets]) / len(node.targets)) if len(up_one_targets) else node.x
    else:
        one_down_sources = [source for source in node.sources if calc_edge_height(node, source) == 1]
        return int(sum([source.x for source in one_down_sources]) / len(one_down_sources)) if len(one_down_sources) else node.x
    """


def update_idealx(node2idealx_dict):
    """
    上から下への座標決定の際、ノードの理想値を変更前座標とどちらがよいかを決める。
         ソースの方が多い：変更前の座標
         ターゲットの方が多い：理想値の座標(calc_idealx()の計算結果)
         ソースとターゲットが同数：変更前の座標と理想値の座標の平均値
    Args:
        node2idealx_dict: key=Node, value=keyの理想のx座標値 となる辞書。
    Return:
    """
    update_idealx_nodes = {}
    for node, idealx in node2idealx_dict.items():
        if node.is_dummy is True:
            update_idealx_nodes[node] = idealx  # idealxデモ良い？
        if len(node.targets) < len(node.sources):
            update_idealx_nodes[node] = node.x
        elif len(node.targets) == len(node.sources):
            update_idealx_nodes[node] = int((node.x + idealx) / 2)
    for node, idealx in update_idealx_nodes.items():
        node2idealx_dict[node] = idealx


def update_x_in_priority_order(nodes, node2priority_dict, node2idealx_dict):
    """
    1つの階層のノードのx座標の更新順序を決め、更新を行う。
    順序は優先度(priority)が大きい順とする。優先度が同じ場合は、x座標の値が小さいほうが先になる。
    更新は、update_x2idealx_recursively()にて行う。
    アルゴリズム
        1．与えられたnodesをx座標値で昇順にソートする
        2．ノードのx座標値を優先度が高い順に更新していく。
        3．更新したノードはその都度記録する。
    Args:
        nodes: 同階層のノードのリスト
        node2priority_dict: key=Nodeオブジェクト, value=優先度 となっている辞書
        node2idealx_dict: key=Nodeオブジェクト, value=理想のx座標値 となっている辞書
    Return:
    """
    assigned_nodes = []
    nodes = sorted(nodes, key=lambda a: a.x)
    for node, priority in sorted(node2priority_dict.items(), key=lambda a: (-a[1], a[0].x)):
        node_stack = Stack()
        node_stack.push(node)

        sign = 1 if node.x < node2idealx_dict[node] else -1  # if node.x > node2idealx_dict[node] else None
        # if sign:
        update_x2idealx_recursively(nodes.index(node), nodes, node2idealx_dict[node], node_stack, assigned_nodes, sign)
        """
        if node.x < node2idealx_dict[node]:
            update_x2idealx_recursively(node_index, nodes, node2idealx_dict[node], node_stack, assigned_nodes, sign=1)
        elif node.x > node2idealx_dict[node]:
            update_x2idealx_recursively(node_index, nodes, node2idealx_dict[node], node_stack, assigned_nodes, sign=-1)
        """
        assigned_nodes.append(node)


def update_x2idealx_recursively(node_index, same_level_nodes, ideal_x, node_stack, assigned_nodes, sign):
    """
    ノードのx座標を更新する。
    アルゴリズム
        1. 更新するノード(same_level_nodes[node_index])が、ノード列の端に到達していた場合、
           node_stackに入ったノードを理想x座標まで動かし、割り当てて、走査終了
        2. node_indexの隣のインデックスのノードを取得する
        3. 2で取得したノードのx座標が理想x座標よりも遠い場所にあった場合
            node_stackを理想x座標まで動かし、割り当てて、走査終了
        4. 2で取得したノードのx座標が理想x座標よりも近い、あるいは一致していた場合
            4.1 そのノードが割当済みノードならば、その1つ手前のx座標からnode_stack内のノードを並べる
            4.2 そのノードが割当済みでなければ、node_stackにそのノードを追加、更新するノードをそのノードにし、
                理想x座標を更新し、1に戻る。
    Args:
        node_index: x座標を更新したいノードのsame_level_nodesにおけるインデックス
        same_level_nodes: 操作を行う階層のノード(x座標値でソート済み)
        ideal_x: x座標を更新したいノードsame_level_nodes[node_index]の理想のx座標値
        assigned_nodes: 既に割り当てを行った、動かしたくないノードのリスト
        node_stack: 座標を更新している途中のノードが入ったスタック。
                    初期値としてsame_level_nodes[node_index]をプッシュしておく必要がある。
        sign: 理想x座標が今のx座標より大きいければ+1, 小さければ-1。
    Return:
    """
    if (node_index == 0 and sign == -1) or (node_index == len(same_level_nodes) - 1 and sign == 1):
        assign_x_in_sequence(node_stack, ideal_x, -sign)
        return

    next_node = same_level_nodes[node_index + sign]

    if (next_node.x > ideal_x and sign == 1) or (next_node.x < ideal_x and sign == -1):
        assign_x_in_sequence(node_stack, ideal_x, -sign)
        return
    else:
        if next_node in assigned_nodes:
            assign_x_in_sequence(node_stack, next_node.x - sign, -sign)
        else:
            node_stack.push(next_node)
            node_index += sign
            ideal_x += sign
            update_x2idealx_recursively(node_index, same_level_nodes, ideal_x, node_stack, assigned_nodes, sign)


def assign_x_in_sequence(node_stack, x, sign):
    """
    nodes_stack内のノードを空になるまでポップして、順にx座標を割り当てる。
    Args:
        node_stack: ノードが入ったスタック
        x: 最初popされるノードに割り当てるx座標の値
        sign: +1 or -1, +1: 順に増やしたい場合、-1: 順に減らしたい場合
    Return:
    """
    while node_stack.is_empty() is False:
        node = node_stack.pop()
        node.x = x
        x += sign


def assign_coordinate_by_means(nodes):
    """
    ノードのx座標を横幅の平均値で決定する
    """
    y2nodes = divide_nodes_by_level(nodes)
    max_width = 0
    # 最大幅を取得
    for y, nodes in y2nodes.items():
        if max_width < len(nodes):
            max_width = len(nodes)
    # 最大幅/その階層のノード数 をx座標として割り当てる
    for nodes in y2nodes.values():
        par_y = max_width / len(nodes)+1
        y = par_y
        for node in nodes:
            node.y = y
            y += par_y
"""
仕上げ
"""


def node_list_to_node_dict(node_list):
    """
    ノードについての情報（属性）をリスト形式から辞書形式に変換する。

    Args:
        node_list:全ノードをNodeクラスでまとめたリスト。

    Return:
        各ノードのname, href, x, y, is_dummyを持つ辞書。
        キーはnameで、その値としてhref, x, y, is_dummyをキーに持つ辞書が与えられる。
        例:
        node_dict = {"f": { "href": "example.html", "x": 0, "y": 2, "is_dummy": false}, ... }
    """
    node_dict = {}
    for node in node_list:
        node_dict[node.name] = {
            "href": node.href,
            "x": node.x,
            "y": node.y,
            "is_dummy": node.is_dummy
        }
    return node_dict


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


def move_isolated_node(all_nodes):
    """
    孤立したノードをグラフの頂上ノードの右に移動させる。
    Args:
        all_nodes: 全てのノード
    Return:
    """
    x_coordinate_of_top_node = 0
    for node in all_nodes:
        if len(node.targets) == 0 and len(node.sources) > 0:  # 頂上のノードの検索
            if x_coordinate_of_top_node < node.x:
                x_coordinate_of_top_node = node.x
    for node in all_nodes:
        if len(node.targets) == 0 and len(node.sources) == 0:  # 孤立したノードの検索
            node.x = x_coordinate_of_top_node + 1
            x_coordinate_of_top_node += 1


def move_graph(all_nodes):
    move_x = 0
    for node in all_nodes:
        if len(node.targets) == 0 and len(node.sources) > 0:
            move_x = node.x
    for node in all_nodes:
        node.x -= move_x


"""
グラフの中心を探る
"""

def calc_average_length_node2node(nodes):
    """
    各ノードのそれ以外のノード間の距離の平均値をとる
    """
    node2average_length = dict()
    for n in nodes:
        total_length = 0
        for m in nodes:
            if n != m:
                total_length += calc_length_node2node(n, m)
        node2average_length[n.name] = (len(nodes)-1) / total_length

    return node2average_length


def calc_length_node2node(from_node, to_node):
    """
    ノード間の距離を計算する
    """
    return pow(from_node.x - to_node.x, 2) + pow(from_node.y - to_node.y, 2)


def calc_nodes_center(node):
    """
    ノードとその接続ノードの座標から、それらのノードの中心(重心)を計算する。
    ココでの重心Cは、各ノードのx座標、y座標の平均値を重心とする。
    """
    node_num = 1
    center_x = node.x
    center_y = node.y

    for target in node.targets:
        center_x += target.x
        center_y += target.y
        node_num += 1

    for source in node.sources:
        center_x += source.x
        center_y += source.y
        node_num += 1

    center_x = center_x / node_num
    center_y = center_y / node_num

    return (center_x, center_y)
    

def calc_graph_center(all_nodes):
    """
    グラフの重心座標を返す
    """
    center_x, center_y = 0.0, 0.0
    for node in all_nodes:
        center_x += node.x
        center_y += node.y

    center_x = center_x / len(all_nodes)
    center_y = center_y / len(all_nodes)

    return (center_x, center_y)


def calc_distance_from_nodescenter_to_graphcenter(nodes_center, graph_center):
    """
    グラフの重心からノードの重心までの距離を計算して返す
    """
    return pow((graph_center[0] - nodes_center[0]), 2) + pow((graph_center[1] - nodes_center[1]), 2)

"""
グラフの中心を探る おわり
"""

"""
自身の参照を取り除く
"""
def remove_reference_myself(nodes):
    for node in nodes:
        if node in node.targets:
            node.targets.remove(node)
        if node in node.sources:
            node.sources.remove(node)


"""
nodeインスタンスから，networkx.draw_networkxで扱える
posを作る．
posとは，グラフのノードの位置を決定する辞書である．
keyはノード名(str)，valueはarray([x座標, y座標])
"""
def create_networkx_pos_from_node(nodes):
    node_pos = dict()
    for node in nodes:
        node_pos[node.name] = (node.x, node.y)
    return node_pos


def create_graph(select_categories, layout='sfdp'):  # ['bipartite', 'circular', 'kamada_kawai', 'planar', 'random', 'shell', 'spring', 'spectral', 'spiral', 'multipartite']:
    """
    関数の実行を行う関数。

    Args:
        select_categories: 依存関係を知りたいカテゴリを示すjsonファイル

    Return:
    """

    def shuffle_dict(d):
        """
        辞書（のキー）の順番をランダムにする
        Args:
            d: 順番をランダムにしたい辞書。
        Return:
            dの順番をランダムにしたもの
        """
        random.seed(0)
        keys = list(d.keys())
        random.shuffle(keys)
        return dict([(key, d[key]) for key in keys])

    """
       input_node_dict: 全ノードについての情報を辞書にまとめたもの。dict()
           key: ノードの名前。
           value: リスト
               第1要素: keyのノードが指すノードの集合。set()
               第2要素: keyのノードのリンク先URL。str()

    """
    # mizarライブラリから依存関係のデータを取得
    lib_dict = retrieve_environment.make_library_dependency()
    lib_dict = retrieve_environment.make_marge_category2article_dependency(lib_dict, select_categories)
    lib_dict = retrieve_environment.merge_category2article_dependency(lib_dict)
    
    # theoremを取得
    with open('nodes.json', 'r') as f:
        print('json no yomikomi')
        #lib_dict = json.load(f)    # ここのコメントを外すと，nodes.jsonを読み込みます
    input_node_dict = lib_dict
    print(len(input_node_dict))

    node_list = create_node_list(shuffle_dict(input_node_dict))

    # 自身の参照を取り除く
    remove_reference_myself(node_list)
    print("remove myself")
    
    # 余分の間引きを行う
    pluck_waste_edges(node_list)
    print('plunk waste edges')

    if layout=='layered':
        # レベルを決定する。なにも参照していないノードが一番上にくる。
        assign_level(node_list)
        print('assign level')

        # ダミーノードの生成
        #"""
        cut_edges_higher_than_1(node_list)
        assign_x_sequentially(node_list)
        print('create dummy node')
        #"""

        # 交差削減50回
        reduce_cross(50, node_list) 
        print("reduce_cross")

        # ダミーノードの削除
        #"""
        node_list = delete_dummy(node_list)
        leave_no_space(node_list)
        print("remove dummy")
        #"""

        # 座標割り当て
        assign_coordinate(2, node_list)
        #assign_coordinate_by_means(node_list)
        print('assign coordinate')
        
        # 孤立ノードの座標を割り当て
        move_isolated_node(node_list) 


    elif layout=='spring':
        """
        spectral layoutの実装
        """
        # node_list = remove_alone_nodes(node_list)
        # nodes_pos = change_layout.assign_nodes_position_in_spcetral_layout(node_list) # spectral layout 800 800
        nodes_pos = change_layout.assign_nodes_position_in_spring_layout(node_list)  # spring layout 150 150
        # nodes_pos = change_layout.assign_nodes_position_in_kamada_layout(node_list)  # kamada kawai layout 150 150
        change_layout.update_nodes_position(node_list, nodes_pos, ratio=150)

        """
        ここまで
        """

    elif layout in ['dot', 'twopi', 'fdp', 'sfdp', 'circo', 'neato']:
        ratio = 1
        nodes_pos = change_layout.change_layout_for_graphviz_layout(node_list, layout)  # spring layout 150 150
        if layout == 'dot':
            ratio = 0.008
        elif layout == 'twopi':  # 動かない
            ratio = 0.08
        elif layout == 'neato':
            ratio = 0.1
        elif layout == 'fdp':  # 動かない
            ratio = 0.1
        elif layout == 'sfdp':
            ratio = 0.1
        elif layout == 'circo':  # 動かない
            ratio = 0.1
        change_layout.update_nodes_position(node_list, nodes_pos, ratio=ratio)

    elif layout in ['bipartite', 'circular', 'kamada_kawai', 'planar', 'random', 'shell', 'spring', 'spectral', 'spiral', 'multipartite']:
        ratio = 1
        nodes_pos = change_layout.change_layout_for_networkx_layout(node_list, layout)
        if layout == 'bipartite':
            ratio = 1
        elif layout == 'planar':
            ratio = 1
        elif layout == 'kamada_kawai':
            ratio = 1000
        change_layout.update_nodes_position(node_list, nodes_pos, ratio=0.008)

    else:
        print("error")
        return "error"
    
    
    # ノードの名前、座標等をnetworkxで扱えるように辞書形式に変換
    node_attributes = node_list_to_node_dict(node_list)
    
    # 有向グラフGraphの作成
    graph = nx.DiGraph()

    create_dependence_graph(node_list, graph)
    
    # nodes_attrsを用いて各ノードの属性値を設定
    nx.set_node_attributes(graph, node_attributes)

    # cytoscape.jsの記述形式(JSON)でグラフを記述
    graph_json = nx.cytoscape_data(graph, attrs=None)
    
    with open(GRAPH_DIR + '/' + layout + '_theorem_graph.json', 'w') as f_out:
        json.dump(graph_json, f_out)
    

    """
    以下，画像(svg)出力
    """
    plt.figure(figsize=(200.0,100.0))
    #pos = nx.spring_layout(graph, seed=1)
    #pos = nx.circular_layout(graph)
    pos = create_networkx_pos_from_node(node_list)
    nx.draw_networkx(graph, pos=pos)
    plt.savefig('layered_theorem_graph.svg', format="svg")

    return graph_json
