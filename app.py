"""
IoTアプリ構築・運用支援 ＝ フィールドワーク実践 ─ 入口（左メニューの組み立て）

起動: streamlit run app.py
  ホームは home.py、各ページは views/（pages/ という名前にしない：Streamlit が自動で読みこみ、
  URLを直接開いたときに左メニューがファイル名の一覧に置きかわるため）、計算部品は iot_core.py（測る〜つくる）と ops_core.py（運用・届ける）。
左メニューは8つの段の順、そのあとにメガリスク（南海トラフ地震＋富士山噴火）への備え。ページを足すときは NAV に1行足すだけ（ファイルが無い行は自動で飛ばす）。
"""
import importlib
from pathlib import Path

import streamlit as st

import backbone
import guard
import iot_core
import mega_core
import ops_core
import sister_sites as ss
import ui

# Streamlit Cloud が古いモジュールを読みこんだまま app.py だけ新しくなったときの対策
if getattr(ui, "API_VERSION", 0) < 1:
    for _m in (iot_core, mega_core, ops_core, backbone, guard, ss, ui):
        importlib.reload(_m)

ROOT = Path(__file__).parent
st.set_page_config(page_title="IoTアプリ構築・運用支援 ＝ フィールドワーク実践", page_icon="📡", layout="wide")

NAV = {
    "📡 はじめに": [
        ("home.py", "ホーム（問いと歩き方）", "🏠"),
        ("views/1_chizu.py", "地図と学習計画", "🗺️"),
    ],
    "🔧 しくみを作る（5つの段）": [
        ("views/2_hakaru.py", "測る：CO2と換気", "📏"),
        ("views/3_tameru.py", "貯める：番地と表", "🗄️"),
        ("views/4_miru.py", "見る：代表値・CSV読みこみ", "📈"),
        ("views/5_shiraseru.py", "知らせる：誤報とまとめ", "🔔"),
        ("views/6_ugokasu.py", "動かす：自動水やり", "💧"),
    ],
    "🌾 回して・届ける（3つの段）": [
        ("views/7_tsukuru.py", "つくる：設計と費用", "🖨️"),
        ("views/8_unyo.py", "運用する：健康診断・点検", "🔁"),
        ("views/9_todokeru.py", "届ける：言えることで伝える", "🛒"),
    ],
    "🌋 メガリスクに備える（実験的プロトタイプ）": [
        ("views/11_mega_rekishi.py", "歴史と連動：時間差", "🌊"),
        ("views/12_mega_rensa.py", "依存の連鎖と降灰", "🔗"),
        ("views/13_mega_bichiku.py", "備蓄と途絶：確率で備える", "📦"),
        ("views/14_mega_iot.py", "止まらないIoT", "🔋"),
        ("views/15_mega_jikyu.py", "自給の基盤：麦からパン", "🌾"),
    ],
    "🧑‍🏫 先生・支援者向け": [
        ("views/10_kyoin.py", "構成・役割・安全", "🧑‍🏫"),
    ],
}


def build_nav() -> dict[str, list]:
    nav = {}
    for section, items in NAV.items():
        pages = [st.Page(path, title=title, icon=icon, default=(path == "home.py"))
                 for path, title, icon in items if (ROOT / path).exists()]
        if pages:
            nav[section] = pages
    return nav


with st.sidebar:
    st.toggle("やさしい解説を表示", value=True, key=ui.EASY_KEY)
    st.caption("三原西部のハウス（5.5m×15m）でIoTを作り、測り、運用し、育てた物を届ける。")
    if st.session_state.get(ui.USER_DF_KEY) is not None:
        st.caption(f"📄 読みこんだCSV：{len(st.session_state[ui.USER_DF_KEY]):,} 行（このセッションの中だけ）")
    _n = len(st.session_state.get(ui.TD_LOG_KEY, {}))
    if _n:
        st.caption(f"🎯 このセッションの予想：{_n} 件（保存はしません）")
    st.divider()
    st.markdown("**🔗 姉妹サイト**")
    for _k in ("tanpaku", "bakery"):
        _s = ss.SITES[_k]
        st.link_button(f"{_s['icon']} {_s['name']} ↗", ss.url(_k), width="stretch")

st.navigation(build_nav()).run()
