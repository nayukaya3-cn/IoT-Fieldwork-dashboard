"""📈 見る：1日のグラフと代表値、手元のCSVを読みこむ"""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import iot_core as ic
import ops_core as oc
import ui

BLUE, GREEN, ORANGE = "#3f6584", "#2f6f4f", "#c9822b"
ui.hero("段3 見る ｜ 情報Ⅰ データの活用（代表値・外れ値・欠測）",
        "📈 見る：平均だけを信じない",
        "ありえない値が1点まじるだけで、平均は大きく動く。測れなかった時間を0で埋めると、もっと動く。"
        "まず架空の1日で確かめ、つぎに自分たちのCSVを読みこむ。", stage="見る")

tab1, tab2 = st.tabs(["① 架空の1日で練習する", "② 自分たちのCSVを読みこむ"])

with tab1:
    st.warning("このグラフは、しくみを説明するための**架空データ**です。実測ではありません。", icon="🧪")
    f1, f2, f3 = st.columns(3)
    item = f1.selectbox("見る数字", list(oc.SENSOR_COLS), index=3, key="mr_item")
    outlier = f2.toggle("センサーの誤動作を1点まぜる（CO2）", key="mr_outlier")
    missing = f3.toggle("昼の1時間を欠測にする（CO2）", key="mr_missing")
    day = ic.synth_day(interval_min=10, outlier=outlier, missing=missing)
    unit = oc.UNITS[item]
    s = ic.summary(day[item])
    g1, g2, g3, g4, g5 = st.columns(5)
    g1.metric("平均", f"{s['mean']:,.0f} {unit}")
    g2.metric("中央値", f"{s['median']:,.0f} {unit}")
    g3.metric("最小", f"{s['min']:,.0f} {unit}")
    g4.metric("最大", f"{s['max']:,.0f} {unit}")
    g5.metric("欠測", f"{s['missing']} 件", f"{s['n']} 件は有効", delta_color="off", delta_arrow="off")
    fig = go.Figure(go.Scatter(x=day["時刻"], y=day[item], mode="lines+markers", marker=dict(size=4),
                               line=dict(color=BLUE, width=2), connectgaps=False))
    fig.add_hline(y=s["mean"], line_dash="dash", line_color=ORANGE, annotation_text="平均")
    fig.add_hline(y=s["median"], line_dash="dot", line_color=GREEN, annotation_text="中央値", annotation_position="bottom right")
    fig.update_layout(height=300, margin=dict(t=20, b=10, l=10, r=10), xaxis_title="時刻（時）", yaxis_title=f"{item}（{unit}）",
                      showlegend=False, xaxis=dict(dtick=3, range=[0, 24]))
    st.plotly_chart(fig, width="stretch")
    if item == "CO2" and outlier:
        base = ic.summary(ic.synth_day(interval_min=10, missing=missing)["CO2"])
        st.error(f"ありえない値が1点入っただけで、平均は {base['mean']:.0f} → {s['mean']:.0f} ppm に動いた。"
                 f"中央値は {base['median']:.0f} → {s['median']:.0f} ppm でほとんど動かない。"
                 "まとめメールに『平均』だけを書くと、1点の誤動作でだまされる。")
    if item == "CO2" and missing:
        st.info("線が切れているところが欠測。『0 ppm』と書きこむプログラムにすると、平均が大きく下がってしまう。"
                "測れなかったときは、空欄のまま残す。", icon="🕳️")
    if item == "CO2":
        ui.hint("日中にCO2が外気（420 ppm）より下がるのは、ハウスの中の植物が光合成で吸っているから。"
                "夜は呼吸で出すので上がる。ヒトの教室とは逆の形になる。")
    ui.reading_card(
        axis="時刻（横） と センサーの値（縦）", unit=f"時、{unit}",
        control="そろえた：測る間隔（10分）・同じ1日・同じ置き場所。変えた：見る数字、誤動作・欠測のあり／なし",
        can="1日の中での上がり下がりの形・外れ値に強い代表値はどれか",
        cannot="ほかの日も同じ形か（1日分だけ）・CO2が下がった原因が光合成か換気か（窓の開閉の記録がないと分けられない）",
        protocols=["P2", "P3"], material="1日分のグラフと5つのまとめの数字")

with tab2:
    st.markdown("表計算（スプレッドシート）から **CSV** で書き出したファイルを読みこむ。1行目が列名、1列は時刻にする。")
    st.caption("ファイルは**このセッションの中だけ**で使い、サーバーには保存しません（1MBまで）。"
               "人の名前・連絡先・写真の列は入れずに書き出してください。")
    up = st.file_uploader("CSVファイル", type=["csv"], key="mr_upload")
    sample = oc.synth_week(days=2, outage=None, stuck_day=None, spikes=0)
    st.download_button("⬇️ 形の見本（架空データ2日分のCSV）", sample.to_csv(index=False).encode("utf-8-sig"),
                       "sample_house.csv", "text/csv")
    if up is not None:
        try:
            df, notes = oc.read_csv_bytes(up.getvalue())
        except ValueError as e:
            st.error(str(e))
        else:
            st.session_state[ui.USER_DF_KEY] = df
            for n in notes:
                st.caption("・" + n)
            interval = oc.guess_interval(df["時刻"])
            c1, c2, c3 = st.columns(3)
            c1.metric("行数", f"{len(df):,}")
            c2.metric("日数", f"{df['時刻'].dt.date.nunique()} 日")
            c3.metric("記録の間隔（推定）", f"{interval:.0f} 分")
            st.caption(f"期間：{df['時刻'].min():%Y/%m/%d %H:%M} 〜 {df['時刻'].max():%Y/%m/%d %H:%M}")
            cols = [c for c in df.columns if c != "時刻"]
            pick = st.multiselect("グラフにする列", cols, default=cols[:1], key="mr_cols")
            fig = go.Figure()
            for c in pick:
                fp = oc.for_plot(df, c, interval)
                fig.add_trace(go.Scatter(x=fp["時刻"], y=fp[c], mode="lines", name=c, connectgaps=False))
            fig.update_layout(height=320, margin=dict(t=20, b=10, l=10, r=10), legend=dict(orientation="h", y=1.1))
            st.plotly_chart(fig, width="stretch")
            names = {"n": "有効", "missing": "欠測", "mean": "平均", "median": "中央値", "min": "最小", "max": "最大"}
            st.dataframe(pd.DataFrame([{"列": c, **{names[k]: (round(v, 1) if isinstance(v, float) else v)
                                                   for k, v in ic.summary(df[c]).items()}} for c in cols]),
                         hide_index=True, width="stretch")
            st.caption("グラフでは、ありえない値（運用の健康診断の範囲の外）を消し、記録が止まった所で線を切っている。"
                       "上の表はそのままの値なので、最大がありえない値になっていることがある。平均と中央値をくらべよう。")
            st.success("読みこみました。「🔔 知らせる」「🔁 運用する」「🛒 届ける」でも、このデータを選べます。", icon="✅")
            if not set(oc.SENSOR_COLS) & set(cols):
                st.info("列名を「気温・湿度・照度・CO2・水深」にしておくと、運用の健康診断（ありえない値の範囲）がそのまま使えます。")
    elif st.session_state.get(ui.USER_DF_KEY) is not None:
        st.info("読みこんだCSVを、このセッションで使っています。別のファイルに替えるときは、上から選びなおしてください。")
ui.footer("miru", "🔔 知らせる")
