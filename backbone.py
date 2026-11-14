"""
背骨（どのページでも同じ「考え方の型」）─ 姉妹サイト「科学と人間生活」ダッシュボードと同じ言葉を使う

  - 読解カード（4項目）：軸・単位・統制・言える／言えない
  - P1〜P5：手順を回す・資料を読む・比較を疑う・模型で考える・知識で答える
  - 先に予想 → 答え → ずれ δ（相対誤差）

Streamlit に依存しない。`python backbone.py` で自己チェック。
"""
from __future__ import annotations

from datetime import datetime

READING_CARD = (
    ("軸", "何と何を比べている？（軸は何と何か）"),
    ("単位", "単位は何か"),
    ("統制", "何をそろえ（統制）、何を変えたか"),
    ("言える／言えない", "この比較で言えること／言えないことは何か"),
)

PROTOCOLS = {
    "P1": ("手順を回す", "決まった順番どおりに処理する"),
    "P2": ("資料を読む", "グラフや表から事実を取り出す"),
    "P3": ("比較を疑う", "「その比べ方、フェア？」と問う"),
    "P4": ("模型で考える", "単純化した絵や式で説明する"),
    "P5": ("知識で答える", "覚えていることを使う"),
}


def p_label(code: str) -> str:
    return f"{code} {PROTOCOLS[code][0]}"


def td_error(predicted: float, observed: float) -> float:
    """相対誤差 |実測−予想| ÷ |予想|（予想が0なら |実測| で割る。両方0ならずれ0）"""
    denom = abs(predicted) or abs(observed)
    return 0.0 if denom == 0 else abs(observed - predicted) / denom


def log_record(field: str, protocol: str, predicted: float, observed: float, unit: str = "",
               timestamp: str | None = None) -> dict:
    """予想の記録1件（姉妹サイトと同じ形：subject・field・timestamp・protocol・td_error）。保存・送信はしない"""
    assert protocol in PROTOCOLS, protocol
    return {"subject": "IoTフィールドワーク", "field": field,
            "timestamp": timestamp or datetime.now().isoformat(timespec="seconds"),
            "protocol": protocol, "predicted": predicted, "observed": observed, "unit": unit,
            "td_error": round(td_error(predicted, observed), 4)}


def _self_check() -> None:
    assert len(READING_CARD) == 4 and set(PROTOCOLS) == {"P1", "P2", "P3", "P4", "P5"}
    assert abs(td_error(60, 14.58) - 0.757) < 1e-3 and td_error(0, 0) == 0
    assert log_record("測る", "P4", 10, 12)["td_error"] == 0.2


if __name__ == "__main__":
    _self_check()
    print("backbone: 自己チェックOK")
