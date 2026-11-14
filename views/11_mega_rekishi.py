"""🌊 歴史と連動：南海トラフ地震の繰り返しと『時間差』"""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import mega_core as mc
import ui

BLUE, RED, ORANGE = "#3f6584", "#b03a2e", "#c9822b"
ui.hero("メガリスク ① ｜ 地球の科学（プレートの境界・火山）× 情報Ⅰ データの活用",
        "🌊 歴史と連動：1回で終わらない巨大地震",
        "南海トラフの地震は、東側と西側が時間差で起きることがある。富士山の噴火が続いたこともある。"
        "過去の記録から『間隔』と『時間差』を読み、物が届かなくなる期間を考える入口にする。")
st.warning("🧪 このページからの5ページ（メガリスク）は**実験的なプロトタイプ**です。確率・日数の多くは授業で話し合うための仮の値で、"
           "予測ではありません。避難や備えは、自治体・気象庁・内閣府の情報に従ってください。", icon="🌋")

with st.container(border=True):
    st.markdown("#### 1854年 安政東海地震 → 安政南海地震")
    st.markdown(f"- {mc.ANSEI['tokai']}  \n- {mc.ANSEI['nankai']}  \n{mc.ANSEI['note']}")

ui.predict("ansei_gap", "安政東海地震（東側）が起きてから、安政南海地震（西側）が起きるまで、**およそ何時間**？",
           mc.GAPS[1][1], "時間", protocol="P5", min_value=0.0, max_value=1000.0, value=24.0, field="メガリスク")

st.markdown("#### 年表：地震と噴火")
ev = pd.DataFrame(mc.HISTORY, columns=["年", "できごと", "種類", "次とのつながり"])
fig = go.Figure()
for kind, color, y in (("地震", BLUE, 1), ("噴火", RED, 2)):
    sub = ev[ev["種類"] == kind]
    fig.add_trace(go.Scatter(x=sub["年"], y=[y] * len(sub), mode="markers+text", text=sub["年"].astype(str),
                             textposition="top center", marker=dict(size=14, color=color), name=kind,
                             hovertext=sub["できごと"] + "<br>" + sub["次とのつながり"], hoverinfo="text"))
fig.update_layout(height=230, margin=dict(t=20, b=10, l=10, r=10), yaxis=dict(visible=False, range=[0.5, 2.7]),
                  xaxis_title="年", legend=dict(orientation="h", y=1.15))
st.plotly_chart(fig, width="stretch")
st.dataframe(ev, hide_index=True, width="stretch")
st.caption("年は資料により数え方が少しちがう。古い時代ほど記録の抜けがあるかもしれない。")

c1, c2 = st.columns(2)
with c1:
    st.markdown("##### 地震の間隔（年）")
    iv = mc.intervals()
    labels = [f"{a}→{b}" for a, b in zip(mc.QUAKE_YEARS, mc.QUAKE_YEARS[1:])]
    f2 = go.Figure(go.Bar(x=labels, y=iv, marker_color=BLUE, text=iv, textposition="outside"))
    f2.update_layout(height=260, margin=dict(t=20, b=10, l=10, r=10), yaxis_title="年")
    st.plotly_chart(f2, width="stretch")
    st.caption(f"最近の3回は {iv[-3]}・{iv[-2]}・{iv[-1]} 年。前回（1944・1946年）から約80年。")
with c2:
    st.markdown("##### 2つ目が起きるまでの時間差（対数の目盛り）")
    f3 = go.Figure(go.Bar(y=[g for g, _ in mc.GAPS], x=[h for _, h in mc.GAPS], orientation="h",
                          marker_color=[RED, BLUE, BLUE], text=[f"{h:,.0f} 時間" for _, h in mc.GAPS], textposition="outside"))
    f3.update_layout(height=260, margin=dict(t=20, b=10, l=10, r=60),
                     xaxis=dict(type="log", title="時間（対数の目盛り）", tickvals=[10, 100, 1000, 10000],
                                ticktext=["10時間", "100時間", "1000時間", "1万時間"], range=[1, 4.6]))
    st.plotly_chart(f3, width="stretch")
    st.caption("30時間・49日・2年。『最初の揺れがおさまったら終わり』とは限らない。救援・物流が動き出したころに2つ目が来ることがある。")

st.markdown("#### いまの公的な見積もり")
m1, m2, m3 = st.columns(3)
m1.markdown(f"30年以内に起きる確率  \n### {mc.NANKAI_PROB_30Y[0]}  \n別の計算方法では **{mc.NANKAI_PROB_30Y[1]}**")
m2.metric("最大クラスの死者（最悪の場合）", f"約{mc.DAMAGE_2025['deaths'] / 10000:.1f}万人",
          f"災害関連死 約{mc.DAMAGE_2025['related_deaths'] / 10000:.1f}万人", delta_color="off", delta_arrow="off")
m3.metric("経済被害", f"約{mc.DAMAGE_2025['economic_trillion_yen']}兆円")
st.caption("出どころ：地震調査委員会（2025年9月、2つの計算方法の値を併記）、内閣府の被害想定（2025年3月）。")
with st.expander("『30年で〇%』を、もっと短い期間に直すと？（説明用の近似）"):
    p30 = st.slider("30年以内の確率（%）", 20, 90, 60, 5, key="mg_p30") / 100
    yrs = st.slider("何年以内？", 1, 30, 5, key="mg_years")
    st.metric(f"{yrs}年以内に起きる確率（近似）", f"{mc.prob_within(yrs, p30):.0%}")
    st.caption("毎年同じ起こりやすさと仮定した近似（ポアソンの考え方）。実際の計算は、前回からの時間がたつほど上がる模型を使っている。")

ui.exam_question("mega_rekishi", dict(
    p="P3", subject="地学基礎 × 情報Ⅰ",
    q="1707年の宝永地震では、49日後に富士山が噴火した。このことから言えることとして最も適切なものはどれか。",
    opts=["南海トラフ地震が起きれば、必ず49日後に富士山が噴火する",
          "南海トラフ地震と富士山の噴火には、まったく関係がない",
          "1854年の安政の地震のあとには噴火しておらず、1つの例だけでは『必ず続く』とも『関係ない』とも言えない",
          "富士山が噴火すれば、必ず南海トラフ地震が起きる"],
    ans="1854年の安政の地震のあとには噴火しておらず、1つの例だけでは『必ず続く』とも『関係ない』とも言えない",
    exp="宝永（1707）は地震のあとに噴火し、安政（1854）は噴火しなかった。地下にマグマがどれだけ準備されているかなど、"
        "ほかの条件で結果が変わる。1つの例から決めつけず、『起きうる』として備える。"))
ui.reading_card(
    axis="年（横） と 地震・噴火（縦）、時間差", unit="年、時間（対数の目盛り）",
    control="そろえた：同じ南海トラフ沿いの地震。変えた：時代",
    can="間隔はおおむね100〜150年（最近ほど記録が確か）・2つ目が数十時間〜数年あとに来た例がある",
    cannot="次がいつ起きるか・次も2つに分かれるか・噴火が続くか（例が少なく、条件もちがう）",
    protocols=["P2", "P3"], material="年表と2つの棒グラフ")
ui.footer("mega_rekishi", "🔗 依存の連鎖")
