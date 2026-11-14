"""🗺️ 地図と学習計画：8つの段 × 資料10本"""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import iot_core as ic
import ui

GREEN = "#2f6f4f"
ui.hero("全体の地図", "🗺️ 8つの段で、作って・測って・運用する",
        "IoTのしくみを『測る→貯める→見る→知らせる→動かす』の5段と、『つくる・運用する・届ける』の3段に分けた。"
        "資料を選ぶと、どの段が手薄かが見える。")
ui.hint("左のメニューは、この8つの段の順に並んでいる。上から順に進めば、1台のIoTを作って、運用して、育てた物を届けるまでの一周になる。")

st.markdown("#### 8つの段：どの段を、理科と情報Ⅰのどこで学ぶか")
st.dataframe(pd.DataFrame(ic.STAGES, columns=["段", "やさしく言うと", "科学と人間生活での見方", "情報Ⅰの単元"]),
             hide_index=True, width="stretch")

st.markdown("#### 学習計画をつくる：資料を選ぶと、抜けている段が見える")
names = {m["name"]: m["id"] for m in ic.MATERIALS}
picked = st.multiselect("使う資料（最初はIoT講座3本）", list(names), key="chizu_pick",
                        default=[ic.BY_ID[i]["name"] for i in ic.IOT_CORE_IDS])
ids = [names[n] for n in picked]
ps = ic.plan_summary(ids)
k1, k2, k3 = st.columns(3)
k1.metric("動画の合計", f"{ps['hours']:g} 時間", f"{ps['lectures']} レクチャー", delta_color="off", delta_arrow="off")
k2.metric("カバーした段", f"{ps['covered']} / {len(ic.STAGE_NAMES)}")
k3.metric("抜けている段", "なし" if not ps["missing"] else "・".join(ps["missing"]))
if ids:
    fig = go.Figure(go.Heatmap(
        z=ic.matrix(ids), x=ic.STAGE_NAMES, y=[ic.BY_ID[i]["name"] for i in ids],
        colorscale=[[0, "#f3f5f7"], [1, GREEN]], showscale=False, xgap=3, ygap=3,
        hovertemplate="%{y}<br>段：%{x}<extra></extra>"))
    fig.update_layout(height=90 + 38 * len(ids), margin=dict(t=10, b=10, l=10, r=10),
                      yaxis=dict(autorange="reversed"), xaxis=dict(side="top"))
    st.plotly_chart(fig, width="stretch")
    st.caption("緑のマス＝その資料がその段を扱っている。縦に見て緑が1つもない列が『抜けている段』。")
    st.dataframe(pd.DataFrame([{"資料": ic.BY_ID[i]["name"], "レベル": ic.BY_ID[i]["level"],
                                "科学と人間生活の領域": ic.BY_ID[i]["field"], "フィールドワークでの役割": ic.BY_ID[i]["role"]}
                               for i in ids]), hide_index=True, width="stretch")
if ps["missing"]:
    st.warning(f"**{'・'.join(ps['missing'])}** の段が抜けている。IoT講座だけでは『作って動いた』で終わりやすい。"
               "運用の輪・直売・伴走の資料を足すと、列が埋まる。", icon="🧩")
else:
    st.success("8つの段がすべて埋まった。どの順番で・だれが・どこまでやるかは「🧑‍🏫 先生・支援者向け」で決める。", icon="✅")
ui.reading_card(
    axis="資料（縦） と 段（横）", unit="扱っている／いない（2値）、時間",
    control="そろえた：段の分け方（8つ）。変えた：選ぶ資料",
    can="選んだ資料で、どの段が手薄か・全部で何時間かかるか",
    cannot="その段がどれだけ深く学べるか（マスは深さを表さない）・自分にとっての難しさ",
    protocols=["P2", "P3"], material="資料×段のマス目")
st.caption("出どころ：作成者がまとめた資料10本の概要。講座名・講師名・事業所名は載せていません。"
           "時間とレクチャー数は資料に書かれていた値です（未記入のものは 0）。")
ui.footer("chizu", "📏 測る")
