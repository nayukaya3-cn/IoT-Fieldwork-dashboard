"""📦 備蓄と途絶：何日分あれば足りるかを『確率』で考える"""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import mega_core as mc
import ui

BLUE, ORANGE, RED, GREEN = "#3f6584", "#c9822b", "#b03a2e", "#2f6f4f"
ui.hero("メガリスク ③ ｜ 科学と人間生活 × 情報Ⅰ 確率・シミュレーション（モンテカルロ法）",
        "📦 備蓄と途絶：『何日分』を確率で決める",
        "物が届かない日数は、前もって1つには決まらない。たくさんの『起こりうる場合』をコンピュータで作り、"
        "備蓄が足りなくなる確率と、どの備えが1万円あたり一番効くかを比べる。")
st.warning("途絶日数・噴火の起こりやすさは**授業で話し合うための仮の値**です。予測ではありません。"
           "南海トラフ地震と噴火が続くと支援物資が大幅に遅れるため、1週間ではなく2週間分以上の備蓄が勧められています。", icon="🧪")

st.markdown("#### シナリオ（仮定）を決める")
s1, s2, s3 = st.columns(3)
qm = s1.slider("地震だけで物が届かない日数（真ん中の値）", 1, 30, 7, key="bc_qm")
pe = s2.slider("噴火が続いて降灰がある確率（%）", 0, 100, 50, 5, key="bc_pe",
               help="1707年は続き、1854年は続かなかった。『半々』から議論を始める") / 100
am = s3.slider("降灰で追加される日数（真ん中の値）", 1, 60, 14, key="bc_am")
spread = st.slider("日数のばらつき（大きいほど、長引く場合が多い）", 0.1, 1.2, 0.6, 0.1, key="bc_sp")
d = mc.sample_disruption(quake_median=qm, quake_spread=spread, p_eruption=pe, ash_median=am, ash_spread=spread)

ui.predict("bichiku", "地震だけで真ん中7日、噴火が続く確率50%で追加の真ん中14日（ばらつき0.6）のとき、"
           "**10回のうち9回は足りる備蓄は、何日分？**",
           round(mc.stock_for(0.1, mc.sample_disruption()), 0), "日", protocol="P4", min_value=0.0, max_value=120.0,
           value=14.0, field="メガリスク")

h1, h2, h3 = st.columns(3)
h1.metric("物が届かない日数（真ん中）", f"{np.median(d):.0f} 日")
h2.metric("10回のうち9回は足りる備蓄", f"{mc.stock_for(0.1, d):.0f} 日分")
h3.metric("100回のうち99回は足りる備蓄", f"{mc.stock_for(0.01, d):.0f} 日分")
fig = go.Figure(go.Histogram(x=np.clip(d, 0, 120), nbinsx=60, marker_color=BLUE, opacity=0.8))
for days, col, name in ((7, GREEN, "1週間"), (14, ORANGE, "2週間"), (mc.stock_for(0.1, d), RED, "9割が足りる")):
    fig.add_vline(x=days, line_dash="dash", line_color=col, annotation_text=name, annotation_position="top")
fig.update_layout(height=300, margin=dict(t=30, b=10, l=10, r=10), xaxis_title="物が届かない日数（120日以上は120に寄せて表示）",
                  yaxis_title="場合の数", showlegend=False, bargap=0.05)
st.plotly_chart(fig, width="stretch")
ui.hint("右に長くのびる『すそ』は、噴火が続いて長引く場合が混ざっているから。"
        "真ん中の値（14日）だけを見て備えると、長引く場合を見落とす。噴火の確率を0にして、すそがどう変わるかくらべよう。")

st.markdown("#### 品目ごとの備蓄：足りなくなる確率")
stocks = {}
cols = st.columns(3)
for i, (name, unit, per, default) in enumerate(mc.ITEMS):
    stocks[name] = cols[i % 3].number_input(f"{name}（日分）", 0, 365, default, 1, key=f"bc_stock_{i}")
rows = []
for name, unit, per, _ in mc.ITEMS:
    s = mc.shortage(stocks[name], d)
    rows.append({"品目": name, "備蓄（日分）": stocks[name], "足りなくなる確率": f"{s['p']:.0%}",
                 "足りない日数の平均": round(s["expected"], 1)})
st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
people = st.slider("家の人数", 1, 10, 4, key="bc_people")
st.caption(f"例：飲み水を {stocks['飲み水']} 日分そろえるには、{people}人 × 3L × {stocks['飲み水']}日 ＝ "
           f"**{mc.water_needed_l(people, stocks['飲み水']):,.0f} L**（2Lのペットボトルで {mc.water_needed_l(people, stocks['飲み水']) / 2:,.0f} 本）。")

st.markdown("#### どの備えが、1万円あたり一番効く？")
st.caption("同じ『起こりうる場合』の集まりで、備えを1つだけ足したときに『足りない日数の平均』がどれだけ減るかをくらべる（値段は仮の値）。")
rank = pd.DataFrame(mc.rank_hedges(stocks, d))
st.dataframe(rank.rename(columns={"費用": "費用（円・仮）", "一万円あたり": "1万円あたり減る日数"}), hide_index=True, width="stretch")
top = rank.iloc[0]
st.success(f"いまの備蓄とシナリオでは、**{top['備え']}** が1万円あたり一番効く（{top['一万円あたり']} 日）。"
           "ただし、安い備えは長引いたときに尽きやすい。高い備え（井戸のポンプ・薪窯）は、長引く場合の『すそ』を守る。", icon="📊")
ui.hint("備えを1つ足すたびに、表の1位は入れかわる。『いちばん効く物から順に買う』をくり返すのが、限られたお金での組み立て方。")
ui.reading_card(
    axis="物が届かない日数（横） と 場合の数（縦）、品目ごとの確率", unit="日、%、日/1万円",
    control="そろえた：同じシナリオから作った同じ『場合』の集まり（乱数の種を固定）。変えた：備蓄の日数、備え",
    can="仮定したシナリオのもとで、何日分あれば何割の場合に足りるか・どの備えが割安か",
    cannot="本当の途絶日数（仮定しだいで大きく変わる）・品目ごとに復旧の早さがちがうこと（この模型は同じ日数で止まる）",
    protocols=["P4", "P3"], material="ヒストグラムと2つの表")
ui.footer("mega_bichiku", "🔋 止まらないIoT")
