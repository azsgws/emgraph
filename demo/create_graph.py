"""
依存関係を階層形式で表示する
・階層化の手順
　　1. 階層割当
　　2. 交差削減
　　3．座標決定
"""
import networkx as nx
import json


class Node:
    """
    ノードをクラスとして定義する。

    Attributes:
        name: ノードの名前。str()。
        target_nodes: 自身が指しているノードの集合。set()。
        source_nodes: 自身を指しているノードの集合。set()。
        x, y: ノードの座標(x,y)。ともにint()。
        href: ノードのリンク。str()。
        is_dummy: ノードがダミーか否か。bool()。
    """
    def __init__(self, name, target_nodes, source_nodes, x, y, href, is_dummy):
        self.name = name
        self.target_nodes = target_nodes
        self.source_nodes = source_nodes
        self.x = x
        self.y = y
        self.href = href
        self.is_dummy = is_dummy

    def __str__(self):
        name = self.name
        target_nodes = self.target_nodes
        source_nodes = self.source_nodes
        x = self.x
        y = self.y
        return f"name: {name}, target_nodes: {target_nodes}, source_nodes: {source_nodes}, (x, y)= ({x}, {y})"


def create_node_list():
    """
    input_node_dictをNodeクラスでインスタンス化したものをリストにまとめる。
    各属性には次の物を格納する。
        ・name:  input_node_dictのkey。str。
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
    node_list = []
    node_dict = {}
    # node_dict, node_listの作成
    for k, v in input_node_dict.items():
        n = Node(k, set(), set(), -1, -1, v[1], False)
        node_dict[k] = n
        node_list.append(n)
        
    # target_nodesの作成
    for k, v in input_node_dict.items():
        for target in v[0]:
            node_dict[k].target_nodes.add(node_dict[target])
            
    # source_nodesの作成
    for k, v in node_dict.items():
        for target in v.target_nodes:
            target.source_nodes.add(node_dict[k])

    return node_list


def main():
    """
    関数の実行を行う関数。

    Return:
    """
    import random

    def shuffle_dict(d):
        """
        辞書（のキー）の順番をランダムにする

        Args:
            d: 順番をランダムにしたい辞書。

        Return:
            dの順番をランダムにしたもの
        """
        keys = list(d.keys())
        random.shuffle(keys)
        [(key, d[key]) for key in keys]
        random.shuffle(keys)
        [(key, d[key]) for key in keys]
        random.shuffle(keys)
        keys = [(key, d[key]) for key in keys]
        return dict(keys)

    """
       input_node_dict: 全ノードについての情報を辞書にまとめたもの。dict()
           key: ノードの名前。
           value: リスト
               第1要素: keyのノードが指すノードの集合。set()
               第2要素: keyのノードのリンク先URL。str()

    """
    input_node_dict = {"a": [set(), "example.html"],
                       "b": [{"a"}, "example.html"],
                       "c": [{"b", "e"}, "example.html"],
                       "d": [{"c", "a"}, "example.html"],
                       "e": [{"a"}, "example.html"],
                       "f": [{"e", "b", "a"}, "example.html"],
                       "g": [{"e"}, "example.html"],
                       "h": [{"g", "f"}, "example.html"],
                       "i": [{"a"}, "example.html"],
                       "j": [{"i"}, "example.html"],
                       "k": [{"j", "m"}, "example.html"],
                       "l": [{"i", "a"}, "example.html"],
                       "m": [{"i"}, "example.html"],
                       "n": [{"j", "m"}, "example.html"],
                       "o": [{"m", "l"}, "example.html"],
                       "p": [{"n", "k"}, "example.html"],
                       "q": [{"k", "o", "i"}, "example.html"],
                       }

    node_list = create_node_list(shuffle_dict(input_node_dict))

    
if __name__ == "__main__":
    main()
    
