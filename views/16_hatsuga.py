"""🌱 畑の実例：地温を足して、発芽の日を知らせる（測る → 貯める → 見る → 知らせる を1本でつなぐ）"""
from datetime import timedelta

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import hatsuga_core as hc
import ui

GREEN, ORANGE, RED, GREY = "#2f6f4f", "#c9822b", "#b03a2e", "#a9bccf"
ui.hero("畑の実例（2026-11）｜ 生命の科学（植物の生育と温度）× 情報Ⅰ データの活用・システムの信頼性",
        "🌱 地温を足して、発芽の日を知らせる",
        "11月16日にパン用小麦（ミナミノカオリ）をまいた。芽が出る日は、毎日の温度を足した『積算温度』で見当がつく。"
        "ただし、記録が止まった日があると、足し算はだまって小さくなる。", stage="知らせる")
ui.hint(hc.EASY_WORDS)

st.markdown("#### 畑の記録（三原西部・2026年11月）")
st.dataframe(pd.DataFrame([{"日付": f"{r['date']:%m/%d}", "作物": r["crop"], "したこと・見たこと": r["event"]}
                           for r in hc.FIELD_LOG]), hide_index=True, width="stretch")
lo, hi = hc.emergence_interval(hc.SPINACH_SOWN, hc.SPINACH_SEEN)
st.caption(f"ほうれん草は {hc.SPINACH_SEEN:%m/%d} に芽を**確認**した。言えるのは『{lo + 1}〜{hi}日目のどこかで出た』まで。"
           "人が見に行けない日をうめるのが、センサーの仕事。")

ui.predict("hatsuga_outage",
           f"まいてから毎日の平均地温が 10℃ だった。積算温度 **{hc.WHEAT_GDD:.0f} ℃・日** で芽が出るとすると 11 日目。"
           "ところが4日目から**4日間、電池切れで記録が止まり**、止まった日を足さずに数えてしまった。"
           "**プログラムが『届いた』と知らせるのは何日目？**",
           float(hc.emerge_day(hc.with_outage([10.0] * 40, 3, 4))), "日目", protocol="P1",
           min_value=1.0, max_value=40.0, value=11.0, field="知らせる")

st.markdown("#### 止まった日を、どう数える？")
c1, c2, c3, c4 = st.columns(4)
start = c1.slider("まいた直後の平均地温（℃）", 4.0, 16.0, 11.0, 0.5, key="hg_start")
drop = c2.slider("1日あたりの下がり方（℃）", 0.0, 0.4, 0.12, 0.02, key="hg_drop")
out_from = c3.slider("記録が止まった日（何日目から）", 1, 10, 4, key="hg_from")
out_len = c4.slider("止まっていた日数", 0, 10, 4, key="hg_len")

full = hc.synth_temps(start_temp=start, drop_per_day=drop)
cut = hc.with_outage(full, out_from - 1, out_len)
filled = hc.fill_missing(cut)
n_true, n_naive, n_fill = hc.emerge_day(full), hc.emerge_day(cut), hc.emerge_day(filled)


def _day(n):
    return "届かない" if n is None else f"{hc.WHEAT_SOWN + timedelta(days=n):%m/%d}（{n}日目）"


m1, m2, m3 = st.columns(3)
m1.metric("止まらずに測れた場合", _day(n_true))
late = None if None in (n_true, n_naive) else n_naive - n_true
m2.metric("止まった日を足さない", _day(n_naive),
          None if late is None else (f"{late} 日おそい" if late else "ずれなし"), delta_color="off", delta_arrow="off")
m3.metric("前後の平均でうめる", _day(n_fill))

days = [hc.WHEAT_SOWN + timedelta(days=i) for i in range(1, len(full) + 1)]
fig = go.Figure()
fig.add_trace(go.Scatter(x=days, y=hc.accumulate(full), name="止まらずに測れた場合", mode="lines",
                         line=dict(color=GREY, width=5)))
fig.add_trace(go.Scatter(x=days, y=hc.accumulate(cut), name="止まった日を足さない", mode="lines",
                         line=dict(color=RED, width=2, dash="dot")))
fig.add_trace(go.Scatter(x=days, y=hc.accumulate(filled), name="前後の平均でうめる", mode="lines",
                         line=dict(color=GREEN, width=2)))
fig.add_hline(y=hc.WHEAT_GDD, line_dash="dash", line_color=ORANGE,
              annotation_text=f"出芽の目安 {hc.WHEAT_GDD} ℃・日", annotation_position="top left")
if out_len:
    fig.add_vrect(x0=days[out_from - 1], x1=days[min(out_from - 1 + out_len, len(days)) - 1], fillcolor=RED,
                  opacity=0.08, line_width=0)
fig.update_layout(height=340, margin=dict(t=30, b=10, l=10, r=10), yaxis_title="積算温度（℃・日）",
                  legend=dict(orientation="h", y=1.15))
st.plotly_chart(fig, width="stretch")
if late:
    st.error(f"止まった日を足さないと、知らせが **{late} 日おそく**なる。芽はもう出ているのに、画面は『まだ』と言い続ける。"
             "止まったことに気づくしくみ（🔁 運用する：健康診断）が先に要る。")
elif out_len:
    st.info("この条件では、止まった日が目安に届いた後だったので、知らせる日はずれなかった。止まる時期によって影響は変わる。")
st.caption("🧪 地温は架空データです。「📈 見る」でCSVを読みこむ機能と同じように、畑に置いた温度計の記録に置きかえて使います。"
           f"積算温度 {hc.WHEAT_GDD} ℃・日 は別の品種（さとのそら）での推定値＝参考値（{hc.GDD_SOURCE}）。")

with st.expander("プログラムで書くと（Python）"):
    st.code(f"""積算 = 0
for 日, 地温 in 記録:            # 1日に1行（日平均）
    if 地温 is None:            # 止まった日 → 0として足さず、前後の平均でうめる
        地温 = 前後の平均(日)
    積算 += max(地温 - {hc.BASE_TEMP:.0f}, 0)   # 基準温度より寒い日は足さない
    if 積算 >= {hc.WHEAT_GDD}:
        知らせる("そろそろ芽が出るころ。畑を見に行こう")
        break""", language="python")
st.info("**知らせの文面**：『芽が出た』とは書かない。センサーが測ったのは温度で、芽ではない。"
        "『そろそろ出るころ。見に行こう』と書き、見た結果（出た・まだ）を記録にもどす。", icon="✉️")

ui.reading_card(
    axis="日付（横） と 積算温度（縦）", unit="℃・日",
    control="そろえた：同じ気温の列・同じ目安の線。変えた：止まった日の数え方（足さない／うめる）",
    can="記録が止まると積算温度は小さく出て、知らせが遅れること。うめると元に近づくこと",
    cannot="小麦が実際に芽を出した日（畑で見ないとわからない）。ミナミノカオリに必要な積算温度（別の品種の値を借りている）",
    protocols=["P1", "P3"], material="積算温度のグラフ")
ui.footer("hatsuga", "🔁 運用する")
