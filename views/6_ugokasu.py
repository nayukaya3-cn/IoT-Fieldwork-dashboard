"""💧 動かす：自動水やりのしきい値は1本より2本"""
import plotly.graph_objects as go
import streamlit as st

import iot_core as ic
import ui

BLUE, GREEN, ORANGE = "#3f6584", "#2f6f4f", "#c9822b"
ui.hero("段5 動かす ｜ 生命の科学（恒常性）× 情報Ⅰ アルゴリズム・制御",
        "💧 動かす：数字に応じてポンプを入れたり切ったりする",
        "水深が浅くなったらポンプをON、深くなったらOFF。しきい値を1本にすると、読みのぶれでカチカチと入切をくり返す。"
        "2本にすると落ち着く。体温や血糖値を保つしくみと同じ形。", stage="動かす")

ui.predict("pump", "水深が 40 mm より浅くなったらポンプON、深くなったらOFF、という**しきい値1本**の規則にした。"
           "読みが ±1 mm ぶれるとき、**1日にポンプが入切する回数**は？（しきい値を 35 mm と 45 mm の2本にすると12回）",
           float(ic.pump_sim(40, 40)["switches"]), "回", protocol="P4", min_value=0.0, max_value=1000.0, value=12.0,
           field="動かす")
z1, z2, z3 = st.columns(3)
lo, hi = z1.slider("ONにする水深 〜 OFFにする水深（mm）", 20, 60, (35, 45), key="ug_band")
nz = z2.slider("水深センサーの読みのぶれ（mm）", 0.0, 3.0, 1.0, 0.1, key="ug_nz")
drain = z3.slider("水が減る速さ（mm/時）", 0.5, 10.0, 3.0, 0.5, key="ug_drain", help="植物が吸う分と蒸発する分")
sim = ic.pump_sim(lo, hi, noise_sd=nz, drain_mm_h=drain)
one = ic.pump_sim((lo + hi) / 2, (lo + hi) / 2, noise_sd=nz, drain_mm_h=drain)
v1, v2, v3 = st.columns(3)
v1.metric("入切の回数（この設定）", f"{sim['switches']} 回/日")
v2.metric("しきい値1本なら", f"{one['switches']} 回/日", f"中央の {(lo + hi) / 2:.0f} mm 1本", delta_color="off",
          delta_arrow="off")
v3.metric("水深の動く幅", f"{sim['min']:.0f}〜{sim['max']:.0f} mm")
fig = go.Figure()
fig.add_trace(go.Scatter(x=sim["t"], y=sim["depth"], mode="lines", line=dict(color=BLUE, width=2), name="水深"))
fig.add_trace(go.Scatter(x=sim["t"], y=sim["pump"] * (hi - lo + 4) + lo - 2, mode="lines", line=dict(color=ORANGE, width=1),
                         name="ポンプON", opacity=0.6, line_shape="hv"))
fig.add_hline(y=lo, line_dash="dash", line_color=GREEN, annotation_text="ON", annotation_position="bottom left")
fig.add_hline(y=hi, line_dash="dash", line_color=GREEN, annotation_text="OFF", annotation_position="top left")
fig.update_layout(height=300, margin=dict(t=20, b=10, l=10, r=10), xaxis_title="時間（時）", yaxis_title="水深（mm）",
                  legend=dict(orientation="h", y=1.12), xaxis=dict(dtick=3))
st.plotly_chart(fig, width="stretch")
st.markdown("2本のしきい値のあいだは『いまの状態を続ける』。この工夫を**ヒステリシス**という。"
            "エアコンやこたつの温度調節、そして体温や血糖値を一定に保つしくみ（恒常性）も、同じ形をしている。")
with st.expander("プログラムで書くと（Python）"):
    st.code(f"""if 水深 < {lo}:      # 浅い → 入れる
    ポンプ = ON
elif 水深 > {hi}:    # 深い → 止める
    ポンプ = OFF
# そのあいだ（{lo}〜{hi}）は、いまの状態のまま""", language="python")
st.info("**安全**：水（ポンプ・容器）と電気（コンセント・基板）は同じ台に置かない。配線は電源を抜いてから。", icon="🦺")
ui.reading_card(
    axis="時間（横） と 水深・ポンプの入切（縦）", unit="時、mm、回/日",
    control="そろえた：水が減る速さ・ポンプの強さ・読みのぶれ。変えた：しきい値の本数と幅",
    can="しきい値の幅を広げると入切は減り、水深の動く幅は広がる",
    cannot="植物にとって最適な水深（育てて測らないとわからない）・ポンプや配管が故障したときの動き",
    protocols=["P4", "P1"], material="水深とポンプのグラフ")
ui.footer("ugokasu", "🖨️ つくる")
