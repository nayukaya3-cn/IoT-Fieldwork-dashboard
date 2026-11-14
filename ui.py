"""
画面の共通部品（どのページでも同じ見た目・同じ言葉にする）
  - hero(): ページ上部の見出しカード（8つの段のどこにいるかも表示）
  - hint(): 「やさしい解説」スイッチがONのときだけ出す説明
  - reading_card(): 読解カード（4項目）。姉妹サイトと同じ見た目・同じ言葉
  - predict(): 先に予想 → 答え → ずれ δ（記録はこのセッションの中だけ）
  - exam_question(): 共通テスト型問題（P1〜P5 のラベルつき）
  - footer(): つながるページ（このサイト内・姉妹サイト）
"""
from __future__ import annotations

import html

import streamlit as st

import backbone as bb
import iot_core as ic
import sister_sites as ss

API_VERSION = 1
EASY_KEY = "easy_mode"
TD_LOG_KEY = "td_log"

_CSS = """
<style>
.hero {padding: 1.3rem 1.5rem 1.1rem; border-radius: 16px;
       background: linear-gradient(120deg, #dcebf5 0%, #e3efd6 100%); color: #1f3142; margin-bottom: .8rem;}
.hero .eyebrow {font-size: .85rem; letter-spacing: .06em; color: #3f6584; margin: 0 0 .3rem 0;}
.hero h1 {margin: 0 0 .45rem 0; font-size: 1.6rem; line-height: 1.35; color: #1f3142;}
.hero .lead {margin: 0; font-size: 1.0rem; line-height: 1.8;}
.stage {display:inline-block; padding:2px 9px; margin:0 3px 4px 0; border-radius:10px; font-size:.78rem;
        background:#eef2f5; color:#7a8a99;}
.stage.on {background:#2f6f4f; color:#fff; font-weight:700;}
.pbadge {display:inline-block; padding:1px 8px; margin-right:4px; border-radius:10px;
         background:#dcebf5; color:#1f3142; font-size:.8rem; font-weight:600;}
</style>
"""


def stage_bar(current: str | None) -> str:
    return "".join(f"<span class='stage{' on' if s == current else ''}'>{html.escape(s)}</span>" for s in ic.STAGE_NAMES)


def hero(eyebrow: str, title: str, lead: str, stage: str | None = None) -> None:
    st.markdown(_CSS, unsafe_allow_html=True)
    st.markdown(
        f"<div class='hero'><p class='eyebrow'>{html.escape(eyebrow)}</p>"
        f"<h1>{html.escape(title)}</h1><p class='lead'>{html.escape(lead)}</p>"
        f"<div style='margin-top:.7rem'>{stage_bar(stage)}</div></div>",
        unsafe_allow_html=True,
    )


def easy() -> bool:
    return st.session_state.get(EASY_KEY, True)


def hint(text: str) -> None:
    if easy():
        st.info(text, icon="💡")


def badges(codes: list[str]) -> str:
    return "".join(f"<span class='pbadge'>{html.escape(bb.p_label(c))}</span>" for c in codes)


def reading_card(axis: str, unit: str, control: str, can: str, cannot: str,
                 protocols: list[str], material: str = "このページの図・表") -> None:
    st.markdown(_CSS, unsafe_allow_html=True)
    answers = (axis, unit, control, f"**言える**：{can}  \n**言えない**：{cannot}")
    with st.container(border=True):
        st.markdown(f"**🔎 読解カード**　{badges(protocols)}", unsafe_allow_html=True)
        st.caption(f"読むもの：{material}。野帳・共通テストの図表・姉妹サイトでも、同じ4項目で読む。")
        st.markdown("  \n".join(f"{i}. {q}" for i, (_, q) in enumerate(bb.READING_CARD, 1)))
        with st.expander("答え合わせ（自分で考えてから開く）"):
            for (name, _), a in zip(bb.READING_CARD, answers):
                st.markdown(f"**{name}**　{a}")


def predict(key: str, question: str, actual: float, unit: str, *, protocol: str = "P4",
            min_value: float = 0.0, max_value: float = 100.0, step: float = 1.0,
            value: float | None = None, fmt: str = "%.0f", field: str = "") -> dict | None:
    """先に予想させ、答えとのずれ δ を見せる。記録はこのセッションの中だけ（保存・送信しない）"""
    log = st.session_state.setdefault(TD_LOG_KEY, {})
    st.markdown(_CSS, unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown(f"**🎯 先に予想しよう**　{badges([protocol])}", unsafe_allow_html=True)
        st.markdown(question)
        with st.form(f"pred_{key}"):
            guess = st.number_input(f"あなたの予想（{unit}）", min_value=min_value, max_value=max_value,
                                    value=min_value if value is None else value, step=step, format=fmt)
            done = st.form_submit_button("予想を確定して答えを見る")
        if done:
            log[key] = bb.log_record(field, protocol, float(guess), float(actual), unit)
            log[key]["question"] = question
        rec = log.get(key)
        if rec is None:
            st.caption("予想を書いてから答えを見ると、ずれ（δ）が学びの入口になる。")
            return None
        d = rec["td_error"]
        c1, c2, c3 = st.columns(3)
        c1.metric("あなたの予想", f"{rec['predicted']:g} {unit}")
        c2.metric("答え", f"{actual:.3g} {unit}")
        c3.metric("ずれ δ", f"{d:.2f}", help="δ＝|答え−予想|÷|予想|")
        if d < 0.1:
            st.success("ほぼ予想どおり。なぜ当てられたのか、根拠を1行で言えるかな？")
        elif d < 0.5:
            st.warning("少しずれた。どこで見込みがちがったか考えよう。")
        else:
            st.error("大きくずれた！ ここがいちばんの学びどころ。")
        st.text_input("ずれの理由（1行：考え方／測り方／自然のばらつき）", key=f"why_{key}", max_chars=200)
        return rec


def exam_question(key: str, item: dict) -> bool | None:
    st.markdown(_CSS, unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown(f"**📝 共通テスト型問題**（{html.escape(item['subject'])}）　{badges([item['p']])}",
                    unsafe_allow_html=True)
        choice = st.radio(item["q"], item["opts"], index=None, key=f"exam_{key}")
        if choice is None:
            st.caption("読解カードの4項目（とくに③ 何をそろえ、何を変えたか）で読んでから選ぼう。")
            return None
        ok = choice == item["ans"]
        (st.success if ok else st.error)(("正解！ " if ok else f"ざんねん。正解は「{item['ans']}」。") + item["exp"])
        return ok


def footer(page: str, next_label: str | None = None) -> None:
    """ページの最後：姉妹サイトへのリンクと、次の段への案内"""
    ss.render(page)
    if next_label:
        st.caption(f"➡️ 次の段：左のメニュー「{next_label}」へ")


USER_DF_KEY = "user_df"      # 「見る」ページで読みこんだ手元のCSV（このセッションの中だけ）


def week_data(key: str) -> tuple:
    """使うデータを選ぶ：架空の1週間 か、「見る」ページで読みこんだ自分たちのCSV。返り値 (表, 説明, 架空か)"""
    import ops_core as oc

    user = st.session_state.get(USER_DF_KEY)
    options = ["架空の1週間（止まった・ずれた・固まった を入れたもの）"]
    if user is not None:
        options.insert(0, "自分たちのCSV（「📈 見る」で読みこんだもの）")
    pick = st.radio("使うデータ", options, horizontal=True, key=key)
    if pick.startswith("自分たち"):
        return user, "自分たちのCSV", False
    st.caption("🧪 架空データです。「📈 見る」でCSVを読みこむと、自分たちのデータに切りかえられます。")
    return oc.synth_week(), "架空の1週間", True
