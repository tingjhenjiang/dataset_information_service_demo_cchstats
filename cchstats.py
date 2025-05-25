# %%
from flask import Flask, request, jsonify, send_file
from flask import render_template
import matplotlib.pyplot as plt
import io
import os
import pandas as pd
from sklearn import tree
from pathlib import Path
import json
import ast
# %%
# 找出程式檔所在目錄
parent_folder = Path(__file__).parent
# 指定資料集封裝檔案路徑
dataset_file = parent_folder  / 'ChenChiehHsien2024P12PlayLog.xlsx'
# 讀取資料集封裝檔案
cch_batting_stats = pd.read_excel(dataset_file)

# 把壘上有人的情形分別轉換為 1壘是否有人 2壘是否有人 3壘是否有人 的特徵
runnersOnBasedf = pd.DataFrame.from_dict({
    'runnersOnBase':  [0,1,2,3,12,13,23],
    'runnersOnBase1': [0,1,0,0,1, 1, 0],
    'runnersOnBase2': [0,0,1,0,1, 0, 1],
    'runnersOnBase3': [0,0,0,1,0, 1, 1],
})
cch_batting_stats = cch_batting_stats.merge(runnersOnBasedf, how='left', on='runnersOnBase')
cch_batting_stats.loc[cch_batting_stats['runnersOnBase']!=0,'runnersOnBase'] = 1 # 將壘上有人的情形統一為1，無人則為0
# 把投手所屬聯盟的情形分別轉換為 是否為Fgn 是否為Ind 是否為A+ 是否為AA 是否為AAA 的特徵
pitcherLeagueDf = pd.DataFrame.from_dict({
    'pitcherLeague':    ['Fgn', 'Ind', 'A+', 'AA', 'AAA'],
    'pitcherLeagueFgn': [1,0,0,0,0],
    'pitcherLeagueInd': [0,1,0,0,0],
    'pitcherLeagueA+':  [0,0,1,0,0],
    'pitcherLeagueAA':  [0,0,0,1,0],
    'pitcherLeagueAAA': [0,0,0,0,1],
})
cch_batting_stats = cch_batting_stats.merge(pitcherLeagueDf, how='left', on='pitcherLeague')

# 在資料集中選取需要的欄位
cch_batting_stats_necessary = cch_batting_stats.loc[:, ['pitcherLeague','pitcherLeagueFgn','pitcherLeagueInd','pitcherLeagueA+','pitcherLeagueAA','pitcherLeagueAAA','throwinghand','runnersOnBase','runnersOnBase1','runnersOnBase2','runnersOnBase3','bases','pitchFaced','strikeFaced','ballFaced']]
feature_names = ['pitcherLeagueFgn','pitcherLeagueInd','pitcherLeagueA+','pitcherLeagueAA','pitcherLeagueAAA','throwinghand','runnersOnBase1','runnersOnBase2','runnersOnBase3','strikeFaced','ballFaced']
x = cch_batting_stats_necessary.loc[:,feature_names]
y = cch_batting_stats_necessary.loc[:,['bases']]

# 將投手慣用手過錄編碼為0、1
throwing_hand_codes = {'R':0, 'L':1}
x['throwinghand'] = x['throwinghand'].replace(throwing_hand_codes)
x['throwinghand'] = x['throwinghand'].astype('int')

# 建立決策樹預測與解釋模型
clf = tree.DecisionTreeRegressor()
clf = clf.fit(x, y)
# 繪製決策樹圖表
fig, ax = plt.subplots(figsize=(12, 10))
tree_plot = tree.plot_tree(
    clf,
    feature_names=feature_names,
    fontsize=10
    )
buf = io.BytesIO()
plt.tight_layout(pad=0)
plt.savefig(buf, transparent=True, format='png', pad_inches=0)
buf.seek(0)
cached_tree_plot = buf.getvalue()
plt.close(fig)

# 設定預測基準特徵值
default_input_data = {
    'pitcherLeague': 'Fgn',
    'throwinghand': 'R',
    'runnersOnBase1': 0,
    'runnersOnBase2': 0,
    'runnersOnBase3': 0,
    'strikeFaced': 0,
    'ballFaced': 0,
}

# 預備好後端程式
app = Flask(__name__)

# 建立後端篩選、呈現與預測程式存取/路徑時的邏輯
@app.route("/", methods=['GET'])
def index():
    # 先從HTTP REQUEST字串( 如 /?throwingHand=L&... )撈參數儲存進dictionary
    input_data = {}
    # 把撈到的參數存到一個字典
    req_args = request.args.to_dict()

    # 如果使用者未給定參數值，則先設定參數值為None，否則設定為使用者傳入的參數值
    for k,v in default_input_data.items():
        if k not in req_args or req_args[k]=='':
            input_data[k] = None
        else:
            input_data[k] = req_args[k]
    # 準備對資料集根據使用者傳入的參數進行篩選後顯示
    filtered_cch_batting_stats = cch_batting_stats.copy()
    # 準備一個用以作為預測基準特徵值的參數dictionary
    test_input_data = {}
    for k,v in input_data.items():
        if v is None:
            # 若使用者未設定參數值，則該預測基準特徵值設定為預設值
            test_input_data[k] = default_input_data[k]
        else:
            if k in ['runnersOnBase1', 'runnersOnBase2', 'runnersOnBase3', 'strikeFaced', 'ballFaced']:
                v = int(v)
            # 將資料集以使用者設定的參數值進行過濾
            filter_condition = filtered_cch_batting_stats[k]==v
            filtered_cch_batting_stats = filtered_cch_batting_stats[filter_condition]
            filtered_cch_batting_stats = filtered_cch_batting_stats.reset_index(drop=True)
            # 若使用者設定參數值，則該預測基準特徵值設定為使用者提供的參數值
            test_input_data[k] = v
    # 算出過濾後資料集的平均獲得/推進壘包數
    avg_bases = filtered_cch_batting_stats['bases'].mean()
    # 得出每種上壘情形的案例數以便視覺化呈現
    chart_data = pd.DataFrame.from_dict({'bases': [0,1,2,3,4]}) #先區分獲得0、1、2、3、4個壘包的情形
    chart_data = chart_data.merge(
        filtered_cch_batting_stats['bases'].value_counts().reset_index(drop=False),
        on=['bases'],
        how='left'
    ).fillna(0).loc[:,'count'].to_list() #將打席紀錄以獲得壘包數分組計算發生次數，然後結合以瞭解0、1、2、3、4個壘包各種情形
    # 根據各個特徵值得出彙整資料（進壘數取平均值、耗球數取平均值以及打席數取次數），數值精度取四捨五入後小數點第二位
    grouped_filtered_data = filtered_cch_batting_stats.groupby(
            ['pitcherLeague','throwinghand','runnersOnBase1','runnersOnBase2','runnersOnBase3']
        ) \
        .agg(
            {'bases':'mean', 'pitchFaced':'mean', 'playlog':'count'} # 計算各個組別的平均上壘數、平均耗球數、事件數
        ).round(2)
    # 將使用者提供的參數值轉換為預測基準特徵值並進行預測
    test_data = pd.DataFrame.from_records([test_input_data])
    test_data = test_data.merge(pitcherLeagueDf, how='left', on='pitcherLeague').drop(columns=['pitcherLeague'])
    test_data['throwinghand'] =  test_data['throwinghand'].replace(throwing_hand_codes)
    test_data = test_data.loc[:,feature_names] # 只保留特徵值
    prediction = clf.predict(test_data)[0]
    
    # 渲染至網頁呈現結果
    return render_template(
        'index.html',
        input_data=input_data,
        test_input_data=test_input_data,
        avg_bases=avg_bases,
        chart_data=str(chart_data),
        prediction=prediction,
        grouped_filtered_data_table=grouped_filtered_data.to_html(classes='data'),
        nrow_filtered_data=filtered_cch_batting_stats.shape[0]
        )

# 提供決策樹圖表的路由
@app.route("/tree_plot.png", methods=['GET'])
def output_tree():
    new_buffer = io.BytesIO(cached_tree_plot)
    return send_file(new_buffer, mimetype="image/png")

if __name__ == '__main__':
    app.debug = True
    app.run()