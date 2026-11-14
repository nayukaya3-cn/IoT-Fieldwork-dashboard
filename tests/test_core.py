"""計算部品の自己チェックと、出どころの値"""
import math

import backbone
import guard
import iot_core as ic
import ops_core as oc
import sister_sites


def test_self_checks():
    for m in (ic, oc, backbone, guard, sister_sites):
        m._self_check()


def test_values_match_the_sources():
    got = {m["id"]: (m["hours"], m["lectures"]) for m in ic.MATERIALS}
    assert got == {"kanki": (2.0, 45), "garden": (2.5, 35), "kit": (6.0, 48), "cad": (0.0, 0), "mlops": (2.5, 23),
                   "bio": (1.0, 25), "sour": (5.0, 105), "web": (10.0, 121), "marche": (3.5, 22), "fukushi": (0.0, 0)}
    assert ic.BUDGET_RANGE == (20000, 30000)
    assert ic.LIMITS == {"建築物衛生法（事務所など）": 1000, "学校環境衛生基準（教室）": 1500}
    assert ic.VENT_PER_PERSON == 30 and (ic.HOUSE["width"], ic.HOUSE["length"]) == (5.5, 15.0)


def test_ventilation_model_is_consistent():
    a, b = ic.steady_ppm(40, 600), ic.steady_ppm(40, 1200)
    assert math.isclose(a - ic.OUTDOOR_PPM, 2 * (b - ic.OUTDOOR_PPM))
    assert math.isinf(ic.minutes_to_reach(1500, 40, 180, ic.required_vent(40, 1400)))


def test_health_flags_each_fault_separately():
    """故障を1つずつ入れると、その故障だけが見つかる"""
    base = dict(outage=None, stuck_day=None, spikes=0, drift_ppm_per_day=0.0)
    assert oc.health(oc.synth_week(**base), 10)["issues"] == []
    only = {
        "outage": ({**base, "outage": (1, 9.0, 11.0)}, "記録が止まった"),
        "stuck": ({**base, "stuck_day": 5}, "同じ値"),
        "spikes": ({**base, "spikes": 3}, "ありえない値が 3 件"),
        "drift": ({**base, "drift_ppm_per_day": 30.0}, "夜の基準線"),
    }
    for name, (kw, word) in only.items():
        issues = oc.health(oc.synth_week(**kw), 10)["issues"]
        assert len(issues) == 1 and word in issues[0][1], (name, issues)


def test_csv_reader_rejects_and_cleans():
    df, _ = oc.read_csv_bytes("時刻,CO2\n2026-11-16 00:00,500\n2026-11-16 00:10,=1+1\n2026-11-16 00:20,510\n".encode())
    assert df["CO2"].isna().sum() == 1                       # 数式のような文字は数字として読まない
    df, notes = oc.read_csv_bytes("時刻,CO2\n2026-11-16 00:00,500\n2026-11-16 00:10,505\n".encode())
    assert oc.health(df, oc.guess_interval(df["時刻"]))["uptime"] == 1.0


def test_no_names_of_courses_or_people():
    """講座名・講師名・事業所名・講座のURLを持ちこんでいない"""
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    for p in [*root.glob("*.py"), *(root / "pages").glob("*.py")]:
        text = p.read_text(encoding="utf-8")
        for word in ("udemy", "Udemy", "大手町", "株式会社"):
            assert word not in text, (p.name, word)
