"""
教材ネットワーク（姉妹サイト）─ このダッシュボードから見た、つながる相手

  📡 IoTフィールドワーク（このサイト）… 現場のしくみ：ハウスを測り、貯め、知らせ、運用する
  🧬 科学と人間生活 × 情報Ⅰ         … 教室：教科書の単元を Python で動かす（事前学習）
  🌾 スマートパン屋農家              … 現場：畑・パン工房で確かめる

ページのURLは「views/ のファイル名から番号を除いた部分」（st.Page の既定の url_path）。
※ フォルダ名を pages/ にしないこと：Streamlit が自動で読みこみ、URLを直接開いたときに左メニューが崩れる。
Streamlit に依存しない（render() の中だけで import する）。
"""
from __future__ import annotations

SITES: dict[str, dict] = {
    "tanpaku": {
        "name": "科学と人間生活 × 情報Ⅰ", "icon": "🧬",
        "role": "教室（事前学習）：教科書の単元をPythonで動かす。読解カードとP1〜P5はここと同じ",
        "app": "https://science-and-our-daily-life-dashboard-eemy7afzawym4gn656fjat.streamlit.app",
        "repo": "https://github.com/nayukaya3-cn/Science-and-Our-Daily-Life-dashboard",
    },
    "bakery": {
        "name": "スマートパン屋農家", "icon": "🌾",
        "role": "現場（フィールドワーク）：畑・ハウス・パン工房で確かめる",
        "app": "https://smart-bakery-farm.streamlit.app",
        "repo": "https://github.com/nayukaya3-cn/Smart-Bakery-Farmer_20260923",
    },
}

#   (このサイトのページ, 相手サイト, 相手ページ, つながる理由)
LINKS: list[tuple[str, str, str, str]] = [
    ("hakaru", "tanpaku", "biseibutsu", "発酵の速さは温度で変わる。ハウスや発酵室の温度を測る理由になる"),
    ("tsukuru", "tanpaku", "plastic", "PLAは60℃前後で柔らかくなる。夏のハウスに置く部品の材料選び"),
    ("hakaru", "tanpaku", "iot", "同じCO2の模型を、教室の授業1ページにまとめた版"),
    ("todokeru", "bakery", "", "育てた麦・焼いたパンを届ける現場"),
    ("unyo", "tanpaku", "panic", "止まっても困らない備え（パニックプルーフ）と、止まらない運用は同じ考え方"),
    ("mega_rensa", "tanpaku", "panic", "井戸・ハウスの備え（パニックプルーフ）を、依存の連鎖で見直す"),
    ("mega_jikyu", "bakery", "", "播いた麦でパンを焼く現場"),
    ("hatsuga", "tanpaku", "hatsuga", "同じ畑の記録を、教室で計算する版（気温と日数は反比例・『見た日』と『出た日』）"),
    ("hatsuga", "bakery", "", "小麦をまいた畑。今まく作物の『計画と実績』に同じ記録がある"),
    ("mega_jikyu", "tanpaku", "biseibutsu", "サワー種（自家製の酵母）と発酵の温度"),
]


def links_for(page: str) -> list[tuple[str, str, str]]:
    return [(site, p, why) for here, site, p, why in LINKS if here == page]


def url(site: str, page: str = "") -> str:
    app = SITES[site]["app"].rstrip("/")
    return f"{app}/{page}" if page else app


def render(page: str) -> None:
    import streamlit as st

    links = links_for(page)
    if not links:
        return
    with st.container(border=True):
        st.markdown("**🔗 姉妹サイトでつながるページ**")
        for site, p, why in links:
            s = SITES[site]
            c1, c2 = st.columns([4, 1])
            c1.markdown(f"{s['icon']} **{s['name']}** ─ {why}")
            c2.link_button("開く ↗", url(site, p), width="stretch")


def _self_check() -> None:
    for here, site, _p, why in LINKS:
        assert site in SITES and why and here
    assert url("bakery").startswith("https://") and url("tanpaku", "iot").endswith("/iot")


if __name__ == "__main__":
    _self_check()
    print("sister_sites: 自己チェックOK")
