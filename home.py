"""ホーム：問いと、8つの段の歩き方"""
import streamlit as st

import iot_core as ic
import sister_sites as ss
import ui

ui.hero("三原西部のハウス（5.5m×15m）・圃場 × 科学と人間生活 × 情報Ⅰ",
        f"📡 {ic.TITLE}",
        f"❓ {ic.LEAD_QUESTION}")
ui.hint(ic.EASY_WORDS)

a, b, c = st.columns(3)
with a.container(border=True):
    st.markdown("**📡 IoTアプリ構築**")
    st.caption("センサー・小型コンピュータ・クラウドの表・メール・ポンプ・3Dプリンタの部品。1台2〜3万円の目安で作る。")
with b.container(border=True):
    st.markdown("**🔁 運用支援**")
    st.caption("止まった・固まった・ずれた、を毎週見つけて直す。1周ごとに変えるのは1か所。引きつぎ書で次の人へ。")
with c.container(border=True):
    st.markdown("**🌾 フィールドワーク実践**")
    st.caption("ハウスと畑で、数字と実物を見くらべる。何を測れば何が言えるかは、理科（科学と人間生活）が決める。")

st.subheader("🗺️ 8つの段を一周する")
st.graphviz_chart("""
digraph G {
  rankdir=LR; node [shape=box, style="rounded,filled", fontname="sans-serif", fontsize=11, color="#3f6584", margin="0.25,0.1"];
  edge [color="#3f6584", fontsize=9];
  a [label="📏 測る", fillcolor="#dcebf5"]; b [label="🗄️ 貯める", fillcolor="#dcebf5"]; c [label="📈 見る", fillcolor="#dcebf5"];
  d [label="🔔 知らせる", fillcolor="#dcebf5"]; e [label="💧 動かす", fillcolor="#dcebf5"];
  f [label="🖨️ つくる", fillcolor="#e3efd6"]; g [label="🔁 運用する", fillcolor="#fdecc8"]; h [label="🛒 届ける", fillcolor="#e3efd6"];
  a -> b -> c -> d -> e; f -> a [label="カバー・台"]; e -> g; c -> g; g -> a [style=dashed, label="1か所だけ直す"]; g -> h [label="記録が根拠"];
}
""", width="stretch")

st.subheader("このダッシュボードの歩き方")
st.table({
    "段": ["🗺️ 地図と学習計画", "📏 測る", "🗄️ 貯める", "📈 見る", "🔔 知らせる", "💧 動かす", "🖨️ つくる", "🔁 運用する", "🛒 届ける"],
    "問い": ["どの資料で、どの段を学ぶ？", "40人の教室は何分で1500ppm？ ハウスはなぜ足りなくなる？", "番地は2進数で何？ 表はいつ満杯？",
           "平均と中央値、どちらを信じる？（自分のCSVも読める）", "誤報は1日何回？ 鳴った警報は本当？", "しきい値は1本と2本、どちらが落ち着く？",
           "図面どおりだとなぜ入らない？ 1台いくら？", "1週間で、いつ止まり、何がずれた？", "記録から、何を言える？ 何を言えない？"],
    "情報Ⅰ": ["─", "モデル化とシミュレーション", "2進数・ネットワーク", "データの活用", "条件分岐・確率", "アルゴリズム・制御",
             "知的財産権", "情報セキュリティ・保守", "情報デザイン"],
})

with st.container(border=True):
    st.markdown("### 🦴 どのページでも同じ『考え方の型』")
    st.markdown("各ページの最後に **🔎 読解カード**（軸・単位・統制・言える／言えない）と、途中に **🎯 先に予想しよう** があります。"
                "姉妹サイト「科学と人間生活 × 情報Ⅰ」と同じ言葉・同じ形です。")

with st.container(border=True):
    st.markdown("### 🔒 このダッシュボードが扱わないもの")
    st.markdown("- 実機・クラウドには**つながない**（グラフは架空データか、手元で読みこんだCSV）  \n"
                "- **鍵・パスワード・トークンの入力欄はない**（公開前の点検はファイル名だけで行う）  \n"
                "- 入力・読みこんだCSVは**このセッションの中だけ**で使い、保存も送信もしない")

st.subheader("🔗 姉妹サイト")
n1, n2 = st.columns(2)
for col, key in ((n1, "tanpaku"), (n2, "bakery")):
    s = ss.SITES[key]
    with col.container(border=True):
        st.markdown(f"**{s['icon']} {s['name']}**")
        st.caption(s["role"])
        st.link_button("開く ↗", ss.url(key), width="stretch")
