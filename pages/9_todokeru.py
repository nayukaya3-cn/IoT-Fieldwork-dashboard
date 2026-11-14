"""🛒 届ける：育てた物・わかった事を、言えることだけで伝える"""
import pandas as pd
import streamlit as st

import guard
import ops_core as oc
import ui

ui.hero("段8 届ける ｜ 終章（これからの科学と人間生活）× 情報Ⅰ 情報デザイン・メディアの特性",
        "🛒 届ける：測った記録を、伝わる言葉にする",
        "育てた麦・焼いたパンを、写真と文章で届ける。科学の出番は『言えること／言えないこと』を分けるところ。"
        "測った物は数字で言える。測っていない物は言わない。", stage="届ける")

st.markdown("#### 最初の1個を売るまでの段取り")
st.dataframe(pd.DataFrame(oc.FIRST_SALE_STEPS, columns=["段取り", "やること", "データ（このダッシュボード）とのつながり"]),
             hide_index=True, width="stretch")
st.caption("出どころ：作成者がまとめた直売の資料の概要を、自分の言葉で8段に整理したもの。")

st.markdown("#### 記録から『言える1文』をつくる")
df, label, synthetic = ui.week_data("td_data")
cols = [c for c in df.columns if c != "時刻"]
col = st.selectbox("どの記録を使う？", cols, index=0, key="td_col")
sentence = oc.evidence_sentence(df, col)
st.info(sentence, icon="📏")
if synthetic:
    st.caption("🧪 これは架空データから作った文です。実際の説明文には、自分たちの記録から作った文だけを使う。")

st.markdown("#### 商品説明の下書き")
with st.form("td_form"):
    a1, a2 = st.columns(2)
    name = a1.text_input("名前", "三原西部の小麦（ミナミノカオリ）", max_chars=40)
    who = a2.text_input("だれに", "おうちでパンを焼く人", max_chars=60)
    joy = st.text_input("何がうれしいか", "粉の香りが立ち、焼き色がこんがりつく", max_chars=100)
    use_ev = st.checkbox("根拠として、上の『言える1文』を入れる", value=not synthetic)
    howto = st.text_input("食べ方・保存", "冷暗所で保存し、開けたら早めに使う", max_chars=100)
    extra = st.text_area("自由に書き足す（試しに『日本一』『無農薬』『栄養たっぷり』などを入れてみる）",
                         "日本一の香り！栄養たっぷり。", max_chars=300, height=70)
    go_btn = st.form_submit_button("下書きをつくって点検する")
draft = oc.product_text(guard.clean_text(name, 40), guard.clean_text(who, 60), guard.clean_text(joy, 100),
                        sentence if use_ev and not synthetic else "", guard.clean_text(howto, 100))
draft = draft + ("\n" + guard.clean_text(extra, 300) if extra.strip() else "")
st.code(draft, language="text")
flags = oc.flag_words(draft)
if flags:
    st.error(f"気をつける言葉が {len(flags)} か所あります。言いかえるか、根拠を足すか、消す。")
    st.dataframe(pd.DataFrame(flags, columns=["言葉", "なぜ気をつけるか"]), hide_index=True, width="stretch")
else:
    st.success("決まった形で探した範囲では、気をつける言葉は見つからなかった（見落としはありうる。人の目でも読む）。")
if use_ev and synthetic:
    st.warning("架空データの文は、説明文に入れていません。自分たちのCSVを「📈 見る」で読みこむと入れられます。")
st.download_button("⬇️ 下書き（テキスト）", draft.encode("utf-8"), "setsumei_shitagaki.txt", "text/plain")
ui.hint("『測った数字』は強い根拠になる。ただし数字が言えるのは『このハウスで、この期間、こう記録された』ことまで。"
        "おいしさや体への効き目は、温度の記録からは言えない。")
ui.reading_card(
    axis="説明文の言葉 と その根拠", unit="（文の中の数字には単位をつける）",
    control="そろえた：同じ品物・同じ記録。変えた：言い方",
    can="記録した期間・間隔・値の範囲（例：夜の最低の中央値）",
    cannot="ほかの農家より優れていること（くらべていない）・体への効き目・栄養の多さ（測っていない）",
    protocols=["P3", "P2"], material="説明文と点検の表")
st.caption("言葉の点検は、決まった形を探す補助です。表示のルール（食品表示・農産物の表示ガイドライン・有機JAS）は、使う前に公的な資料で確かめてください。")
ui.footer("todokeru")
