"""🌾 自給の基盤：播いた麦で、パンを焼くまで"""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import iot_core as ic
import mega_core as mc
import ui

BLUE, GREEN, ORANGE = "#3f6584", "#2f6f4f", "#c9822b"
ui.hero("メガリスク ⑤ ｜ 生命の科学（植物・微生物）× 情報Ⅰ モデル化",
        "🌾 自給の基盤：播いた麦で、パンを焼くまで",
        "物が届かなくなったとき、三原西部のハウスと畑は何人を何日ささえられるか。"
        "麦は『育てる』だけでは食べられない。刈る・挽く・ふくらませる・焼く、のどこが外の物にたよっているかを見る。")
st.warning("収量・食べる量・製粉の歩どまりは**仮の値**です。地域・年・品種・育て方で大きく変わります。自分たちの収穫を量って置きかえてください。", icon="🧪")

st.markdown("#### ① どこで、どれだけ作れる？")
PLACES = {f"ハウス（{ic.house_area():.1f}㎡）": ic.house_area() / 100, "ハウス周りの区画（3列・約96㎡）": 0.96,
          "当面使える畑（約10a）": 10.0, "親戚の遊休地（約10a・借りられれば）": 10.0}
picked = st.multiselect("使う場所", list(PLACES), default=list(PLACES)[1:3], key="jk_places")
area = sum(PLACES[p] for p in picked)
c1, c2, c3 = st.columns(3)
yld = c1.slider("収量（kg/10a）", 100, 600, 300, 10, key="jk_yield", help="小麦の収量の仮の値")
seed_rate = c2.slider("来年の種（kg/10a）", 4, 15, 8, 1, key="jk_seed", help="播く量の目安（仮の値）")
ext = c3.slider("製粉の歩どまり（%）", 60, 100, 100, 5, key="jk_ext", help="全粒粉なら100%、白い粉は70%前後") / 100
harvest = mc.wheat_harvest_kg(area, yld)
seed = mc.seed_keep_kg(area, seed_rate)
food = max(harvest - seed, 0.0)
d1, d2, d3, d4 = st.columns(4)
d1.metric("面積", f"{area:.2f} a", f"{area * 100:,.0f} ㎡", delta_color="off", delta_arrow="off")
d2.metric("収穫", f"{harvest:,.0f} kg")
d3.metric("来年の種に残す", f"{seed:,.1f} kg")
d4.metric("食べられる麦", f"{food:,.0f} kg", f"食パン約 {mc.loaves(food, ext):,.0f} 斤", delta_color="off", delta_arrow="off")

st.markdown("#### ② 何人を、何日ささえられる？")
e1, e2, e3 = st.columns(3)
people = e1.slider("人数", 1, 20, 4, key="jk_people")
share = e2.slider("食事のエネルギーのうち、麦でまかなう割合（%）", 10, 100, 50, 10, key="jk_share") / 100
kcal = e3.slider("1人1日のエネルギー（kcal）", 1400, 3000, mc.KCAL_PER_PERSON_DAY, 100, key="jk_kcal")
pdays = mc.person_days(food, ext, kcal_per_day=kcal, share=share)
st.metric(f"{people}人で", f"約 {pdays / people:,.0f} 日", f"のべ {pdays:,.0f} 人日", delta_color="off", delta_arrow="off")
st.caption(f"計算：食べられる麦 {food:,.0f} kg × 歩どまり {ext:.0%} × {mc.WHEAT_KCAL_PER_KG:,} kcal/kg ÷（{kcal:,} kcal × {share:.0%}）。"
           "小麦（玄穀）のエネルギーは食品成分表の目安。")

st.markdown("#### ③ いつ起きるかで、手元の麦はちがう")
f1, f2 = st.columns(2)
month = f1.select_slider("災害が起きた月", list(range(1, 13)), 12, key="jk_month", format_func=lambda m: f"{m}月")
use = f2.slider("ふだん1か月に食べる麦（kg）", 0, 100, 10, 5, key="jk_use")
months = list(range(1, 13))
stock = [mc.stock_at_month(food, m, use) for m in months]
fig = go.Figure(go.Bar(x=[f"{m}月" for m in months], y=stock,
                       marker_color=[ORANGE if m == month else BLUE for m in months]))
fig.update_layout(height=250, margin=dict(t=20, b=10, l=10, r=10), yaxis_title="手元の麦（kg）")
st.plotly_chart(fig, width="stretch")
now = mc.stock_at_month(food, month, use)
st.info(f"{month}月に起きると、手元の麦は **{now:,.0f} kg**（{people}人で約 {mc.person_days(now, ext, kcal_per_day=kcal, share=share) / people:,.0f} 日）。"
        "収穫（6月）の直前がいちばん少ない。11月に播いた麦は、冬の災害のときはまだ畑の中。", icon="📅")

st.markdown("#### ④ 麦からパンまでの工程：外の物にたよっているのはどこ？")
eq = st.checkbox("🌊 南海トラフ地震が起きた", True, key="jk_eq")
ash = st.checkbox("🌋 富士山の降灰で物流が止まった", False, key="jk_ash")
hedge_names = {mc.HEDGES[n]: n for n in ("PUMP", "MILL", "YEAST", "OVEN", "FERT", "HARVEST")}
chosen = st.multiselect("用意する別の道", list(hedge_names), default=[mc.HEDGES["YEAST"]], key="jk_hedges")
hz = [k for k, on in (("EQ", eq), ("ASH", ash)) if on]
hd = [hedge_names[c] for c in chosen]
down = mc.propagate(hz, hd)
rows = []
for step, buy, alt, node in mc.WHEAT_TO_BREAD:
    state = "─" if node not in down else ("✅ 別の道で動く" if node in hd else ("🛑 止まる" if down[node] else "○ 動く"))
    rows.append({"工程": step, "ふだん外から買うもの": buy, "止まったら": state, "別の道（ヘッジ）": alt})
st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
(st.success if not down["BREAD"] else st.error)(
    "播いた麦で、パンを焼ける。" if not down["BREAD"] else
    f"パンが焼けない。止まっているのは：{'・'.join(mc.NODES[p][0] for p in mc.causes('BREAD', hz, hd))}")
ui.hint("サワー種（自家製の酵母）は、粉と水をつぎ足せば育ち続ける。買ったイーストが届かなくなっても、パンはふくらむ。"
        "発酵の速さは温度で変わる。ここでIoTの温度記録が役に立つ。")

st.markdown("#### ⑤ 水：井戸と、汲みおき")
g1, g2 = st.columns(2)
wdays = g1.slider("何日分？", 1, 30, 14, key="jk_wdays")
tank = g2.slider("汲みおきの容器（L）", 0, 1000, 60, 20, key="jk_tank")
need = mc.water_needed_l(people, wdays)
st.metric(f"{people}人 × {wdays}日の飲み水", f"{need:,.0f} L", f"容器だけなら {tank / (people * mc.DRINK_L_PER_PERSON_DAY):.1f} 日分",
          delta_color="off", delta_arrow="off")
st.caption("飲み水は1人1日3Lが目安。井戸の水は、飲む前に水質検査を受け、煮沸する。電動ポンプは停電で止まるので、手押しポンプか蓄電池を考える。")
ui.reading_card(
    axis="面積・収量・人数 と ささえられる日数", unit="a、kg/10a、kg、人日、L",
    control="そろえた：麦のエネルギー（食品成分表の目安）・食べる割合。変えた：使う場所・収量・人数・発災の月",
    can="仮定した収量のもとで、何人を何日ささえられるか・どの工程が外の物にたよっているか",
    cannot="本当の収量（天気・病気・鳥の害）・栄養のかたより（麦だけでは足りない栄養がある）・保存中の傷み",
    protocols=["P4", "P1"], material="面積と日数の数字、月ごとの棒グラフ、工程の表")
ui.footer("mega_jikyu")
