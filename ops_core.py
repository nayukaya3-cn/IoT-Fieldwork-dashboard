"""
IoTアプリ構築・運用支援 ＝ フィールドワーク実践 ─ 運用・届けるの計算部品

  - 運用（見張る）：1週間分の記録の「健康診断」。止まった時間・欠測・ありえない値・張りついた値・夜の基準線のずれ
  - 見る：手元のCSV（表計算から書き出したもの）を読みこむ。サーバーには保存しない
  - 知らせる：まとめメールの文面をつくる（送信はしない。文面をコピーして使う）
  - 届ける：最初の1個を売るまでの段取り、言える／言えない表現の点検、商品説明の下書き

数値の扱い
  - 1週間分のデータは**説明用の架空データ**（iot_core.synth_day を日ごとに種を変えて並べ、停止・ずれ・誤動作をわざと入れる）
  - 「ありえない値」の範囲・「張りつき」の長さ・「ずれ」の目安は、授業で話し合って決めなおす前提の仮の値

Streamlit に依存しない。`python ops_core.py` で自己チェック。
"""
from __future__ import annotations

import io
import math
import re
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

import iot_core as ic

SENSOR_COLS = ("気温", "湿度", "照度", "CO2", "水深")
UNITS = {"気温": "℃", "湿度": "%", "照度": "lx", "CO2": "ppm", "水深": "mm"}
# ありえない値の範囲（この外は誤動作とみなす。仮の値。授業で決めなおす）
PLAUSIBLE = {"気温": (-10.0, 60.0), "湿度": (0.0, 100.0), "照度": (0.0, 150000.0), "CO2": (300.0, 5000.0),
             "水深": (0.0, 200.0)}
# CO2 だけは日中の光合成で外気より下がるので、下限は「夜の基準線」で別に見る。日中のハウスは 300ppm を切ることがある
PLAUSIBLE["CO2"] = (100.0, 5000.0)
STUCK_IGNORE = {"照度": 0.0}  # 夜の照度0は『張りつき』ではなく本当の値（暗い）。この値の連続は数えない
STUCK_ROWS = 12              # 同じ値が何行つづいたら「張りついた」とみなすか（10分おきなら2時間）
DRIFT_PPM_PER_DAY = 15.0     # 夜の基準線が1日にこれ以上動いたら「ずれ」を疑う
NIGHT_HOURS = (0, 5)         # 夜の基準線をとる時間帯（光合成がなく、換気も少ない）
START = datetime(2026, 11, 16)


# ─────────────────────────────────────────────
# 1週間分の架空データ
# ─────────────────────────────────────────────
def synth_week(days: int = 7, interval_min: int = 10, seed: int = 11, outage: tuple[int, float, float] | None = (4, 13.0, 19.0),
               drift_ppm_per_day: float = 0.0, stuck_day: int | None = 2, spikes: int = 2,
               start: datetime = START) -> pd.DataFrame:
    """1週間分の**架空データ**。
    outage＝(何日目, 止まった時刻, 戻った時刻)：その間の行がない（電源・Wi-Fiが落ちた）
    drift_ppm_per_day：CO2センサーが1日あたりこれだけ高めにずれていく
    stuck_day：その日の湿度が1つの値に張りつく（センサーが固まった）
    spikes：CO2にありえない値（9999）を何点まぜるか"""
    rng = np.random.default_rng(seed)
    frames = []
    for d in range(days):
        day = ic.synth_day(seed=seed + d, interval_min=interval_min)
        df = pd.DataFrame({k: v for k, v in day.items() if k != "時刻"})
        df.insert(0, "時刻", [start + timedelta(days=d, minutes=float(h) * 60) for h in day["時刻"]])
        df["CO2"] = df["CO2"] + drift_ppm_per_day * (d + df.index / len(df))
        if stuck_day is not None and d == stuck_day:
            df["湿度"] = round(float(df["湿度"].iloc[0]), 1)
        frames.append(df)
    out = pd.concat(frames, ignore_index=True)
    if outage is not None:
        d, h0, h1 = outage
        t0, t1 = start + timedelta(days=d, hours=h0), start + timedelta(days=d, hours=h1)
        out = out[(out["時刻"] < t0) | (out["時刻"] >= t1)].reset_index(drop=True)
    if spikes:
        idx = rng.choice(len(out), size=spikes, replace=False)
        out.loc[idx, "CO2"] = 9999.0
    for c in SENSOR_COLS:
        out[c] = out[c].round(1)
    return out


# ─────────────────────────────────────────────
# 健康診断（運用の「見張る」）
# ─────────────────────────────────────────────
def gaps(times: pd.Series, interval_min: float) -> list[dict]:
    """記録が途切れた区間。間隔が予定の1.5倍をこえたところ [{開始, 再開, 止まっていた分}]"""
    t = pd.to_datetime(times).sort_values().reset_index(drop=True)
    diff = t.diff().dt.total_seconds() / 60
    out = []
    for i in np.where(diff > interval_min * 1.5)[0]:
        out.append({"止まった直前": t[i - 1], "再開": t[i], "止まっていた分": float(diff[i] - interval_min)})
    return out


def longest_run(values, ignore: float | None = None) -> int:
    """同じ値が続いた最長の行数（欠測と ignore の値は数えない）"""
    v = pd.Series(values)
    best = cur = 0
    prev = object()
    for x in v:
        if pd.isna(x) or (ignore is not None and x == ignore):
            cur, prev = 0, object()
            continue
        cur = cur + 1 if x == prev else 1
        prev = x
        best = max(best, cur)
    return best


def night_baseline(df: pd.DataFrame, col: str = "CO2") -> pd.Series:
    """日ごとの夜（0〜5時）の中央値。ありえない値は除く"""
    t = pd.to_datetime(df["時刻"])
    lo, hi = PLAUSIBLE.get(col, (-math.inf, math.inf))
    v = df[col].where((df[col] >= lo) & (df[col] <= hi))
    mask = (t.dt.hour >= NIGHT_HOURS[0]) & (t.dt.hour < NIGHT_HOURS[1])
    return v[mask].groupby(t[mask].dt.date).median()


def drift_per_day(df: pd.DataFrame, col: str = "CO2") -> float:
    """夜の基準線の傾き [単位/日]（2日分以上ないと 0）"""
    b = night_baseline(df, col).dropna()
    if len(b) < 2:
        return 0.0
    return float(np.polyfit(np.arange(len(b)), b.to_numpy(dtype=float), 1)[0])


def health(df: pd.DataFrame, interval_min: float, cols=SENSOR_COLS) -> dict:
    """記録の健康診断。返り値：稼働率・途切れ・列ごとの欠測／範囲外／張りつき・CO2のずれ・気になる点の一覧"""
    t = pd.to_datetime(df["時刻"])
    span = (t.max() - t.min()).total_seconds() / 60 if len(t) > 1 else 0.0
    expected = int(round(span / interval_min)) + 1 if len(t) else 0
    gp = gaps(t, interval_min)
    per = {}
    issues: list[tuple[str, str, str]] = []      # (重さ, 何が, どうする)
    for c in cols:
        if c not in df:
            continue
        v = pd.to_numeric(df[c], errors="coerce")
        lo, hi = PLAUSIBLE.get(c, (-math.inf, math.inf))
        oor = int(((v < lo) | (v > hi)).sum())
        run = longest_run(v, STUCK_IGNORE.get(c))
        per[c] = {"欠測": int(v.isna().sum()), "範囲外": oor, "最長の張りつき（行）": run}
        if oor:
            issues.append(("⚠️ 注意", f"{c}：ありえない値が {oor} 件", "その時刻の写真・作業記録を見る。まとめでは中央値を使う"))
        if run >= STUCK_ROWS:
            issues.append(("⚠️ 注意", f"{c}：同じ値が {run} 行つづいた（約 {run * interval_min / 60:.0f} 時間）",
                           "センサーが固まった可能性。差しなおし・再起動して、値が動くか確かめる"))
        if v.isna().any():
            issues.append(("ℹ️ 記録", f"{c}：欠測が {int(v.isna().sum())} 件", "0 で埋めずに空欄のまま残す"))
    for g in gp:
        sev = "🛑 停止" if g["止まっていた分"] >= 60 else "ℹ️ 記録"
        issues.append((sev, f"{g['止まった直前']:%m/%d %H:%M} から約 {g['止まっていた分']:.0f} 分、記録が止まった",
                       "電源・Wi-Fi・表の書きこみ（鍵の期限）の順に確かめる"))
    drift = drift_per_day(df) if "CO2" in df else 0.0
    if abs(drift) >= DRIFT_PPM_PER_DAY:
        issues.append(("⚠️ 注意", f"CO2：夜の基準線が1日に {drift:+.0f} ppm ずつ動いている",
                       "センサーのずれ（校正）か、夜の換気・作物の量が変わったかを分ける。外気で数分測って比べる"))
    order = {"🛑 停止": 0, "⚠️ 注意": 1, "ℹ️ 記録": 2}
    issues.sort(key=lambda x: order[x[0]])
    return dict(rows=len(df), expected=expected, uptime=len(df) / expected if expected else 0.0, gaps=gp, per=per,
                drift=drift, issues=issues, start=t.min() if len(t) else None, end=t.max() if len(t) else None)


def for_plot(df: pd.DataFrame, col: str, interval_min: float) -> pd.DataFrame:
    """グラフ用：ありえない値を空欄にし、記録が止まった所に空欄の行をはさむ（線が止まった時間をまたいでつながらないように）"""
    t = pd.to_datetime(df["時刻"])
    v = pd.to_numeric(df[col], errors="coerce")
    lo, hi = PLAUSIBLE.get(col, (-math.inf, math.inf))
    out = pd.DataFrame({"時刻": t, col: v.where((v >= lo) & (v <= hi))})
    breaks = [{"時刻": g["止まった直前"] + timedelta(minutes=interval_min), col: np.nan} for g in gaps(t, interval_min)]
    if breaks:
        out = pd.concat([out, pd.DataFrame(breaks)], ignore_index=True)
    return out.sort_values("時刻").reset_index(drop=True)


def daily_table(df: pd.DataFrame, cols=SENSOR_COLS) -> pd.DataFrame:
    """日ごとの行数・平均・最小・最大（ありえない値は除く）"""
    t = pd.to_datetime(df["時刻"])
    rows = []
    for day, g in df.groupby(t.dt.date):
        r = {"日付": str(day), "行数": len(g)}
        for c in cols:
            if c not in g:
                continue
            lo, hi = PLAUSIBLE.get(c, (-math.inf, math.inf))
            v = pd.to_numeric(g[c], errors="coerce")
            v = v[(v >= lo) & (v <= hi)]
            r[f"{c} 平均"] = round(float(v.mean()), 1) if len(v) else None
            r[f"{c} 最小"] = round(float(v.min()), 1) if len(v) else None
            r[f"{c} 最大"] = round(float(v.max()), 1) if len(v) else None
        rows.append(r)
    return pd.DataFrame(rows)


# ─────────────────────────────────────────────
# まとめメールの文面（送らない。文面をつくるだけ）
# ─────────────────────────────────────────────
def summary_mail(df: pd.DataFrame, day, interval_min: float, thresholds: dict[str, tuple[float | None, float | None]]) -> str:
    """その日のまとめ。ありえない値は除き、代表値は中央値。しきい値をこえた回数も書く"""
    t = pd.to_datetime(df["時刻"])
    g = df[t.dt.date == day]
    lines = [f"【ハウスのまとめ】{day}", f"記録：{len(g)} 行（予定 {int(1440 / interval_min)} 行）", ""]
    for c in SENSOR_COLS:
        if c not in g:
            continue
        lo, hi = PLAUSIBLE[c]
        v = pd.to_numeric(g[c], errors="coerce")
        bad = int(((v < lo) | (v > hi)).sum())
        v = v[(v >= lo) & (v <= hi)]
        if v.empty:
            lines.append(f"・{c}：記録なし")
            continue
        s = f"・{c}：中央値 {v.median():.0f} {UNITS[c]}（最小 {v.min():.0f}〜最大 {v.max():.0f}）"
        low, high = thresholds.get(c, (None, None))
        over = []
        if low is not None and (v < low).any():
            over.append(f"{low:g} 未満 {int((v < low).sum())} 回")
        if high is not None and (v > high).any():
            over.append(f"{high:g} 超 {int((v > high).sum())} 回")
        if over:
            s += "　⚠ " + "・".join(over)
        if bad:
            s += f"　（ありえない値 {bad} 件は除いた）"
        lines.append(s)
    lines += ["", "※ 数字と実物を見くらべに、一度ハウスへ。鍵・パスワード・個人の連絡先はこの文面に書かない。"]
    return "\n".join(lines)


# ─────────────────────────────────────────────
# 手元のCSVを読む（サーバーに保存しない）
# ─────────────────────────────────────────────
MAX_ROWS = 100_000
MAX_BYTES = 1_000_000        # .streamlit/config.toml の maxUploadSize（1MB）と同じ


def read_csv_bytes(data: bytes) -> tuple[pd.DataFrame, list[str]]:
    """CSV（UTF-8 か Shift_JIS）を読み、時刻の列を見つけて『時刻』に、数字の列を数値にする。
    返り値：(表, 気づいたことのメモ)。形がおかしければ ValueError"""
    if len(data) > MAX_BYTES:
        raise ValueError("ファイルが大きすぎます（1MBまで）。期間を区切って書き出してください。")
    text = None
    for enc in ("utf-8-sig", "cp932"):
        try:
            text = data.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    if text is None:
        raise ValueError("文字コードが読めません（UTF-8 か Shift_JIS で保存してください）。")
    try:
        raw = pd.read_csv(io.StringIO(text), nrows=MAX_ROWS + 1, dtype=str)
    except Exception as e:  # pandas の細かい例外を、利用者向けの言葉にまとめる
        raise ValueError("CSVとして読めません。1行目が列名、2行目からデータの形か確かめてください。") from e
    notes = []
    if len(raw) > MAX_ROWS:
        raw = raw.iloc[:MAX_ROWS]
        notes.append(f"{MAX_ROWS:,} 行をこえた分は読みこんでいません。")
    raw.columns = [re.sub(r"[\x00-\x1f]", "", str(c)).strip()[:40] or f"列{i + 1}" for i, c in enumerate(raw.columns)]
    time_col = None
    named = [c for c in raw.columns if re.search(r"時刻|日時|日付|時間|time|date", c, re.I)]
    for c in named + [c for c in raw.columns if c not in named]:
        col = raw[c].dropna()
        if col.empty or col.str.contains(r"[/\-:年]").mean() < 0.6:   # 数字だけの列（CO2など）を時刻とまちがえない
            continue
        if pd.to_datetime(col, errors="coerce", format="mixed").notna().mean() >= 0.6:
            time_col = c
            break
    if time_col is None:
        raise ValueError("時刻の列が見つかりません（例：2026/11/16 08:10 の形の列を入れてください）。")
    out = pd.DataFrame({"時刻": pd.to_datetime(raw[time_col], errors="coerce", format="mixed")})
    for c in raw.columns:
        if c == time_col:
            continue
        num = pd.to_numeric(raw[c].str.replace(",", "", regex=False), errors="coerce")
        if num.notna().mean() >= 0.5:
            out[c] = num
        else:
            notes.append(f"「{c}」は数字が少ないので使いません。")
    bad_t = int(out["時刻"].isna().sum())
    if bad_t:
        notes.append(f"時刻が読めない行 {bad_t} 行を除きました。")
    out = out.dropna(subset=["時刻"]).sort_values("時刻").reset_index(drop=True)
    if len(out.columns) < 2:
        raise ValueError("数字の列が見つかりません。")
    return out, notes


def guess_interval(times: pd.Series) -> float:
    """記録の間隔（分）の推定：となりあう時刻の差の中央値"""
    d = pd.to_datetime(times).sort_values().diff().dt.total_seconds().dropna() / 60
    d = d[d > 0]
    return float(d.median()) if len(d) else 10.0


# ─────────────────────────────────────────────
# 届ける：最初の1個を売るまで
# ─────────────────────────────────────────────
#   (段取り, やること, データ（このダッシュボード）とのつながり)
FIRST_SALE_STEPS: list[tuple[str, str, str]] = [
    ("① 魅力をはっきりさせる", "だれに・何がうれしいか・なぜこの品かを書き出す", "『なぜ』の根拠に、測った記録を使える"),
    ("② くらべる相手を見る", "似た品物の値段・写真・説明を3つ見て、ちがいを1行で書く", "ちがいを『言える／言えない』で点検する"),
    ("③ 名前をつける", "何が・どこで・どう育ったかが伝わる短い名前", "─"),
    ("④ 写真をとる", "明るさ・背景・大きさのわかる物・切った断面", "生育の写真（タイムラプス）も伝える材料になる"),
    ("⑤ 文章を書く", "最初の1文で魅力、次に根拠、最後に食べ方・保存", "数字は測った物だけ。単位をつける"),
    ("⑥ 同封の紙をつくる", "育て方・食べ方・次に買える時期を1枚に", "1か月分のグラフを小さく載せる"),
    ("⑦ 送ってみる", "自分あてに1回送り、壊れ・傷み・届く日数を確かめる", "箱の中の温度を測れば、季節ごとの送り方が決められる"),
    ("⑧ やりとりの型をつくる", "注文・発送・お礼のあいさつ文を先に用意する", "─"),
]

#   気をつける言葉（正規表現, 理由）。言いすぎ・効き目・表示のルール
RISKY_WORDS: list[tuple[str, str]] = [
    (r"日本一|世界一|最高|最強|No\.?1|ナンバーワン", "比べた根拠がないと言いすぎ（くらべた範囲と方法を書けるか）"),
    (r"必ず|絶対|100\s*[%％]", "言い切り。自然の産物は年や個体で変わる"),
    (r"治る|効く|予防|免疫|血糖|血圧|ダイエット|やせる", "体への効き目は、食品の説明では書けない（法律の決まりがある）"),
    (r"無農薬|減農薬|無化学肥料|減化学肥料", "農産物の表示のルール（農林水産省のガイドライン）で使えない言い方がある。使う前に確かめる"),
    (r"栄養たっぷり|栄養満点|ビタミンたっぷり", "成分を測っていなければ言えない"),
    (r"オーガニック|有機", "有機JASの認証がないと使えない"),
]


def flag_words(text: str) -> list[tuple[str, str]]:
    """説明文の中の気をつける言葉 [(見つかった言葉, 理由)]"""
    out = []
    for pat, why in RISKY_WORDS:
        for m in re.finditer(pat, text or ""):
            out.append((m.group(0), why))
    return out


def product_text(name: str, who: str, joy: str, evidence: str, howto: str) -> str:
    """商品説明の下書き（魅力 → 根拠 → 食べ方）"""
    parts = [f"【{name or '（名前）'}】"]
    parts.append(f"{who or '（だれに）'}に、{joy or '（何がうれしいか）'}。")
    if evidence:
        parts.append(f"育てたハウスでは、{evidence}")
    if howto:
        parts.append(f"おすすめの食べ方・保存：{howto}")
    return "\n".join(parts)


def evidence_sentence(df: pd.DataFrame, col: str, days: int | None = None) -> str:
    """記録から言える1文（例：11/16〜11/22の7日間、10分ごとに気温を記録。夜の最低の中央値は 9℃）"""
    t = pd.to_datetime(df["時刻"])
    lo, hi = PLAUSIBLE.get(col, (-math.inf, math.inf))
    v = pd.to_numeric(df[col], errors="coerce")
    ok = (v >= lo) & (v <= hi)
    n_days = t.dt.date.nunique()
    interval = guess_interval(t)
    daily_min = v[ok].groupby(t[ok].dt.date).min()
    daily_max = v[ok].groupby(t[ok].dt.date).max()
    u = UNITS.get(col, "")
    return (f"{t.min():%m/%d}〜{t.max():%m/%d}の{n_days}日間、約{interval:.0f}分ごとに{col}を記録しました。"
            f"1日の最小の中央値は {daily_min.median():.0f}{u}、最大の中央値は {daily_max.median():.0f}{u}です。")


def _self_check() -> None:
    w = synth_week()
    assert list(w.columns) == ["時刻", *SENSOR_COLS]
    assert len(w) == 7 * 144 - 36                                   # 4日目 13〜19時（6時間＝36行）が抜けている
    h = health(w, 10)
    assert len(h["gaps"]) == 1 and abs(h["gaps"][0]["止まっていた分"] - 360) < 1e-9
    assert abs(h["uptime"] - (7 * 144 - 36) / (7 * 144)) < 1e-9
    assert h["per"]["CO2"]["範囲外"] == 2 and h["per"]["湿度"]["最長の張りつき（行）"] >= 144
    assert h["issues"][0][0] == "🛑 停止"
    assert abs(h["drift"]) < DRIFT_PPM_PER_DAY                        # ずれを入れていなければ注意は出ない
    hd = health(synth_week(drift_ppm_per_day=40.0), 10)
    assert 30 < hd["drift"] < 50 and any("夜の基準線" in i[1] for i in hd["issues"])
    clean = health(synth_week(outage=None, stuck_day=None, spikes=0), 10)
    assert clean["issues"] == [] and clean["uptime"] == 1.0
    assert longest_run([1, 1, np.nan, 1, 1, 1, 2]) == 3 and longest_run([0, 0, 0, 5], ignore=0) == 1
    fp = for_plot(w, "CO2", 10)
    assert len(fp) == len(w) + 1 and fp["CO2"].isna().sum() == 3     # 止まった所に1行、ありえない値2点が空欄
    dt = daily_table(w)
    assert len(dt) == 7 and dt["CO2 最大"].max() < 1000                # 9999 は除かれる
    mail = summary_mail(w, START.date(), 10, {"CO2": (None, 550.0)})
    assert "中央値" in mail and "550 超" in mail
    # CSV：Shift_JIS・カンマ区切りの数字・読めない列
    csv = ("CO2(ppm),日時,メモ\n\"1,020\",2026/11/16 0:00,晴れ\n980,2026/11/16 0:10,\n990,2026/11/16 0:20,\n"
           "1,こわれた行,\n").encode("cp932")
    df, notes = read_csv_bytes(csv)
    assert list(df.columns) == ["時刻", "CO2(ppm)"] and df["CO2(ppm)"].tolist() == [1020, 980, 990]
    assert any("メモ" in n for n in notes) and any("時刻が読めない行 1" in n for n in notes)
    assert guess_interval(df["時刻"]) == 10
    for bad in (b"a,b\nx,y\n", b"x" * (MAX_BYTES + 1)):
        try:
            read_csv_bytes(bad)
            raise AssertionError("ValueError になるはず")
        except ValueError:
            pass
    # 届ける
    found = [w for w, _ in flag_words("日本一あまい！無農薬で栄養たっぷり。風邪の予防にも効く")]
    assert found == ["日本一", "予防", "効く", "無農薬", "栄養たっぷり"]
    assert flag_words("11月に播いた小麦を、6月に手で刈りました。") == []
    assert product_text("三原の小麦", "パンを焼く人", "香りが立つ", "", "").startswith("【三原の小麦】")
    s = evidence_sentence(synth_week(outage=None, spikes=0), "気温")
    assert s.startswith("11/16〜11/22の7日間、約10分ごとに気温") and "℃" in s
    assert len(FIRST_SALE_STEPS) == 8


if __name__ == "__main__":
    _self_check()
    print("ops_core: 自己チェックOK")
