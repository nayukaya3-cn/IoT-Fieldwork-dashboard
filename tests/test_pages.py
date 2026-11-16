"""全ページが描画でき、主な操作で期待どおりに変わるか（Streamlit AppTest）"""
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import iot_core as ic
import ops_core as oc

ROOT = Path(__file__).resolve().parents[1]
PAGES = ["home.py", *sorted(str(p.relative_to(ROOT)) for p in (ROOT / "views").glob("*.py"))]


def _run(page, monkeypatch):
    monkeypatch.chdir(ROOT)
    monkeypatch.syspath_prepend(str(ROOT))
    return AppTest.from_file(str(ROOT / page), default_timeout=90).run()


@pytest.mark.parametrize("page", PAGES)
def test_page_renders(page, monkeypatch):
    at = _run(page, monkeypatch)
    assert not at.exception, at.exception


def test_app_entry(monkeypatch):
    at = _run("app.py", monkeypatch)
    assert not at.exception, at.exception


def test_nav_lists_every_page():
    src = (ROOT / "app.py").read_text(encoding="utf-8")
    for p in (ROOT / "views").glob("*.py"):
        assert f"views/{p.name}" in src, p.name


def test_map_gap(monkeypatch):
    at = _run("views/1_chizu.py", monkeypatch)
    assert any(m.label == "抜けている段" and "運用する" in str(m.value) for m in at.metric)
    at.multiselect(key="chizu_pick").set_value([m["name"] for m in ic.MATERIALS]).run()
    assert any(m.label == "抜けている段" and m.value == "なし" for m in at.metric)


def test_closed_classroom(monkeypatch):
    at = _run("views/2_hakaru.py", monkeypatch)
    at.slider(key="hk_vent").set_value(0).run()
    assert any(m.label == "落ち着く濃度" and m.value == "上がり続ける" for m in at.metric)
    assert any(m.label == "1500 ppm まで" and m.value == "15 分" for m in at.metric)


def test_outlier_moves_mean(monkeypatch):
    at = _run("views/4_miru.py", monkeypatch)
    at.toggle(key="mr_outlier").set_value(True).run()
    assert any("平均は" in e.value for e in at.error)


def test_uploaded_csv_flows_to_operations(monkeypatch):
    """『見る』で読みこんだCSVを、『運用する』で選べる（セッションの中だけ）"""
    at = _run("views/8_unyo.py", monkeypatch)
    at.session_state["user_df"] = oc.synth_week(days=2, outage=None, stuck_day=None, spikes=0)
    at.run()
    assert not at.exception
    opts = at.radio(key="uy_data").options
    assert any("自分たちのCSV" in o for o in opts)
    at.radio(key="uy_data").set_value(next(o for o in opts if "自分たちのCSV" in o)).run()
    assert any(m.label == "稼働率" and m.value == "100.0%" for m in at.metric)


def test_health_finds_outage(monkeypatch):
    at = _run("views/8_unyo.py", monkeypatch)
    assert any(m.label == "止まった回数" and m.value == "1 回" for m in at.metric)
    at.toggle(key="uy_out").set_value(False).run()
    assert any(m.label == "止まった回数" and m.value == "0 回" for m in at.metric)


def test_security_gate(monkeypatch):
    at = _run("views/8_unyo.py", monkeypatch)
    assert any("service_account.json" in c.value for c in at.code)
    at.checkbox(key="uy_sec_2").set_value(True).run()
    assert any("公開しない" in e.value for e in at.error)


def test_fit_and_license(monkeypatch):
    at = _run("views/7_tsukuru.py", monkeypatch)
    assert any("入らない" in e.value for e in at.error)
    at.number_input(key="tk_hole").set_value(10.4).run()
    assert any("ちょうど" in s.value for s in at.success)
    at.toggle(key="tk_cc_sell").set_value(True).run()
    assert any("できない" in e.value and "NC" in e.value for e in at.error)


def test_claims_are_checked(monkeypatch):
    at = _run("views/9_todokeru.py", monkeypatch)
    assert any("気をつける言葉" in e.value for e in at.error)       # 既定の『日本一』『栄養たっぷり』を見つける


def test_summary_mail_has_no_send(monkeypatch):
    at = _run("views/5_shiraseru.py", monkeypatch)
    assert any("【ハウスのまとめ】" in c.value for c in at.code)


def test_no_auto_pages_folder():
    """pages/ フォルダがあると、URLを直接開いたときに左メニューが自動の一覧に置きかわる"""
    assert not (ROOT / "pages").exists()


def test_url_paths_are_unique_and_short():
    """st.Page の既定の url_path（番号を除いたファイル名）が重ならない。姉妹サイトからのリンク先もここで決まる"""
    import re
    names = [re.sub(r"^\d+_", "", p.stem) for p in (ROOT / "views").glob("*.py")]
    assert len(names) == len(set(names))
    import sister_sites as ss
    for here, *_ in ss.LINKS:
        assert here in names, here


def test_outage_delays_the_notice(monkeypatch):
    """畑の実例：記録が止まった日を足さないと知らせが遅れ、うめると元にもどる"""
    at = _run("views/16_hatsuga.py", monkeypatch)
    assert any(m.label == "止まった日を足さない" and "おそい" in str(m.delta) for m in at.metric)
    assert any("おそく" in e.value for e in at.error)
    at.slider(key="hg_len").set_value(0).run()
    assert any(m.label == "止まった日を足さない" and m.delta == "ずれなし" for m in at.metric)
    assert not at.error


def test_hatsuga_core():
    import hatsuga_core as hc
    hc._self_check()
