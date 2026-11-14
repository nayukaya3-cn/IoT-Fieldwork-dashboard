"""🖨️ つくる：部品を設計・印刷し、いくらかかるかを見積もる"""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import iot_core as ic
import ui

BLUE, GREEN, ORANGE = "#3f6584", "#2f6f4f", "#c9822b"
ui.hero("段6 つくる ｜ 物質の科学（プラスチック）× 情報Ⅰ モデル化・知的財産権",
        "🖨️ つくる：自分で設計し、いくらで何ができるかを知る",
        "センサーのカバーやカメラの台は、3Dプリンタで作れる。図面どおりに描くと入らない理由、"
        "人の3Dデータを使うときの約束、1台にかかるお金を、ここで確かめる。", stage="つくる")

tab1, tab2 = st.tabs(["① 自分で設計する", "② いくらで何ができる？"])

with tab1:
    st.markdown("#### 3Dプリンタ向けの設計のコツ")
    st.dataframe(pd.DataFrame(ic.DESIGN_TIPS, columns=["コツ", "なぜ", "ハウスのIoTでの例"]), hide_index=True, width="stretch")
    st.caption("資料に挙がっていた設計のコツのうち3つ。扱う材料：" + "・".join(ic.FILAMENTS_IOT) +
               "。ハウスの中は夏に50℃をこえることがあり、PLAは60℃前後で柔らかくなる（置き場所と材料に注意）。")

    st.markdown("#### はめ合いの隙間：図面どおりに描くと入らない")
    ui.hint("3Dプリンタは、溶かした糸を少しずつ重ねる。重ねた糸がわずかに広がるので、穴は図面より狭く、出っぱりは太く仕上がる。")
    f1, f2, f3 = st.columns(3)
    hole = f1.number_input("穴（溝）の幅：図面（mm）", 1.0, 100.0, 10.0, 0.05, key="tk_hole", format="%.2f")
    part = f2.number_input("差しこむ物の幅：図面（mm）", 1.0, 100.0, 10.0, 0.05, key="tk_part", format="%.2f")
    swell = f3.slider("印刷で太る量（片側・mm）", 0.0, 0.3, 0.1, 0.01, key="tk_swell",
                      help="機種・材料・設定で変わる仮定の値。小さな試し刷り（隙間を0.1mmずつ変えた見本）で確かめる")
    fit = ic.clearance_fit(hole, part, swell)
    msg = f"印刷後のすき間 {fit['gap']:+.2f} mm → **{fit['verdict']}**"
    {"入らない": st.error, "きつい": st.warning, "ちょうど": st.success, "ゆるい": st.info}[fit["verdict"]](msg)
    st.caption("『ちょうど』の幅（0.1〜0.4 mm）も目安。外して付け直すふたは広め、動かない差しこみは狭め、と目的で決める。")
    gaps = [round(x * 0.1, 1) for x in range(0, 7)]
    st.markdown("**試し刷りの見本**：穴の幅を下のように変えた7つの穴を1枚に印刷し、どれがちょうどかを自分の機種で決める。")
    st.dataframe(pd.DataFrame([{"図面の隙間（mm）": g, "穴の幅（mm）": round(part + g, 2),
                                "この仮定での判定": ic.clearance_fit(part + g, part, swell)["verdict"]} for g in gaps]),
                 hide_index=True, width="stretch")

    st.markdown("#### 人の3Dデータを使うときは、ライセンスを読む")
    st.dataframe(pd.DataFrame(ic.CC_TERMS, columns=["条件", "意味", "使うときにすること"]), hide_index=True, width="stretch")
    l1, l2, l3 = st.columns(3)
    terms = l1.multiselect("データに付いている条件", [t[0] for t in ic.CC_TERMS], default=["BY（表示）", "NC（非営利）"],
                           key="tk_cc")
    sell = l2.toggle("直売で売る品物・販促に使う", key="tk_cc_sell")
    mod = l3.toggle("形を変えて使う（穴を足す など）", key="tk_cc_mod")
    ok, notes = ic.cc_ok({t.split("（")[0] for t in terms}, commercial=sell, modify=mod)
    (st.success if ok else st.error)(("この使い方はできる。" if ok else "この使い方はできない。") +
                                     ("　" + "／".join(notes) if notes else ""))
    st.caption("クリエイティブ・コモンズ（CC）の考え方の要点だけ。使う前に、データのページに書かれたライセンスの本文を確かめる。")
    ui.reading_card(
        axis="図面の寸法 と 印刷後のすき間", unit="mm",
        control="そろえた：差しこむ物の幅・太る量。変えた：穴の幅",
        can="図面どおり（隙間0）だと、印刷すると入らない",
        cannot="自分の機種で何mm太るか（試し刷りが必要）・夏の高温で変形しないか",
        protocols=["P4", "P1"], material="すき間の判定と試し刷りの表")

with tab2:
    st.markdown("#### 1台つくると、いくら？")
    st.warning("下の値段は**仮の値**です。部品の値段は時期と店で大きく変わります。買う前に必ず調べて、表を書きかえてください。", icon="🧾")
    bom = pd.DataFrame([{"買う": True, "部品": n, "役割": r, "値段（円）": p, "なくても始められる": opt}
                        for n, r, p, opt in ic.BOM])
    edited = st.data_editor(bom, hide_index=True, width="stretch", key="tk_bom", num_rows="fixed",
                            disabled=["部品", "役割", "なくても始められる"],
                            column_config={"値段（円）": st.column_config.NumberColumn(min_value=0, max_value=200000, step=100)})
    total = ic.bom_total(edited["値段（円）"].fillna(0).tolist(), edited["買う"].tolist())
    o1, o2, o3 = st.columns(3)
    watt = o1.slider("本体の消費電力（W）", 2.0, 10.0, ic.POWER_W, 0.5, key="tk_watt", help="機種と負荷で 3〜8W ほど")
    yen = o2.slider("電気代の単価（円/kWh）", 20.0, 50.0, ic.YEN_PER_KWH, 1.0, key="tk_yen", help="契約で違う。検針票で確かめる")
    months = o3.slider("使う期間（月）", 1, 36, 8, key="tk_months", help="麦なら播種（11月）から収穫（6月）まで約8か月")
    monthly = ic.power_cost_month(watt, yen)
    per = ic.cost_per_reading(total, months, monthly, 5, 10)
    t1, t2, t3, t4 = st.columns(4)
    t1.metric("材料費", f"{total:,} 円", f"資料の目安 {ic.BUDGET_RANGE[0] // 10000}〜{ic.BUDGET_RANGE[1] // 10000}万円",
              delta_color="off", delta_arrow="off")
    t2.metric("電気代", f"{monthly:,.0f} 円/月", f"{watt * 24 * 30 / 1000:.1f} kWh", delta_color="off", delta_arrow="off")
    t3.metric(f"{months}か月の合計", f"{total + monthly * months:,.0f} 円")
    t4.metric("数字1個あたり", f"{per:.3f} 円", "5つの数字を10分ごと", delta_color="off", delta_arrow="off")
    fig = go.Figure(go.Bar(x=["材料費（最初に1回）", f"電気代（{months}か月）", "クラウド（無料枠の中）"],
                           y=[total, monthly * months, 0], marker_color=[BLUE, ORANGE, GREEN],
                           text=[f"{total:,}円", f"{monthly * months:,.0f}円", "0円"], textposition="outside"))
    fig.update_layout(height=280, margin=dict(t=30, b=10, l=10, r=10), yaxis_title="円", showlegend=False)
    st.plotly_chart(fig, width="stretch")
    st.markdown("#### 3Dプリンタで作る部品の材料費")
    p1c, p2c = st.columns(2)
    grams = p1c.slider("部品1個の重さ（g）", 5, 300, 40, 5, key="tk_grams")
    ykg = p2c.slider("フィラメントの値段（円/kg）", 1500, 8000, 3000, 100, key="tk_ykg")
    st.metric("部品1個の材料費", f"{ic.filament_cost(grams, ykg):,.0f} 円")
    ui.hint("毎朝ハウスまで見に行く手間とくらべてみよう。ただし『行かなくてよくなる』のではなく、『行くべき日がわかる』のがIoTの役目。")
    ui.reading_card(
        axis="費用の内わけ（材料費・電気代・クラウド）", unit="円、円/月、円/個",
        control="そろえた：測る数字（5つ）と間隔（10分）。変えた：部品の選び方・期間・電気代の単価",
        can="最初にかかるお金と、続けるのにかかるお金のどちらが大きいか",
        cannot="作る時間・直す時間の値段（人の手間は入っていない）・無料枠がこの先も続くか",
        protocols=["P1", "P3"], material="部品の表と3本の棒グラフ")
ui.footer("tsukuru", "🔁 運用する")
