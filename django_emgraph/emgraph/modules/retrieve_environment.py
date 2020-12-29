import os
import glob
from pathlib import Path
import re
from collections import defaultdict
from mizar_graph.settings import BASE_DIR

MML_DIR = BASE_DIR + "/mizar_graph/static/mml/"
CURRENT_DIR = BASE_DIR + "/emgraph/modules/"
CATEGORIES = ['vocabularies', 'constructors', 'notations', 'registrations', 'theorems', 'schemes',
              'definitions', 'requirements', 'expansions', 'equalities']

from pprint import pprint


class Mizar_file:
    """
    articleファイル(.mizファイル)の参照しているファイル、および自身のURLを
    Attributes:
        name: 自身のファイルの名前. str().
        dependency_articles: 参照しているファイル群. set()
        url: 自身のファイルのURL. str()
    """
    def __init__(self, name, dependency_articles, url):
        self.name = name
        self.dependency_files = dependency_articles
        self.url = url


def make_library_dependency(*args):
    """
    各カテゴリ内で参照しているファイルを取得する。
    Return:
        article2dependency_articles: 各カテゴリ(vocabularies, constructors等)において、各ライブラリが
                       どのライブラリを参照しているかを示す辞書。
                       例：lib_aがlib_x, lib_y, ... を参照している場合、
                        article2dependency_articles = {
                            'vocabularies': {
                                'lib_a': {'lib_x', 'lib_y', ...},
                                'lib_b': {'lib_o', 'lib_p', ...},
                                ...
                            }
                            'constructors': { ... },
                            ...
                        }
    """
    article2dependency_articles = dict()
    categories = ['vocabularies', 'constructors', 'notations', 'registrations', 'theorems', 'schemes',
                  'definitions', 'requirements', 'expansions', 'equalities']
    for category in categories:
        article2dependency_articles[category] = dict()
    try:
        os.chdir(MML_DIR)
        article_files = glob.glob("*.miz")  # mmlディレクトリの.mizファイルを取り出す
        for article_file in article_files:
            category2reference_articles = create_key2list(categories)
            with open(article_file, 'rt', encoding="utf-8", errors="ignore") as f:
                strings = f.read()
            category2reference_articles = extract_articles(strings)
            update_miz_file2library(article_file, category2reference_articles, article2dependency_articles)
    finally:
        os.chdir(CURRENT_DIR)
    return article2dependency_articles


def extract_articles(contents):
    """
    mizファイルが環境部(environ~begin)で参照しているarticleを
    各カテゴリごとに取得する。
    Args:
        contents: mizファイルのテキスト
    Retrun:
        category2articles: keyがカテゴリ名、valueが参照しているarticleのリスト
    """
    category2articles = create_key2list(CATEGORIES)
    # 単語、改行、::、;で区切ってファイルの内容を取得
    file_words = re.findall(r"\w+|\n|::|;", contents)
    is_comment = False
    environ_words = list()

    # mizファイルから環境部を抜き出す
    for word in file_words:
        # コメント行の場合
        if word == "::" and not is_comment:
            is_comment = True
            continue
        # コメント行の終了
        if re.search(r"\n", word) and is_comment:
            is_comment = False
            continue
        # コメント以外の部分(environ ~ beginまで)
        if not is_comment:
            environ_words.append(word)
            # 本体部に入ったら、ループから抜け出す
            if re.match(r"begin", word):
                break

    # 改行文字の削除
    environ_words = [w for w in environ_words if not re.match(r"\n", w)] 

    # カテゴリでどのarticleを参照しているかを得る
    category_name = str()
    for word in environ_words:
        # 環境部の終了条件
        if re.match(r"begin", word):
            break
        # カテゴリ名が来たとき
        if word in category2articles.keys():
            category_name = word
            continue
        # ;でそのカテゴリでの参照が終わったとき
        if re.match(r";", word):
            category_name = str()
            continue
        # カテゴリ名が決まっているとき
        if category_name:
            category2articles[category_name].append(word)
        
    return category2articles


def create_key2list(keys):
    """
    keyがkeys，valueがlist()の辞書を作成する．
    Args:
        keys: keyに設定したい値(リスト)
    return:
        key2list: keyがkeys，valueがlist()の辞書
    """
    key2list = dict()
    for i in keys:
        key2list[i] = list()
    return key2list


def update_miz_file2library(article_file, category2article_files, article2dependency_articles):
    """
    create_graph.pyでinputとして使えるような辞書を作成する
    各ファイルのURLの設定，およびarticleのノードを作成する．
    Args:
        miz_file: mizarファイル名
        category2article_files: key=カテゴリー名, value=keyで参照するライブラリ名 の辞書
        miz_files_dict: key=カテゴリー名, value=miz_fileの辞書。
                    このvalueをkeyとし、そのvalueにcategory2article_filesのvalueが格納される。
    Return:
    """
    article_name = set_file_name(article_file)
    url = set_file_url(article_file)

    # article2dependency_articlesの作成
    for category, article_files in category2article_files.items():
        article2dependency_articles[category][article_name] = \
            {"dependency_articles": set(article_files), "url": url}
        # {"dependency_articles": 参照しているファイル群, "url": このファイルのURL]
    return article2dependency_articles


def set_file_name(article_file):
    """
    articleの名前をファイル名から，mizファイル内のテキスト形式にする．
    例：tarski.miz -> TARSKI

    Args:
        miz_file: articleのファイル名

    Return:
        mizファイル内のテキスト形式になった文字列
    """
    article_name = article_file.upper()
    article_name = article_name.replace('.MIZ', '')
    return article_name


def set_file_url(miz_file):
    """
    各ファイルへのリンクを設定する．

    Args:
        miz_file: articleのファイル名

    Return:
        mizファイルへのパス
    """
    #return str(os.getcwd()) + "\\" + miz_file
    return "http://www.mizar.org/version/current/html/" + miz_file.rstrip('miz') + 'html'


def make_marge_category2article_dependency(category2article_files, select_categories):
    """
    category_dictから特定のカテゴリの辞書のみ抜粋する．
    Args:
        miz_files_dict: 各カテゴリにおいて、どのファイルがどのファイルを参照しているかを示す辞書
        select_categories: マージしたいカテゴリー名たち
    Return:
        select_dict: マージしたいカテゴリのみをmiz_files_dictから抽出した辞書
    """
    select_category2article_files = dict()
    for k in select_categories:
        select_category2article_files[k] = category2article_files[k]
    return select_category2article_files


def merge_category2article_dependency(merge_category_dict):
    """
    辞書をマージする．
    アルゴリズム
        1．各カテゴリでのファイル群(miz_files)を取得
        2．1で取得したファイル(lib)が参照しているライブラリ(article)を取得
        3. libが同名の物をまとめる
    Args:
        merge_category_dict: マージしたいカテゴリーの辞書
    Return:
        merge_dict:
    """
    merge_dict = dict()
    for miz_files in merge_category_dict.values():
        for article, attribute in miz_files.items():
            if article not in merge_dict.keys():
                merge_dict[article] = {"dependency_articles": set(), "url": attribute["url"]}
            merge_dict[article]["dependency_articles"] |= attribute["dependency_articles"]
    return merge_dict


def mizar_dict_to_mizar_list(files_dict):
    """
    キーがファイル名、値が辞書{"dependency_articles": , "url": }の辞書をMizar_fileオブジェクトのリストにする。
    files_dict = { article_name:{ "dependency_articles": set(参照しているarticle群), "url": 自身のURL}}
    ↓
    mizar_file_list = [article]
     (article: Mizar_fileオブジェクト, article.dependency_articles: 参照しているarticle群, article.url: 自身のURL)
    Args:
        files_dict:
    Return:

    """
    mizar_file_list = list()
    for k in files_dict.keys():
        mizar_file_list.append(Mizar_file(name=k, dependency_articles=k["dependency_articles"], url=k["url"]))
    return mizar_file_list


def main():
    """
    実行関数
    Return:
    """
    library_dict = make_library_dependency()


if __name__ == '__main__':
    main()
