"""📏 測る：CO2と換気（教室とハウス）"""
import math

import plotly.graph_objects as go
import streamlit as st

import iot_core as ic
import ui

BLUE, GREEN, ORANGE = "#3f6584", "#2f6f4f", "#c9822b"
ui.hero("段1 測る ｜ 物質の科学・生命の科学（呼吸と光合成）× 情報Ⅰ モデル化とシミュレーション",
        "📏 測る：CO2の数字から、空気の『ちょうどいい』を決める",
        "同じCO2センサーでも、教室では『高すぎる』、ハウスでは『低すぎる』が問題になる。"
        "入ってくる量と出ていく量のつり合い（箱の模型）で、どちらも説明できる。", stage="測る")
ui.hint(ic.EASY_WORDS)

st.markdown("#### 教室：40人が窓を閉めたままだと、何分で基準をこえる？")
cr = ic.CLASSROOM
actual = ic.minutes_to_reach(1500, cr["people"], cr["volume"], 0)
ui.predict("co2_min", f"{cr['people']}人の教室（{cr['volume']:.0f} m³）で、窓も換気扇も止めた。"
           f"外気と同じ {ic.OUTDOOR_PPM} ppm から始めて、**1500 ppm（学校環境衛生基準）に届くまで何分？**",
           round(actual, 1), "分", protocol="P4", min_value=0.0, max_value=300.0, value=60.0, field="測る")

c1, c2, c3 = st.columns(3)
people = c1.slider("人数", 1, 60, cr["people"], key="hk_people")
volume = c2.slider("部屋の体積（m³）", 30, 600, int(cr["volume"]), 10, key="hk_volume", help="床の広さ × 天井の高さ")
vent = c3.slider("換気量（m³/時）", 0, 3000, 300, 50, key="hk_vent", help="窓や換気扇で1時間に入れかわる空気の量")
gen = st.slider("1人が1時間に出すCO2（m³/時）", 0.010, 0.040, ic.CO2_PER_PERSON, 0.002, format="%.3f", key="hk_gen",
                help="座って軽い作業で 0.02 ほど（仮定）。じっとしていれば少なく、体を動かすと増える")
t, c = ic.co2_series(people, volume, vent, 100, gen=gen)
eq = ic.steady_ppm(people, vent, gen)
m1500 = ic.minutes_to_reach(1500, people, volume, vent, gen=gen)
need = ic.required_vent(people, 1000, gen)
r1, r2, r3, r4 = st.columns(4)
r1.metric("落ち着く濃度", "上がり続ける" if math.isinf(eq) else f"{eq:,.0f} ppm")
r2.metric("1500 ppm まで", "届かない" if math.isinf(m1500) else f"{m1500:.0f} 分")
r3.metric("換気回数", f"{vent / volume:.1f} 回/時", help="1時間に部屋の空気が何回入れかわるか")
r4.metric("1000 ppm に保つ換気量", f"{need:,.0f} m³/時", f"1人あたり {need / people:.0f} m³/時", delta_color="off",
          delta_arrow="off")
fig = go.Figure(go.Scatter(x=t, y=c, mode="lines", line=dict(color=BLUE, width=3)))
for name, v in ic.LIMITS.items():
    fig.add_hline(y=v, line_dash="dash", line_color=ORANGE, annotation_text=f"{name} {v} ppm", annotation_position="top left")
fig.update_layout(height=320, margin=dict(t=20, b=10, l=10, r=10), xaxis_title="時間（分・授業2コマ分）",
                  yaxis_title="CO2濃度（ppm）", showlegend=False, yaxis_range=[300, max(2200, float(min(c.max(), 6000)) + 200)])
st.plotly_chart(fig, width="stretch")
st.code("落ち着く濃度[ppm] ＝ 外気[ppm] ＋ 人数 × 1人の発生量[m³/時] ÷ 換気量[m³/時] × 1,000,000", language="text")
ui.hint("お風呂にたとえると、蛇口（人の呼吸）から入る量と、排水口（換気）から出る量が同じになったところで水位（濃度）が止まる。"
        "排水口を閉めれば、水位は上がり続ける。")
st.caption("基準値の出どころ：建築物衛生法（1000 ppm 以下）、学校環境衛生基準（1500 ppm 以下が望ましい）、"
           f"換気の目安 1人あたり毎時{ic.VENT_PER_PERSON} m³（厚生労働省の換気資料）。授業の前に最新の資料で確かめる。")

st.divider()
st.markdown("#### ハウス：晴れた朝、閉め切るとCO2は逆に『足りなく』なる")
st.caption(f"三原西部のハウス（{ic.HOUSE['width']} m × {ic.HOUSE['length']} m・平均の高さ {ic.HOUSE['height']} m と仮定 ＝ "
           f"{ic.house_volume():.0f} m³）。人は出す側、植物は日中に吸う側。")
h1, h2 = st.columns(2)
uptake = h1.slider("植物がCO2を吸う速さ（g/㎡・時、外気と同じ濃度のとき）", 0.0, 4.0, 1.5, 0.1, key="hk_uptake",
                   help="葉がよく茂った作物で 1〜3 ほど（幅のある仮定）。苗が小さいうちはずっと小さい")
ach = h2.slider("ハウスの換気回数（回/時）", 0.0, 20.0, 1.0, 0.5, key="hk_ach",
                help="閉め切りで 0.5〜2 ほど、側面を開けると 10 以上になる（目安）")
ht, hc = ic.house_series(uptake, ach, 180)
heq = ic.house_steady_ppm(uptake, ach)
q1, q2 = st.columns(2)
q1.metric("落ち着く濃度", f"{heq:.0f} ppm", f"外気 {ic.OUTDOOR_PPM} ppm より {ic.OUTDOOR_PPM - heq:.0f} 低い",
          delta_color="off", delta_arrow="off")
q2.metric("光合成の速さ（外気のときを100として）",
          f"{(heq - ic.COMPENSATION_PPM) / (ic.OUTDOOR_PPM - ic.COMPENSATION_PPM) * 100:.0f}",
          help="この模型では、吸う速さは（濃度 − 補償点）に比例すると仮定している")
fig = go.Figure(go.Scatter(x=ht, y=hc, mode="lines", line=dict(color=GREEN, width=3)))
fig.add_hline(y=ic.OUTDOOR_PPM, line_dash="dot", line_color=BLUE, annotation_text="外気")
fig.add_hline(y=ic.COMPENSATION_PPM, line_dash="dot", line_color=ORANGE, annotation_text="補償点（これ以下では育たない）")
fig.update_layout(height=280, margin=dict(t=20, b=10, l=10, r=10), xaxis_title="日が当たりはじめてからの時間（分）",
                  yaxis_title="CO2濃度（ppm）", showlegend=False, yaxis_range=[0, 480])
st.plotly_chart(fig, width="stretch")
st.markdown("**ここから議論すること**  \n"
            "1. 教室では『高すぎる』、ハウスでは『低すぎる』。**同じセンサー・同じ式で、基準が逆向き**になる  \n"
            "2. 冬は保温のために閉めたい、でもCO2は入れたい。**温度とCO2のどちらを優先するか**は、測らないと決められない  \n"
            "3. この模型の仮定（吸う速さは濃度に比例）は、**1週間の実測で確かめる**（📈 見る・🔁 運用する）")
ui.reading_card(
    axis="時間（横） と CO2濃度（縦）", unit="分、ppm（100万分の1）",
    control="そろえた：部屋の体積・外気の濃度・1人の発生量。変えた：人数と換気量（ハウスでは吸う速さと換気回数）",
    can="発生量と換気量のつり合いで、濃度がどこに落ち着くか・基準をこえるまでの時間",
    cannot="部屋の中の場所による濃度のむら（模型は空気がよく混ざっていると仮定）・感染のリスクそのもの（CO2は換気の目安）",
    protocols=["P4", "P2"], material="2つのグラフ（教室・ハウス）")
ui.exam_question("hakaru", ic.EXAM)
ui.footer("hakaru", "🗄️ 貯める")
