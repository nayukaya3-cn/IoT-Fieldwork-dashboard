"""🔗 依存の連鎖：何が止まると、何が止まるか（＋降灰の段階）"""
import pandas as pd
import streamlit as st

import iot_core as ic
import mega_core as mc
import ui

ui.hero("メガリスク ② ｜ 科学と人間生活（これからの科学と人間生活）× 情報Ⅰ 情報システム・モデル化",
        "🔗 依存の連鎖：サプライチェーンは矢印でできている",
        "店にパンが並ぶまでには、電気・道路・燃料・通信など、たくさんの矢印がつながっている。"
        "どこか1本が切れると、その先がまとめて止まる。備え（ヘッジ）は、止まった矢印の『別の道』をつくること。")
ui.hint("矢印は『原因 → 結果』の向き。災害を選ぶと、そこから矢印をたどって止まるものが赤くなる。"
        "備えを選ぶと、そのマスは親が止まっても動き続ける（緑）。")

c1, c2 = st.columns([1, 2])
with c1:
    eq = st.checkbox("🌊 南海トラフ地震", True, key="rs_eq")
    ash = st.checkbox("🌋 富士山噴火（降灰）", False, key="rs_ash")
with c2:
    labels = {f"{mc.NODES[k][0]}：{v}": k for k, v in mc.HEDGES.items()}
    picked = st.multiselect("用意する備え（ヘッジ）", list(labels), key="rs_hedges")
hazards = [k for k, on in (("EQ", eq), ("ASH", ash)) if on]
hedges = [labels[x] for x in picked]
down = mc.propagate(hazards, hedges)

local = [n for n, (_, kind, _) in mc.NODES.items() if kind == "三原西部"]
k1, k2, k3 = st.columns(3)
k1.metric("止まるもの（全体）", f"{sum(down[n] for n in mc.NODES if mc.NODES[n][1] != '災害')} / {len(mc.NODES) - 2}")
k2.metric("止まるもの（三原西部）", f"{sum(down[n] for n in local)} / {len(local)}")
k3.metric("🍞 麦からパンを焼く", "止まる" if down["BREAD"] else "焼ける")


def color(n: str) -> str:
    if mc.NODES[n][1] == "災害":
        return "#b03a2e" if down[n] else "#eeeeee"
    if n in hedges:
        return "#bfe3c4"
    return "#f4c7c3" if down[n] else "#ffffff"


dot = ["digraph G {", 'rankdir=LR; nodesep=0.15; ranksep=0.5; node [shape=box, style="rounded,filled", fontname="sans-serif", fontsize=10, margin="0.08,0.03"];',
       'edge [color="#7a8a99", arrowsize=0.6];']
for n in mc.NODES:
    lab = mc.NODES[n][0] + ("\\n（備えあり）" if n in hedges else "")
    pen = ', penwidth=2, color="#2f6f4f"' if n in hedges else ""
    dot.append(f'{n} [label="{lab}", fillcolor="{color(n)}"{pen}];')
dot.append("{rank=same; EQ; ASH;}")
for a, b in mc.EDGES:
    style = "bold" if down[a] and down[b] else "solid"
    col = "#b03a2e" if down[a] and (down[b] or b in hedges) else "#9aa8b5"
    dot.append(f'{a} -> {b} [color="{col}", style={style}];')
dot.append("}")
st.graphviz_chart("\n".join(dot), width="stretch")
st.caption("赤＝止まる、緑＝備えで動き続ける、白＝動く。『飲み水』は水道か井戸のどちらかが動けば足りる（ほかは親が1つでも止まると止まる）。")

rows = []
for n in local:
    if down[n] or n in hedges:
        rows.append({"もの": mc.NODES[n][0], "状態": "備えで動く" if n in hedges else "止まる",
                     "止めている原因": "・".join(mc.NODES[p][0] for p in mc.causes(n, hazards, [])) or "─",
                     "別の道（ヘッジ）": mc.HEDGES.get(n, "（この図では用意していない）")})
if rows:
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
if down["BREAD"]:
    need = [mc.NODES[p][0] for p in mc.causes("BREAD", hazards, hedges)]
    st.warning(f"パンが焼けない。すぐ上で止まっているのは **{'・'.join(need)}**。そこに備えを足すか、さらに上の原因を探そう。", icon="🍞")
elif hazards:
    st.success("災害が起きても、播いた麦でパンを焼ける。外から買う物に頼らない『別の道』がつながっている。", icon="🍞")

st.divider()
st.markdown("#### 降灰の段階：灰の厚さで、何が起きる？")
a1, a2 = st.columns(2)
mm = a1.select_slider("積もった灰の厚さ（mm）", [0, 0.5, 1, 3, 10, 30, 50, 100, 200, 300, 500], 30, key="rs_ash_mm")
rain = a2.toggle("雨が降っている", True, key="rs_rain", help="ぬれた灰は重く、電気を通しやすくなる")
stage, action = mc.ash_stage(mm)
b1, b3 = st.columns([2, 1])
b1.markdown(f"**段階**：{stage}  \n**基本の行動**：{action}")
dens = 1500 if rain else 1000
load = mc.ash_mass_kg_m2(mm, dens) * ic.house_area()
b3.metric("ハウスの屋根にかかる重さ", f"{load / 1000:,.1f} トン" if load >= 1000 else f"{load:,.0f} kg",
          f"{ic.house_area():.1f}㎡ × {mc.ash_mass_kg_m2(mm, dens):.0f} kg/㎡", delta_color="off", delta_arrow="off")
eff = mc.ash_effects(mm, rain)
if eff:
    st.markdown("\n".join(f"- {e}" for e in eff))
else:
    st.info("降灰はない。")
st.caption("影響の目安：内閣府『首都圏における広域降灰対策ガイドライン』（2025年3月）、中央防災会議の広域降灰WG（2020年4月）。"
           "灰のかさ密度（乾いて約1000、ぬれて約1500 kg/m³）は仮の値。三原は富士山から遠く、厚く積もる想定の範囲ではないが、"
           "**物が届かなくなる影響**は首都圏・東海の物流を通じて届く。")
ui.reading_card(
    axis="原因 → 結果 の矢印（依存の関係）", unit="止まる／動く（2値）、mm、kg",
    control="そろえた：矢印のつなぎ方。変えた：起きた災害と、用意した備え",
    can="どの備えが、どの先の止まりを防ぐか（矢印をたどれば言える）",
    cannot="止まる期間の長さ・止まる程度（この図は止まる／動くの2つだけ）・矢印のつなぎ方そのものの正しさ（授業で見直す）",
    protocols=["P4", "P3"], material="依存の図と降灰の表")
ui.footer("mega_rensa", "📦 備蓄と途絶")
