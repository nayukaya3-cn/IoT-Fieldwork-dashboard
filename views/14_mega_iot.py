"""🔋 止まらないIoT：停電・通信断でも測り続ける"""
import math

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import iot_core as ic
import mega_core as mc
import ui

BLUE, ORANGE, RED = "#3f6584", "#c9822b", "#b03a2e"
ui.hero("メガリスク ④ ｜ 光・熱・電気（エネルギー）× 情報Ⅰ 情報システムの信頼性",
        "🔋 止まらないIoT：停電・通信断のときこそ測る",
        "災害のときにIoTが止まれば、ハウスの様子も井戸の水位もわからない。"
        "電気は蓄電池と太陽光で、記録はSDカードに貯めて、知らせるのは現地のブザーで。ネットにたよらない設計を考える。")

st.markdown("#### ① 眠らせて、電気を節約する（間欠動作）")
c1, c2, c3, c4 = st.columns(4)
aw = c1.number_input("起きているとき（W）", 0.5, 20.0, 5.0, 0.5, key="mi_aw")
sw = c2.number_input("眠っているとき（W）", 0.0, 5.0, 0.3, 0.1, key="mi_sw", help="眠らせる機能は機種によって違う（仮の値）")
asec = c3.number_input("1回に起きている秒数", 5, 600, 60, 5, key="mi_as")
iv = c4.select_slider("測る間隔（分）", [1, 5, 10, 30, 60], 10, key="mi_iv")
avg = mc.avg_watt(aw, sw, asec, iv)
d1, d2 = st.columns(2)
d1.metric("平均の消費電力", f"{avg:.2f} W", f"つけっぱなし {aw:.1f} W の {avg / aw:.0%}", delta_color="off", delta_arrow="off")
d2.metric("1日に使う電気", f"{avg * 24:.0f} Wh", f"つけっぱなしなら {aw * 24:.0f} Wh", delta_color="off", delta_arrow="off")

st.markdown("#### ② 蓄電池と太陽光で、何日動く？")
e1, e2, e3, e4 = st.columns(4)
bat = e1.number_input("蓄電池の容量（Wh）", 50, 5000, 500, 50, key="mi_bat", help="ポータブル電源の容量の表示など")
panel = e2.number_input("太陽光パネル（W）", 0, 400, 50, 10, key="mi_panel")
sun = e3.slider("日照（ピーク時間換算・時間/日）", 0.0, 6.0, 3.0, 0.5, key="mi_sun", help="冬・くもりは小さい（仮の値）")
ashloss = e4.slider("パネルの灰・汚れで減る割合（%）", 0, 100, 0, 5, key="mi_ash") / 100
solar = mc.solar_wh_day(panel, sun, 0.7, ashloss)
auto = mc.autonomy_days(bat, avg, solar)
auto_on = mc.autonomy_days(bat, aw, solar)
f1, f2, f3 = st.columns(3)
f1.metric("1日の発電", f"{solar:.0f} Wh")
f2.metric("動き続けられる日数（眠らせる）", "ずっと" if math.isinf(auto) else f"{auto:.1f} 日")
f3.metric("（参考）つけっぱなしなら", "ずっと" if math.isinf(auto_on) else f"{auto_on:.1f} 日")
loss = np.linspace(0, 1, 21)
days = [min(mc.autonomy_days(bat, avg, mc.solar_wh_day(panel, sun, 0.7, x)), 60) for x in loss]
fig = go.Figure(go.Scatter(x=loss * 100, y=days, mode="lines+markers", line=dict(color=BLUE, width=3)))
fig.add_vline(x=ashloss * 100, line_dash="dash", line_color=ORANGE)
fig.update_layout(height=260, margin=dict(t=20, b=10, l=10, r=10), xaxis_title="パネルの灰・汚れで減る割合（%）",
                  yaxis_title="動き続けられる日数（60日で頭打ち表示）")
st.plotly_chart(fig, width="stretch")
st.caption("『ずっと』＝1日の発電が1日の消費を上回り、蓄電池が減らない。グラフは60日で頭打ちに表示。灰・汚れの割合がある値をこえると、日数が急に短くなる。")

st.markdown("#### ③ ネットが止まっても、記録は残す（SDに貯めて、つながったら送る）")
g1, g2, g3 = st.columns(3)
gb = g1.select_slider("SDカード（GB）", [8, 16, 32, 64, 128], 32, key="mi_gb")
photos = g2.slider("1日に撮る写真の枚数", 0, 288, 24, 4, key="mi_photos")
pkb = g3.slider("写真1枚の大きさ（KB）", 50, 2000, 300, 50, key="mi_pkb")
sd = mc.storage_days(gb, ic.rows_per_day(iv), photos_per_day=photos, photo_kb=pkb)
st.metric("SDカードに貯め続けられる日数", "ほぼ無限" if sd > 36500 else f"{sd:,.0f} 日（約 {sd / 365:.1f} 年）")
st.dataframe(pd.DataFrame([
    {"ふだん": "測ったらすぐクラウドの表へ", "ネットが止まったら": "SDカードに書く。つながったら、まだ送っていない行をまとめて送る", "ねらい": "記録が欠けない"},
    {"ふだん": "警報はメール", "ネットが止まったら": "現地のブザー・ランプ。人が見に来たときに画面で確かめる", "ねらい": "知らせる手段を2つ"},
    {"ふだん": "時刻はネットで合わせる", "ネットが止まったら": "時計（RTC）の部品で時刻を保つ", "ねらい": "あとで並べたときに順番がくずれない"},
    {"ふだん": "電気は家のコンセント", "ネットが止まったら": "蓄電池＋太陽光。電池が減ったら測る間隔をのばす", "ねらい": "長く動く"},
]), hide_index=True, width="stretch")

st.markdown("#### ④ IoTそのものを『降灰センサー』にする")
ui.hint("パネルの横に照度センサーを置き、晴れた日のいつもの値とくらべる。いつもより暗ければ、灰か汚れがパネルの光をさえぎっている。")
h1, h2 = st.columns(2)
cover = h1.slider("灰でさえぎられる割合（このシミュレーションの設定・%）", 0, 90, 40, 5, key="mi_cover") / 100
thr = h2.slider("掃除の合図を出す割合（%）", 5, 60, 20, 5, key="mi_thr") / 100
day = ic.synth_day(seed=7)
normal = day["照度"]
ashy = normal * (1 - cover)
noon = (day["時刻"] >= 11) & (day["時刻"] <= 13)
soil = mc.panel_soiling(float(ashy[noon].mean()), float(normal[noon].mean()))
fig = go.Figure()
fig.add_trace(go.Scatter(x=day["時刻"], y=normal, name="晴れた日のいつもの値", line=dict(color="#a9bccf")))
fig.add_trace(go.Scatter(x=day["時刻"], y=ashy, name="今日の値（灰あり）", line=dict(color=RED)))
fig.update_layout(height=260, margin=dict(t=20, b=10, l=10, r=10), xaxis_title="時刻（時）", yaxis_title="照度（lx）",
                  legend=dict(orientation="h", y=1.15), xaxis=dict(dtick=3, range=[0, 24]))
st.plotly_chart(fig, width="stretch")
(st.error if soil >= thr else st.success)(
    f"昼（11〜13時）の照度は、いつもの {1 - soil:.0%}。さえぎられている割合 {soil:.0%} → "
    + ("**パネルを掃除する合図**（灰は水で流すと固まることがある。乾いたまま、やわらかいほうきで落とす）" if soil >= thr else "まだ合図は出さない"))
st.caption("架空データ。実際は、くもりでも暗くなる。『くもり』と『灰』を分けるには、パネルと同じ向きの照度計を2つ置き、1つだけをカバーで守ってくらべる（対照実験）。")
ui.reading_card(
    axis="パネルの灰・汚れの割合（横） と 動き続けられる日数（縦）", unit="%、日、Wh、W",
    control="そろえた：蓄電池の容量・消費電力・日照。変えた：灰・汚れの割合",
    can="灰・汚れが増えると発電が減り、ある割合をこえると蓄電池が減り続ける（日数が急に短くなる）",
    cannot="実際の日照（季節・天気）・蓄電池の寒さでの弱り・部品が壊れたときの動き",
    protocols=["P4", "P1"], material="日数のグラフと照度のグラフ")
ui.footer("mega_iot", "🌾 自給の基盤")
