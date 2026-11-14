"""
メガリスク（南海トラフ地震 ＋ 富士山噴火）によるサプライチェーン崩壊への備え ─ 計算部品（実験的プロトタイプ）

問い：「物が届かなくなったとき、三原西部のハウスと畑は、何を・何日・何人分ささえられるか。
       そのとき IoT は止まらずに動き続けられるか」

扱うこと
  ① 歴史と連動：南海トラフ地震の繰り返しと、東西の時間差・噴火との時間差
  ② 依存の連鎖：何が止まると、何が止まるか（因果の矢印）。備え（ヘッジ）で鎖を切る
  ③ 降灰の段階：火山灰の厚さで、交通・電気・建物に何が起きるか
  ④ 備蓄と途絶：途絶日数を「確率」で考え、どの備えが1万円あたり一番効くかを比べる（モンテカルロ）
  ⑤ 止まらないIoT：停電・通信断でも測り続ける電源と記録の設計
  ⑥ 自給の基盤：播いた麦で、パンを焼くまで（収穫・製粉・酵母・窯・水）

数値の扱い
  - 公的な資料の値（出どころは各定数の横に書く）：被害想定・発生確率・降灰の影響の目安
  - それ以外（途絶日数・噴火の起こりやすさ・収量・消費電力・値段など）は**授業で話し合うための仮の値**。
    「噴火がこの確率で起きる」という予測ではない
Streamlit に依存しない。`python mega_core.py` で自己チェック。
"""
from __future__ import annotations

import math

import numpy as np

TITLE = "メガリスクに備える：サプライチェーンが止まったとき"
LEAD_QUESTION = ("物が届かなくなったとき、三原西部のハウスと畑は、何を・何日・何人分ささえられるか。"
                 "そのときIoTは止まらずに動き続けられるか？")

# ─────────────────────────────────────────────
# ① 歴史と連動
# ─────────────────────────────────────────────
#   公的な資料の値
NANKAI_PROB_30Y = ("60〜90%程度以上", "20〜50%")      # 地震調査委員会（2025年9月）：計算方法の違う2つを併記
DAMAGE_2025 = dict(deaths=298_000, related_deaths=52_000, economic_trillion_yen=292)   # 内閣府 被害想定（2025年3月）

#   (年, できごと, 種類, 次のできごととの時間差の説明)　年は資料により数え方が少しちがう
HISTORY: list[tuple[int, str, str, str]] = [
    (684, "白鳳地震", "地震", ""),
    (887, "仁和地震", "地震", ""),
    (1096, "永長地震（東側）", "地震", "約2年後に西側（康和地震 1099）"),
    (1361, "正平（康安）地震", "地震", ""),
    (1498, "明応地震", "地震", ""),
    (1605, "慶長地震", "地震", ""),
    (1707, "宝永地震（東西ほぼ同時）", "地震", "49日後に富士山の宝永噴火"),
    (1707, "富士山 宝永噴火", "噴火", "約2週間つづき、江戸にも灰が降った"),
    (1854, "安政東海地震（M8.4・東側）", "地震", "約30時間後に西側（資料により約32時間）"),
    (1854, "安政南海地震（M8.4・西側）", "地震", "富士山は噴火しなかった"),
    (1944, "昭和東南海地震（東側）", "地震", "約2年後に西側"),
    (1946, "昭和南海地震（西側）", "地震", ""),
]

#   東西（または噴火）の時間差 [時間]
GAPS: list[tuple[str, float]] = [
    ("宝永 1707：地震 → 富士山噴火", 49 * 24.0),
    ("安政 1854：東海 → 南海", 30.0),
    ("昭和 1944→1946：東南海 → 南海", 2 * 365 * 24.0),
]

ANSEI = dict(
    tokai="1854年12月23日 安政東海地震（M8.4）：紀伊半島東部沖〜駿河湾",
    nankai="1854年12月24日 安政南海地震（M8.4）：紀伊半島沖〜四国沖",
    note="約30時間の差で、東側 → 西側の順に起きた。最大の被害は天竜川河口付近。甲府・松本・福井でも被害。房総〜土佐の沿岸に津波。",
)


QUAKE_YEARS = [684, 887, 1096, 1361, 1498, 1605, 1707, 1854, 1944]   # 一連の地震の始まりの年


def intervals() -> list[int]:
    """地震の間隔 [年]。古い時代ほど記録の抜けがあるかもしれない（間隔が長く見える）"""
    return [b - a for a, b in zip(QUAKE_YEARS, QUAKE_YEARS[1:])]


def prob_within(years: float, p30: float) -> float:
    """30年以内の確率 p30 を、毎年同じ起こりやすさと仮定して years 年以内に直す（ポアソンの考え方。説明用の近似）"""
    lam = -math.log(1 - p30) / 30
    return 1 - math.exp(-lam * years)


# ─────────────────────────────────────────────
# ② 依存の連鎖（何が止まると、何が止まるか）
# ─────────────────────────────────────────────
#   id: (表示名, 種類, need)  need＝all（親が1つでも止まると止まる）／any（親のどれか1つが動けば動く）
NODES: dict[str, tuple[str, str, str]] = {
    "EQ": ("🌊 南海トラフ地震（揺れ・津波）", "災害", "all"),
    "ASH": ("🌋 富士山噴火（降灰）", "災害", "all"),
    "ROAD": ("🛣️ 道路・鉄道", "社会の基盤", "all"),
    "POWER": ("⚡ 電気（電力会社）", "社会の基盤", "all"),
    "NET": ("📶 通信（携帯・ネット）", "社会の基盤", "all"),
    "WATERWORKS": ("🚰 水道", "社会の基盤", "all"),
    "FUEL": ("⛽ 燃料（ガソリン・灯油）", "物の流れ", "all"),
    "STORE": ("🏪 店の在庫（食料・日用品）", "物の流れ", "all"),
    "FERT": ("🧪 肥料・資材", "物の流れ", "all"),
    "PARTS": ("🔩 電子部品・フィラメント", "物の流れ", "all"),
    "POST": ("📦 宅配・発送", "物の流れ", "all"),
    "PUMP": ("💧 井戸の電動ポンプ", "三原西部", "all"),
    "WATER": ("🥤 飲み水", "三原西部", "any"),
    "IOT": ("📡 IoT（測る）", "三原西部", "all"),
    "CLOUD": ("☁️ クラウドの表・メール", "三原西部", "all"),
    "ALERT": ("🔔 警報が人に届く", "三原西部", "all"),
    "HARVEST": ("🌾 麦の収穫", "三原西部", "all"),
    "MILL": ("⚙️ 製粉（電動）", "三原西部", "all"),
    "YEAST": ("🦠 パン酵母（買ったイースト）", "三原西部", "all"),
    "OVEN": ("🔥 オーブン（電気）", "三原西部", "all"),
    "BREAD": ("🍞 麦からパンを焼く", "三原西部", "all"),
    "SALES": ("🛒 直売で届ける", "三原西部", "all"),
}
EDGES: list[tuple[str, str]] = [
    ("EQ", "ROAD"), ("EQ", "POWER"), ("EQ", "NET"), ("EQ", "WATERWORKS"), ("EQ", "FUEL"),
    ("ASH", "ROAD"), ("ASH", "POWER"), ("ASH", "WATERWORKS"), ("ASH", "HARVEST"),
    ("ROAD", "STORE"), ("ROAD", "FUEL"), ("ROAD", "FERT"), ("ROAD", "PARTS"), ("ROAD", "POST"),
    ("POWER", "NET"), ("POWER", "PUMP"), ("POWER", "IOT"), ("POWER", "MILL"), ("POWER", "OVEN"),
    ("NET", "CLOUD"), ("IOT", "ALERT"), ("CLOUD", "ALERT"),
    ("WATERWORKS", "WATER"), ("PUMP", "WATER"),
    ("STORE", "YEAST"),
    ("HARVEST", "BREAD"), ("MILL", "BREAD"), ("YEAST", "BREAD"), ("OVEN", "BREAD"), ("WATER", "BREAD"),
    ("POST", "SALES"), ("NET", "SALES"),
]
#   備え（ヘッジ）：そのノードを、親が止まっても動かし続ける別の道
HEDGES: dict[str, str] = {
    "PUMP": "手押しポンプ／太陽光＋蓄電池で動かす",
    "IOT": "蓄電池＋太陽光パネル＋SDカードに記録",
    "ALERT": "現地のブザー・ランプで知らせる（ネット不要）",
    "MILL": "手回しの石臼・製粉機",
    "YEAST": "自家製のサワー種（買わずに育て続ける）",
    "OVEN": "薪窯（自家の山の薪）",
    "HARVEST": "ハウスの中でも育てる・不織布で覆う",
    "STORE": "2週間分以上の備蓄",
    "FERT": "堆肥・緑肥を自分でつくる",
    "SALES": "近所に手渡しで届ける",
}


def parents(node: str) -> list[str]:
    return [a for a, b in EDGES if b == node]


def topo_order() -> list[str]:
    """親 → 子 の順（矢印の向き）。輪になっていれば ValueError"""
    indeg = {n: 0 for n in NODES}
    for _, b in EDGES:
        indeg[b] += 1
    order, ready = [], [n for n in NODES if indeg[n] == 0]
    while ready:
        n = ready.pop(0)
        order.append(n)
        for a, b in EDGES:
            if a == n:
                indeg[b] -= 1
                if indeg[b] == 0:
                    ready.append(b)
    if len(order) != len(NODES):
        raise ValueError("依存の矢印が輪になっている")
    return order


def propagate(hazards, hedges=()) -> dict[str, bool]:
    """起きた災害（hazards）と、用意した備え（hedges）から、各ノードが『止まる（True）』かを決める"""
    hazards, hedges = set(hazards), set(hedges)
    down: dict[str, bool] = {}
    for n in topo_order():
        _, kind, need = NODES[n]
        if kind == "災害":
            down[n] = n in hazards
            continue
        ps = parents(n)
        if not ps:
            down[n] = False
        elif need == "any":
            down[n] = all(down[p] for p in ps)
        else:
            down[n] = any(down[p] for p in ps)
        if n in hedges:
            down[n] = False
    return down


def causes(node: str, hazards, hedges=()) -> list[str]:
    """そのノードを止めている、すぐ上の親（止まっているもの）"""
    d = propagate(hazards, hedges)
    return [p for p in parents(node) if d[p]]


# ─────────────────────────────────────────────
# ③ 降灰の段階（内閣府「首都圏における広域降灰対策ガイドライン」2025年3月、
#    中央防災会議 大規模噴火時の広域降灰対策検討WG 2020年4月 の目安）
# ─────────────────────────────────────────────
#   (この厚さ[mm]から, 何が起きる, 雨のときだけか)
ASH_EFFECTS: list[tuple[float, str, bool]] = [
    (0.1, "地上の鉄道が止まる（レールと車輪のすべり・通電不良）", False),
    (3.0, "停電（灰が碍子について絶縁が下がる）", True),
    (30.0, "二輪駆動の車が通れない・視界が悪くなる", False),
    (100.0, "四輪駆動の車も通れない", False),
    (300.0, "灰と雨の重みで木造家屋が倒れるおそれ", True),
]


def ash_stage(mm: float) -> tuple[str, str]:
    """(ステージ, 基本の行動)。3〜30cm のステージ2と3は被害の大きさで分かれるので、ここでは一緒に示す"""
    if mm >= 300:
        return "ステージ4（30cm以上）", "原則避難"
    if mm >= 30:
        return "ステージ2・3（3〜30cm）", "自宅などで生活を続ける（物資の供給が難しくなる）"
    if mm > 0:
        return "ステージ1（微量〜3cm）", "自宅などで生活を続ける"
    return "降灰なし", "─"


def ash_effects(mm: float, rain: bool) -> list[str]:
    return [what for th, what, rain_only in ASH_EFFECTS if mm >= th and (rain or not rain_only)]


def ash_mass_kg_m2(mm: float, density_kg_m3: float = 1000.0) -> float:
    """1㎡に積もった灰の重さ [kg]（かさ密度は乾いて約1000、ぬれると増える。仮の値）"""
    return mm / 1000 * density_kg_m3


# ─────────────────────────────────────────────
# ④ 備蓄と途絶（モンテカルロ）
# ─────────────────────────────────────────────
#   (品目, 単位, 1人1日あたり, 既定の備蓄日数)　1人1日の量は目安（飲み水3L は国の呼びかけでよく使われる目安）
ITEMS: list[tuple[str, str, float, int]] = [
    ("飲み水", "L", 3.0, 7),
    ("食料", "食", 3.0, 7),
    ("燃料（煮炊き）", "日分", 1.0, 5),
    ("電池・電源", "日分", 1.0, 3),
    ("肥料・資材（畑）", "日分", 1.0, 60),
    ("電子部品（IoTの予備）", "日分", 1.0, 30),
]
DEFAULT_SCENARIO = dict(quake_median=7.0, quake_spread=0.6, p_eruption=0.5, ash_median=14.0, ash_spread=0.6)


def sample_disruption(n: int = 20000, seed: int = 0, quake_median: float = 7.0, quake_spread: float = 0.6,
                      p_eruption: float = 0.5, ash_median: float = 14.0, ash_spread: float = 0.6) -> np.ndarray:
    """物が届かない日数のサンプル。地震だけの途絶（対数正規）＋ 確率 p_eruption で噴火の降灰による追加の途絶。
    すべて**仮定**（授業で話し合って決める）。予測ではない"""
    rng = np.random.default_rng(seed)
    q = quake_median * np.exp(quake_spread * rng.standard_normal(n))
    erupt = rng.random(n) < p_eruption
    a = ash_median * np.exp(ash_spread * rng.standard_normal(n))
    return q + erupt * a


def shortage(stock_days: float, d: np.ndarray) -> dict:
    """備蓄 stock_days 日分で、足りなくなる確率と、足りない日数の平均（期待値）"""
    lack = np.maximum(d - stock_days, 0.0)
    return dict(p=float((d > stock_days).mean()), expected=float(lack.mean()), p90=float(np.quantile(d, 0.9)))


def stock_for(p_target: float, d: np.ndarray) -> float:
    """足りなくなる確率を p_target 以下にするのに必要な備蓄日数（分布の 1−p_target 分位点）"""
    return float(np.quantile(d, 1 - p_target))


#   (備え, どの品目, 増える日数, 仮の費用[円])　値段は仮の値
HEDGE_OPTIONS: list[tuple[str, str, float, int]] = [
    ("2Lペットボトル 6本×2箱（1人）", "飲み水", 8.0, 2000),
    ("手押しポンプを井戸につける", "飲み水", 60.0, 60000),
    ("ポリタンク 20L×3（井戸水を汲みおく）", "飲み水", 20.0, 4500),
    ("主食の買いおきを1週間分ふやす（1人）", "食料", 7.0, 5000),
    ("カセットボンベ 12本", "燃料（煮炊き）", 10.0, 4000),
    ("薪窯（自家の山の薪）", "燃料（煮炊き）", 60.0, 40000),
    ("ポータブル電源＋太陽光パネル", "電池・電源", 30.0, 60000),
    ("堆肥・緑肥を自分でつくる", "肥料・資材（畑）", 120.0, 3000),
    ("センサー・基板の予備を1セット", "電子部品（IoTの予備）", 90.0, 8000),
]


def rank_hedges(stocks: dict[str, float], d: np.ndarray, options=HEDGE_OPTIONS) -> list[dict]:
    """各備えで『足りない日数の期待値』がどれだけ減るか、1万円あたりで比べる（同じサンプル d を使う＝公平な比較）"""
    out = []
    for name, item, plus, cost in options:
        before = shortage(stocks[item], d)["expected"]
        after = shortage(stocks[item] + plus, d)["expected"]
        gain = before - after
        out.append(dict(備え=name, 品目=item, 増える日数=plus, 費用=cost, 減る不足日数=round(gain, 2),
                        一万円あたり=round(gain / cost * 10000, 2) if cost else math.inf))
    return sorted(out, key=lambda r: -r["一万円あたり"])


# ─────────────────────────────────────────────
# ⑤ 止まらないIoT（停電・通信断）
# ─────────────────────────────────────────────
def avg_watt(active_w: float, sleep_w: float, active_s: float, interval_min: float) -> float:
    """測るときだけ起きて、あとは眠る（間欠動作）ときの平均消費電力 [W]"""
    period = interval_min * 60
    on = min(active_s, period)
    return (active_w * on + sleep_w * (period - on)) / period


def solar_wh_day(panel_w: float, sun_hours: float, derate: float = 0.7, ash_loss: float = 0.0) -> float:
    """太陽光パネルの1日の発電量 [Wh]。derate＝配線・充電のロス等、ash_loss＝パネルに積もった灰による低下（0〜1）"""
    return panel_w * sun_hours * derate * (1 - ash_loss)


def autonomy_days(battery_wh: float, load_w: float, solar_wh: float = 0.0, usable: float = 0.8) -> float:
    """蓄電池で動き続けられる日数。発電が消費を上回れば無限（inf）"""
    need = load_w * 24 - solar_wh
    if need <= 0:
        return math.inf
    return battery_wh * usable / need


def storage_days(capacity_gb: float, rows_per_day: float, bytes_per_row: float = 80,
                 photos_per_day: float = 0, photo_kb: float = 300) -> float:
    """SDカードに貯め続けられる日数（ネットが止まっても記録だけは残す）"""
    per_day = rows_per_day * bytes_per_row + photos_per_day * photo_kb * 1000
    return math.inf if per_day <= 0 else capacity_gb * 1e9 / per_day


def panel_soiling(measured_lux: float, expected_lux: float) -> float:
    """パネル横の照度計の値と、晴れの日のいつもの値から、灰・汚れでどれだけ光がさえぎられているか（0〜1）"""
    if expected_lux <= 0:
        return 0.0
    return float(min(max(1 - measured_lux / expected_lux, 0.0), 1.0))


# ─────────────────────────────────────────────
# ⑥ 自給の基盤：播いた麦で、パンを焼くまで
# ─────────────────────────────────────────────
WHEAT_KCAL_PER_KG = 3290      # 小麦（玄穀・国産・普通）100gあたり約329kcal（日本食品標準成分表の目安）
KCAL_PER_PERSON_DAY = 2000    # 1人1日に必要なエネルギーの目安（年齢・活動で変わる）
FLOUR_PER_LOAF_KG = 0.25      # 食パン1斤の粉の量の目安
DRINK_L_PER_PERSON_DAY = 3.0  # 飲み水の目安
#   (工程, 外から買うもの, 止まったときの別の道（ヘッジ）, 関係するノード)
WHEAT_TO_BREAD: list[tuple[str, str, str, str]] = [
    ("種をまく（11月）", "種子", "収穫から来年の種を残す", "─"),
    ("育てる", "肥料", "堆肥・緑肥", "FERT"),
    ("刈る・脱穀する（6月）", "燃料・機械", "手刈り・足踏み脱穀", "FUEL"),
    ("製粉する", "電気", "手回しの石臼", "MILL"),
    ("ふくらませる", "イースト", "自家製のサワー種", "YEAST"),
    ("焼く", "電気・ガス", "薪窯（自家の山の薪）", "OVEN"),
    ("こねる・飲む", "水道", "井戸＋手押しポンプ", "WATER"),
]


def wheat_harvest_kg(area_a: float, yield_kg_per_10a: float) -> float:
    """収穫量 [kg]。area_a はアール（1a＝100㎡、10a＝1000㎡）。収量は地域・年で大きく変わる**仮の値**"""
    return area_a / 10 * yield_kg_per_10a


def seed_keep_kg(area_a: float, seed_kg_per_10a: float) -> float:
    """来年のために残す種の量 [kg]"""
    return area_a / 10 * seed_kg_per_10a


def person_days(grain_kg: float, extraction: float = 1.0, kcal_per_kg: float = WHEAT_KCAL_PER_KG,
                kcal_per_day: float = KCAL_PER_PERSON_DAY, share: float = 1.0) -> float:
    """麦だけで、エネルギーの share（割合）をまかなうとき、何人日ささえられるか。extraction＝製粉の歩どまり"""
    return grain_kg * extraction * kcal_per_kg / (kcal_per_day * share)


def loaves(grain_kg: float, extraction: float = 1.0, flour_per_loaf: float = FLOUR_PER_LOAF_KG) -> float:
    return grain_kg * extraction / flour_per_loaf


def stock_at_month(harvest_kg: float, month: int, use_kg_per_month: float, harvest_month: int = 6) -> float:
    """発災の月に、手元に残っている麦 [kg]。収穫月（6月）にそろい、毎月 use_kg_per_month ずつ使う"""
    months_since = (month - harvest_month) % 12
    return max(harvest_kg - use_kg_per_month * months_since, 0.0)


def water_needed_l(people: int, days: float, per_day: float = DRINK_L_PER_PERSON_DAY) -> float:
    return people * days * per_day


def _self_check() -> None:
    # ① 歴史：宝永は49日、安政は約30時間
    gaps = dict(GAPS)
    assert gaps["宝永 1707：地震 → 富士山噴火"] == 49 * 24 and gaps["安政 1854：東海 → 南海"] == 30
    iv = intervals()
    assert iv[-2:] == [147, 90] and len(iv) == 8 and min(iv) == 90       # 1707→1854 147年、1854→1944 90年
    assert abs(prob_within(30, 0.8) - 0.8) < 1e-12 and prob_within(1, 0.8) < 0.06
    # ② 依存の連鎖
    assert topo_order().index("EQ") < topo_order().index("BREAD")
    d0 = propagate([])
    assert not any(d0.values())
    d1 = propagate(["EQ"])
    assert d1["POWER"] and d1["IOT"] and d1["BREAD"] and d1["WATER"] and not d1["HARVEST"]
    d2 = propagate(["EQ"], ["PUMP", "MILL", "YEAST", "OVEN"])
    assert not d2["WATER"] and not d2["BREAD"] and d2["SALES"]       # 4つの備えでパンは焼ける、届けるのは止まる
    d3 = propagate(["EQ", "ASH"], ["PUMP", "MILL", "YEAST", "OVEN"])
    assert d3["BREAD"] and causes("BREAD", ["EQ", "ASH"], ["PUMP", "MILL", "YEAST", "OVEN"]) == ["HARVEST"]
    assert not propagate(["EQ"], ["IOT", "ALERT"])["ALERT"]
    assert set(HEDGES) <= set(NODES)
    # ③ 降灰
    assert ash_stage(0)[0] == "降灰なし" and ash_stage(5)[0].startswith("ステージ1")
    assert ash_stage(30)[0].startswith("ステージ2") and ash_stage(300)[1] == "原則避難"
    assert len(ash_effects(5, rain=False)) == 1 and len(ash_effects(5, rain=True)) == 2
    assert len(ash_effects(300, rain=True)) == 5 and ash_mass_kg_m2(100) == 100
    # ④ 備蓄
    d = sample_disruption()
    only_quake = sample_disruption(p_eruption=0.0)
    assert abs(np.median(only_quake) - 7) < 0.3
    assert shortage(14, d)["p"] > shortage(14, only_quake)["p"]          # 噴火が加わると足りなくなりやすい
    s = stock_for(0.1, d)
    assert abs(shortage(s, d)["p"] - 0.1) < 0.01
    stocks = {name: days for name, _, _, days in ITEMS}
    r = rank_hedges(stocks, d)
    assert len(r) == len(HEDGE_OPTIONS) and r[0]["一万円あたり"] >= r[-1]["一万円あたり"]
    assert all(x["減る不足日数"] >= 0 for x in r)
    # ⑤ 電源
    assert abs(avg_watt(5.0, 0.5, 60, 10) - (5 * 60 + 0.5 * 540) / 600) < 1e-12
    assert math.isinf(autonomy_days(1000, 1.0, solar_wh=30))
    assert abs(autonomy_days(1200, 5.0) - 8.0) < 1e-12
    assert solar_wh_day(50, 3, 0.7, 0.5) == 52.5
    assert storage_days(32, 144) > 1e6 and 100 < storage_days(32, 144, photos_per_day=144) < 1000
    assert panel_soiling(30000, 60000) == 0.5 and panel_soiling(70000, 60000) == 0.0
    # ⑥ 自給
    assert wheat_harvest_kg(10, 300) == 300 and seed_keep_kg(10, 8) == 8
    assert abs(person_days(300) - 300 * 3290 / 2000) < 1e-9
    assert loaves(300, 0.7) == 840
    assert stock_at_month(300, 6, 20) == 300 and stock_at_month(300, 5, 20) == 80 and stock_at_month(100, 5, 20) == 0
    assert water_needed_l(4, 14) == 168


if __name__ == "__main__":
    _self_check()
    print("mega_core: 自己チェックOK")
