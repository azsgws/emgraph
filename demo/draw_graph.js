/*
createGraph.pyで出力されたファイルとcytoscape.jsを使って
グラフの描画を行う
*/
$(function(){
    $.getJSON("./demo_sample.json", function(graph_data) {
        //描画(graph_draw()をここに書き写す)
        // cytoscapeグラフの作成(初期化)
        let cy = cytoscape({
            container: document.getElementById('demo'),
            elements: [],

            boxSelectionEnabled: true,
            autounselectify: false,
            selectionType: "additive"
        });
        // グラフにノードを追加
        for(let data in graph_data["elements"]["nodes"]){
            for(let component in graph_data["elements"]["nodes"][data]){
                cy.add({
                    group: "nodes",
                    data:{
                        id: graph_data["elements"]["nodes"][data][component]["id"],
                        name: graph_data["elements"]["nodes"][data][component]["name"],
                        dummy: graph_data["elements"]["nodes"][data][component]["dummy"],
                        href: graph_data["elements"]["nodes"][data][component]["href"]
                    },
                    position:{
                        x: graph_data["elements"]["nodes"][data][component]["x"] * 200,
                        y: graph_data["elements"]["nodes"][data][component]["y"] * 200
                    }
                });
            }
        }
        // グラフにエッジを追加
        for(let data in graph_data["elements"]["edges"]){
            for(let component in graph_data["elements"]["edges"][data]){
                cy.add({
                    group: "edges",
                    data:{
                        source: graph_data["elements"]["edges"][data][component]["source"],
                        target: graph_data["elements"]["edges"][data][component]["target"]
                    }
                })
            }
        }
        // グラフのスタイルを決定
        cy.style([
            /* 初期状態のスタイル */
            {
                selector: "node",
                css: {"background-color": "red", "shape": "ellipse", "width": 100, "height": 100,
                      "content": "data(name)", "font-size": 30, "opacity": 0.8, "z-index": 1,
                      "text-halign":"center", "text-valign": "center", "font-style": "normal",
                      "font-weight": "bold",
                      "z-index": 1}
            },
            {
                selector: "edge",
                css: {"line-color": "black", "target-arrow-shape": "triangle", "curve-style": "straight",
                "target-arrow-color": "black", "arrow-scale": 3, "width": 5, "opacity": 0.2, "z-index": 1}
            },
            /* ノードが左クリックされたときに適応されるスタイル */
           // 選択された(強調表示する)ノード全てのスタイル
            {
                selector: "node.highlight",
                css: {"font-size": 50,  "width": 170, "height": 170,
                "content": "data(name)", "opacity": 1, "z-index": 10}
            },
            // 選択(左クリック)されたノードのスタイル
            {
                selector: "node.selected",
                css: {"background-color": "#ff0000", "width": 200, "height": 200}
            },
            // 選択された(強調表示する)祖先のスタイル
            {
                selector: "node.selected_ancestors0",
                css: {"background-color": "#ff00ff"}
            },
            {
                selector: "node.selected_ancestors1",
                css: {"background-color": "#dd00ff"}
            },
            {
                selector: "node.selected_ancestors2",
                css: {"background-color": "#bb00ff"}
            },
            {
                selector: "node.selected_ancestors3",
                css: {"background-color": "#9900ff"}
            },
            {
                selector: "node.selected_ancestors4",
                css: {"background-color": "#7700ff", "color": "#aaaaaa"}
            },
            {
                selector: "node.selected_ancestors5",
                css: {"background-color": "#5500ff", "color": "#aaaaaa"}
            },
            {
                selector: "node.selected_ancestors6",
                css: {"background-color": "#2f00ff", "color": "#aaaaaa"}
            },
            {
                selector: "node.selected_ancestors7",
                css: {"background-color": "#0000ff", "color": "#aaaaaa"}
            },
            {
                selector: "node.selected_ancestors8",
                css: {"background-color": "#0000dd", "color": "#aaaaaa"}
            },
            {
                selector: "node.selected_ancestors9",
                css: {"background-color": "#0000bb", "color": "#aaaaaa"}
            },
            // 選択された(強調表示する)子孫のスタイル
            {
                selector: "node.selected_descendants0",
                css: {"background-color": "#ffff00"}
            },
            {
                selector: "node.selected_descendants1",
                css: {"background-color": "#ddff00"}
            },
            {
                selector: "node.selected_descendants2",
                css: {"background-color": "#bbff00"}
            },
            {
                selector: "node.selected_descendants3",
                css: {"background-color": "#99ff00"}
            },
            {
                selector: "node.selected_descendants4",
                css: {"background-color": "#77ff00"}
            },
            {
                selector: "node.selected_descendants5",
                css: {"background-color": "#44ff00"}
            },
            {
                selector: "node.selected_descendants6",
                css: {"background-color": "#00ff00"}
            },
            {
                selector: "node.selected_descendants7",
                css: {"background-color": "#00ff44"}
            },
            {
                selector: "node.selected_descendants8",
                css: {"background-color": "#00ff77"}
            },
            {
                selector: "node.selected_descendants9",
                css: {"background-color": "#00ff99"}
            },
            // 強調表示されたノードをつなぐエッジのスタイル
            {
                selector: "edge.highlight",
                css: {"line-color": "#006400", "curve-style": "straight",
                "target-arrow-color": "#006400", "arrow-scale": 3, "width": 3, "opacity": 1, "z-index": 20}
            },
            // 選択されていないノードとエッジのスタイル
            {
                selector: ".not_highlight",
                css: {"opacity": 0.05, "z-index": 0}
            }
        ]);
        
        
        // 強調表示する祖先、子孫の世代数の初期化
        let ancestor_generations = 1
        let descendant_generations = 1
        
        
        /* 検索機能の追加 */
        // 全ノード(article)名の取得
        let all_article_name = [];
        cy.nodes("[!is_dummy]").forEach(function(node){
            all_article_name.push(node.data("name"));
        });
        all_article_name.sort();
        // datalistに全ノード名を追加
        for (let article_name of all_article_name){
            $("#article_list").append($("<option/>").val(article_name).html(article_name));
        }
        
        
        // 強調表示したい祖先、子孫の世代数を取得
        $("#ancestor_generations").on("change", function(){
            ancestor_generations = $("#ancestor_generations").val();
        });
        $("#descendant_generations").on("change", function(){
            descendant_generations = $("#descendant_generations").val();
        });
        
        
        // ノードをクリックした場合、リンクに飛ぶ(htmlリンクの設定)
        cy.on("tap", "node", function(){
            try {
                window.open(this.data("href"));
            } catch(e){
                window.location.href = this.data("href");
            }
        });

    });
});


/**
 * グラフの要素のスタイルを初期状態(ノード：赤い丸、エッジ：黒矢印)に戻す。
 * ただし、移動したノードの位置は戻らない。
 * @param {cytoscape object} cy cytoscapeのグラフ本体
 * @return
**/
function reset_elements_style(cy) {
    let all_class_names = ["highlight",  "not_highlight",  "selected"];
    for(let i=0; i<10; i++){
        all_class_names.push("selected_ancestors" + i);
        all_class_names.push("selected_descendants" + i);
    }
    cy.elements().removeClass(all_class_names);
    cy.nodes().unlock();
}


/**
 * 選んだ1つのノードに近づく、焦点を当てる。
 * @param {cytoscape object} cy: cytoscapeグラフ本体
 * @param {cytoscape object} selected_node: cyの単一のノード。近づきたいノード。
 * @return
**/
function focus_on_selected_node(cy, selected_node){
    cy.animate({
        fit:{
            eles: selected_node,
            padding: 450
        }
    });
}


/**
 * 選択したノード(select_node)とその祖先または子孫を任意の世代数(generations)までを
 * 強調表示するクラスに追加する。
 * アルゴリズム
 *      次の処理を辿りたい世代数まで繰り返す
            1. node_to_get_connectionの親(もしくは子)ノードとそのエッジを強調表示させるクラスに追加する
            2. 1でクラスに追加したノードをnode_to_get_connectionとして更新する
            3. 2でnode_to_get_connectionが空ならループを中断する
 * @param {cytoscape object} cy cytoscapeのグラフ本体
 * @param {int} generations 辿りたい世代数
 * @param {cytoscape object} select_node 選択したノード
 * @param {boolean} is_ancestor 辿りたいのは祖先かどうか。trueなら祖先、falseなら子孫を強調表示させていく。
 * @return
**/
function highlight_connected_elements(cy, generations, select_node, is_ancestor){
    let node_to_get_connection = cy.collection();  // 親(もしくは子)を取得したいノードのコレクション（≒リスト）
    node_to_get_connection = node_to_get_connection.union(select_node);
    for (let i=0; i<generations; i++){
        let class_name = is_ancestor ? "selected_ancestors" : "selected_descendants";
        class_name += Math.min(9, i);
        let next_node_to_get_connection = cy.collection();
        cy.$(node_to_get_connection).forEach(function(n){
            let connect_elements = is_ancestor ? n.outgoers() : n.incomers();
            connect_elements = connect_elements.difference(cy.$(connect_elements).filter(".highlight"));
            cy.$(connect_elements).addClass("highlight");
            cy.$(connect_elements).nodes().addClass(class_name);
            next_node_to_get_connection = next_node_to_get_connection.union(connect_elements.nodes());
        });
        node_to_get_connection = next_node_to_get_connection;
        if (node_to_get_connection.length === 0){
            break;
        }
    }
}

