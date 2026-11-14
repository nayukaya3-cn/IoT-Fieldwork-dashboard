"""🔔 知らせる：誤報を減らす設計と、まとめメールの文面"""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import iot_core as ic
import ops_core as oc
import ui

ORANGE, GREY = "#c9822b", "#a9bccf"
ui.hero("段4 知らせる ｜ 情報Ⅰ 条件分岐・確率（ベイズ）",
        "🔔 知らせる：『オオカミ少年』にしない警報",
        "警報が1日に何度も鳴ると、だれも見なくなる。鳴らなすぎると、本当の異常を見逃す。"
        "しきい値・回数の条件・まとめの書き方を、数字で決める。", stage="知らせる")

st.markdown("#### 誤報は1日に何回？")
ui.hint("センサーの読みは毎回少しずつぶれる。しきい値のすぐ下にいるだけで、たまたま上にはみ出すことがある。")
a1, a2, a3 = st.columns(3)
true_v = a1.slider("本当のCO2濃度（ppm・異常ではない状態）", 400, 1500, 900, 10, key="sr_true")
thr = a2.slider("警報のしきい値（ppm）", 600, 2000, 1000, 50, key="sr_thr")
sd = a3.slider("センサーの読みのぶれ（ppm）", 0, 150, 50, 5, key="sr_sd",
               help="同じ空気を何回も測ったときのばらつき（標準偏差）。安いセンサーほど大きい")
a4, a5 = st.columns(2)
iv = a4.select_slider("測る間隔（分）", [1, 2, 5, 10, 15, 30, 60], 10, key="sr_iv")
ncon = a5.slider("何回つづけてこえたら警報にする？", 1, 6, 1, key="sr_ncon")
p1 = ic.exceed_prob(true_v, thr, sd)
fa = ic.false_alarms_per_day(true_v, thr, sd, iv, ncon)
w1, w2, w3 = st.columns(3)
w1.metric("1回の測定がたまたまこえる確率", f"{p1:.1%}")
w2.metric("まちがい警報（誤報）", f"{fa:.2f} 回/日" if fa >= 0.01 else "ほぼ0 回/日",
          f"月に約 {fa * 30:.0f} 回" if fa >= 0.05 else "月に1回未満", delta_color="off", delta_arrow="off")
w3.metric("本当の異常に気づく遅れ", f"{ic.alert_delay_min(iv, ncon):.0f} 分〜", help="つづけて数える分だけ、警報は遅くなる")
ns = list(range(1, 7))
fig = go.Figure(go.Bar(x=[f"{n}回" for n in ns], y=[ic.false_alarms_per_day(true_v, thr, sd, iv, n) for n in ns],
                       marker_color=[ORANGE if n == ncon else GREY for n in ns]))
fig.update_layout(height=250, margin=dict(t=20, b=10, l=10, r=10), xaxis_title="つづけてこえた回数の条件",
                  yaxis_title="誤報（回/日）", showlegend=False)
st.plotly_chart(fig, width="stretch")
st.caption("計算の仮定：読みのぶれは正規分布で、毎回の測定は独立。設置後に誤報の回数を数えて確かめる。")

st.markdown("#### 警報が鳴った。本当に異常である確率は？（ベイズの考え方）")
y1, y2, y3 = st.columns(3)
prior = y1.slider("異常の起こりやすさ（100回の測定のうち）", 0.1, 20.0, 1.0, 0.1, key="sr_prior") / 100
hit = y2.slider("異常を見つける率（%）", 50, 100, 95, key="sr_hit") / 100
fr = y3.slider("異常でないのに鳴る率（%）", 0.1, 20.0, 5.0, 0.1, key="sr_fr") / 100
post = ic.bayes_alert(prior, hit, fr)
st.metric("警報が鳴ったとき、本当に異常である確率", f"{post:.0%}", f"鳴る前の見込み {prior:.1%} から更新",
          delta_color="off", delta_arrow="off")
if post < 0.5:
    st.warning("鳴った警報の半分以上がまちがい。異常がめったに起きないと、誤報率が小さくても『はずれ』の警報のほうが多くなる。"
               "警報が来たら、まずハウスへ行って実物を見る（数字と実物を見くらべる）。")
ui.reading_card(
    axis="回数の条件（横） と 誤報の回数（縦）", unit="回、回/日、%",
    control="そろえた：本当の濃度・しきい値・ぶれ・間隔。変えた：つづけて数える回数",
    can="条件を厳しくするほど誤報は減り、気づくのは遅れる（どちらかを取れば、どちらかをゆずる）",
    cannot="ぶれが毎回独立かどうか（実際は続けて同じ向きにぶれることがある）・異常の起こりやすさの本当の値",
    protocols=["P4", "P3"], material="誤報の棒グラフとベイズの数字")

st.divider()
st.markdown("#### まとめメールの文面をつくる（送信はしない）")
st.caption("ここでは文面をつくるだけ。実際の送信は、IoTキットのプログラム側で行う。宛先・鍵は、ここには入れない。")
df, label, synthetic = ui.week_data("sr_data")
dates = sorted(pd.to_datetime(df["時刻"]).dt.date.unique())
day = st.selectbox("どの日のまとめ？", dates, index=0, key="sr_day", format_func=lambda d: f"{d:%m/%d}")
t1, t2, t3 = st.columns(3)
co2_lo = t1.number_input("CO2 これ未満で注意（ppm）", 0, 2000, 250, 10, key="sr_co2lo",
                         help="日中のハウスでCO2が足りない目安（仮の値）")
tmp_hi = t2.number_input("気温 これ超で注意（℃）", 0, 60, 30, 1, key="sr_tmphi")
dep_lo = t3.number_input("水深 これ未満で注意（mm）", 0, 200, 35, 1, key="sr_deplo")
mail = oc.summary_mail(df, day, oc.guess_interval(df["時刻"]),
                       {"CO2": (float(co2_lo), None), "気温": (None, float(tmp_hi)), "水深": (float(dep_lo), None)})
st.code(mail, language="text")
st.caption(f"使ったデータ：{label}。代表値に平均でなく中央値を使い、ありえない値は除いて件数だけ書いている。")
ui.footer("shiraseru", "💧 動かす")
