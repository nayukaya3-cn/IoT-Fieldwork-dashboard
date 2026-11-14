"""メガリスク（実験的プロトタイプ）のテスト：出どころの値・連鎖・確率・画面の動き"""
from pathlib import Path

import numpy as np
from streamlit.testing.v1 import AppTest

import mega_core as mc

ROOT = Path(__file__).resolve().parents[1]


def _run(page, monkeypatch):
    monkeypatch.chdir(ROOT)
    monkeypatch.syspath_prepend(str(ROOT))
    return AppTest.from_file(str(ROOT / page), default_timeout=90).run()


def test_self_check():
    mc._self_check()


def test_public_values():
    """公的な資料の値と、利用者がくれた安政の記録"""
    assert mc.NANKAI_PROB_30Y == ("60〜90%程度以上", "20〜50%")
    assert mc.DAMAGE_2025 == dict(deaths=298_000, related_deaths=52_000, economic_trillion_yen=292)
    assert [th for th, _, _ in mc.ASH_EFFECTS] == [0.1, 3.0, 30.0, 100.0, 300.0]
    assert "M8.4" in mc.ANSEI["tokai"] and "M8.4" in mc.ANSEI["nankai"] and "30時間" in mc.ANSEI["note"]


def test_each_hedge_cuts_only_its_branch():
    """備えを1つ足すと、そのノードと、その先だけが動くようになる（ほかは変わらない）"""
    base = mc.propagate(["EQ"])
    for h in mc.HEDGES:
        after = mc.propagate(["EQ"], [h])
        changed = {n for n in mc.NODES if base[n] != after[n]}
        assert all(after[n] is False for n in changed)
        assert not base[h] or h in changed


def test_more_eruption_more_shortage():
    ps = [mc.shortage(14, mc.sample_disruption(p_eruption=p))["p"] for p in (0.0, 0.3, 0.6, 0.9)]
    assert ps == sorted(ps)
    d = mc.sample_disruption()
    assert np.all(d > 0)


def test_rekishi_page(monkeypatch):
    at = _run("views/11_mega_rekishi.py", monkeypatch)
    assert not at.exception
    at.radio(key="exam_mega_rekishi").set_value(
        "1854年の安政の地震のあとには噴火しておらず、1つの例だけでは『必ず続く』とも『関係ない』とも言えない").run()
    assert any("正解" in s.value for s in at.success)


def test_rensa_bread_needs_four_hedges(monkeypatch):
    at = _run("views/12_mega_rensa.py", monkeypatch)
    assert any(m.label == "🍞 麦からパンを焼く" and m.value == "止まる" for m in at.metric)
    ms = at.multiselect(key="rs_hedges")
    want = [o for o in ms.options if any(w in o for w in ("手押しポンプ", "石臼", "サワー種", "薪窯"))]
    ms.set_value(want).run()
    assert any(m.label == "🍞 麦からパンを焼く" and m.value == "焼ける" for m in at.metric)
    at.checkbox(key="rs_ash").check().run()
    assert any(m.label == "🍞 麦からパンを焼く" and m.value == "止まる" for m in at.metric)   # 降灰で収穫が止まる


def test_bichiku_ranking_and_iot(monkeypatch):
    at = _run("views/13_mega_bichiku.py", monkeypatch)
    assert not at.exception and any("1万円あたり一番効く" in s.value for s in at.success)
    at = _run("views/14_mega_iot.py", monkeypatch)
    assert not at.exception and any("掃除する合図" in e.value for e in at.error)
    at.slider(key="mi_cover").set_value(10).run()
    assert any("まだ合図は出さない" in s.value for s in at.success)


def test_jikyu_sourdough(monkeypatch):
    at = _run("views/15_mega_jikyu.py", monkeypatch)
    assert not at.exception
    assert any("パンが焼けない" in e.value for e in at.error)      # イーストだけでは足りない（地震で電気が止まる）
    ms = at.multiselect(key="jk_hedges")
    ms.set_value([o for o in ms.options if any(w in o for w in ("手押しポンプ", "石臼", "サワー種", "薪窯"))]).run()
    assert any("パンを焼ける" in s.value for s in at.success)
