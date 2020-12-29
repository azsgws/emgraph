import math
import matplotlib.pyplot as plt
import csv

def calc_distance_of_node_to_node(start, goal):
    """
    2ノード間の2乗距離を返す
    params:
        start: 始点ノード
        goal: 終点ノード
    """
    return math.sqrt(pow(goal.x - start.x, 2) + pow(goal.y - start.y, 2))

    
def calc_length_node_to_source(start_nodes, depth=1):
    """
    ノードとソースの距離を計算する
    深さは何世代先まで見るかを設定する
    """
    if type(start_nodes) is not list:
        start_nodes = [start_nodes]

    source2length = dict()
    from_node = start_nodes[-1]
    start_nodes_name = [n.name for n in start_nodes]

    for source in from_node.sources:
        key = start_nodes_name + [source.name]
        source2length[tuple(key)] = calc_distance_of_node_to_node(start_nodes[0], source)
    if depth > 1:
        for source in from_node.sources:
            source2length.update(calc_length_node_to_source(start_nodes+[source], depth=depth-1))

    return source2length



def calc_length_node_to_target(start_nodes, depth=1):
    """
    ノードとターゲットの距離を計算する
    深さ(depth)は何世代先まで見るかを設定する
    """
    if type(start_nodes) is not list:
        start_nodes = [start_nodes]

    target2length = dict()
    from_node = start_nodes[-1]
    start_nodes_name = [n.name for n in start_nodes]

    for target in from_node.targets:
        key = start_nodes_name + [target.name]
        target2length[tuple(key)] = calc_distance_of_node_to_node(start_nodes[0], target)
    if depth > 1:
        for target in from_node.targets:
            target2length.update(calc_length_node_to_target(start_nodes+[target], depth=depth-1))

    return target2length


def calc_distance_average(connect_node2length):
    """
    接続されたノードとの距離の平均を返す
    たどるノードの個数別に分ける
    """
    len2distance = create_len2distance(connect_node2length)
    len2average_distance = dict()
    for k, v in len2distance.items():
        len2average_distance[k] = calc_average(v)
    return len2average_distance


def calc_variance(connect_node2length):
    """
    ノードをたどった数別に分散を計算する
    """
    len2distance = create_len2distance(connect_node2length)  # 各ノード数における距離
    len2average_distance = calc_distance_average(connect_node2length)  # 各ノード数における平均値
    node2variance = dict()
    variance = dict()
    for k, v in len2distance.items():
        total = 0
        for distance in v:
            total += pow(distance - len2average_distance[k], 2)
        variance[k] = total / len(v)

    return variance
    

def calc_min(connect_node2length):
    """
    ノードをたどった数別に最小値を返す
    """
    len2distance = create_len2distance(connect_node2length)  # 各ノード数における距離
    len2min_distance = dict()
    for k in len2distance.keys():
        len2min_distance[k] = min(len2distance[k])
    return len2min_distance


def calc_max(connect_node2length):
    """
    ノードをたどった数別に最大値を返す
    """
    len2distance = create_len2distance(connect_node2length)  # 各ノード数における距離
    len2max_distance = dict()
    for k in len2distance.keys():
        len2max_distance[k] = max(len2distance[k])
    return len2max_distance


def create_len2distance(tuple2value):
    """
    {tuple: value}の辞書でtupleの長さが同じものをまとめる。
    valueはリスト形式にしてまとめる。

    return: {1: [value1, value2, ...], 2: [value1, value2, ...], ....}
    """
    
    tuple_len2value = dict()
    for k, v in tuple2value.items():
        if len(k)-1 not in tuple_len2value.keys():
            tuple_len2value[len(k)-1] = list()
        tuple_len2value[len(k)-1].append(v)

    return tuple_len2value


def calc_average(numbers):
    """
    numbers: 数字の配列。list()。
    """
    total = 0
    for n in numbers:
        total += n
    average = total / len(numbers)

    return average
    

def remove_items_from_tuple2values(tuple2values):
    """
    タプルで最後の値が同じやつを取り除く
    タプルの長さが違う場合は短い方を採用
    """
    copy_keys = create_key2float(tuple2values)
    key_remove = list()
    for k1 in tuple2values.keys():
        for k2 in copy_keys.keys():
            if (k1!=k2) and (k1[-1]==k2[-1]):
                if len(k1)>len(k2) and (k1 not in key_remove):
                    key_remove.append(k1)
                elif k2 not in key_remove:
                    key_remove.append(k2)
                """
                print("-------------****************--------")
                print(k1)
                print(tuple2values[k1])
                print(k2)
                print(tuple2values[k2])
                """
    
    for k in key_remove:
        tuple2values.pop(k)

    return tuple2values


def create_hakohige(file_name, num2list):
    """
    数字のデータから箱ひげ図を作る
    """
    with open(file_name, "w") as f:
        fig, ax = plt.subplots()
        bp = ax.boxplot(tuple(num2list.values()))
        ax.set_xticklabels(list(num2list.keys()))
        plt.xlabel("number of edge from start to target")
        plt.ylabel("distance")
        plt.ylim([0,70])
        plt.grid()
        plt.savefig(file_name)


def create_key2float(key2values):
    key2float = dict()
    for k in key2values:
        key2float[k] = 0.0
    return key2float


def create_ave_distance_csv(node_name, node_len2distance_ave):
    output_dict = dict()
    output_dict.update({"node_name": node_name})
    output_dict.update(node_len2distance_ave)
    with open("distance_of_ave(target).csv", "a") as f:
        fieldnames = ["node_name", 1, 2, 3, 4, 5]
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=",", quotechar='"')
        writer.writerow(output_dict)


def create_variance_distance_csv(node_name, node_len2distance_variance):
    output_dict = dict()
    output_dict.update({"node_name": node_name})
    output_dict.update(node_len2distance_variance)
    with open("distance_of_variance(target).csv", "a") as f:
        fieldnames = ["node_name", 1, 2, 3, 4, 5]
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=",", quotechar='"')
        writer.writerow(output_dict)
