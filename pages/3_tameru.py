"""🗄️ 貯める：センサーの番地と、表の大きさ"""
import pandas as pd
import streamlit as st

import iot_core as ic
import ui

ui.hero("段2 貯める ｜ 情報Ⅰ 情報通信ネットワーク・2進数・データベース",
        "🗄️ 貯める：だれの数字かを番地で見分け、表に書きこむ",
        "センサーが何個あっても、番地（アドレス）で相手を選べば2本の線で足りる。"
        "書きこむ表には上限がある。何を・どの間隔で貯めるかを先に決める。", stage="貯める")

st.markdown("#### 何を測る？　5つの数字と、理科での意味")
st.dataframe(pd.DataFrame(ic.SENSORS, columns=["測るもの", "つなぎ方", "単位", "理科での意味", "番地の例"]),
             hide_index=True, width="stretch")
st.caption("番地は機種によって違う。買ったセンサーの説明書（データシート）で必ず確かめる。")

st.markdown("#### 番地（アドレス）を2進数で読む")
ui.hint("I2C（アイ・ツー・シー）は、2本の線に何個ものセンサーをぶら下げるつなぎ方。"
        "先生が『出席番号68番の人、温度は？』と呼ぶように、番地で相手を選ぶ。")
addr = st.slider("番地（10進数）", 0, 127, 0x44, key="tm_addr")
info = ic.i2c_info(addr)
b1, b2, b3, b4 = st.columns(4)
b1.metric("10進数", info["dec"])
b2.metric("16進数", info["hex"])
b3.metric("2進数（7ビット）", info["bin"])
b4.metric("ふつうに使える？", "はい" if info["usable"] else "予約済み")
st.caption(f"7ビットで表せるのは 2⁷ ＝ 128 通り。そのうち両端は特別な用途に予約されていて、ふつうに使えるのは "
           f"{ic.I2C_MIN}〜{ic.I2C_MAX}（0x08〜0x77）の {ic.i2c_usable_count()} 個。同じ番地のセンサーを2個つなぐと、区別できない。")

st.markdown("#### 表はいつ、いっぱいになる？")
ui.predict("rows", "CO2・気温・湿度・照度・水深の5つに、日付と時刻を足した **7列** を **10分ごと** に1行ずつ書きこむ。"
           "1ファイルの上限は1000万セル。**いっぱいになるまで、およそ何年？**",
           round(ic.days_until_full(7, 10) / 365, 1), "年", protocol="P1", min_value=0.0, max_value=100.0, value=3.0,
           field="貯める")
d1, d2 = st.columns(2)
cols = d1.slider("列の数", 2, 20, 7, key="tm_cols")
interval = d2.select_slider("測る間隔（分）", [1, 2, 5, 10, 15, 30, 60], 10, key="tm_interval")
days = ic.days_until_full(cols, interval)
e1, e2, e3 = st.columns(3)
e1.metric("1日の行数", f"{ic.rows_per_day(interval):.0f} 行")
e2.metric("1日に増えるセル", f"{cols * ic.rows_per_day(interval):,.0f}")
e3.metric("いっぱいになるまで", f"{days / 365:.1f} 年" if days >= 365 else f"{days:.0f} 日")
ui.hint("間隔を10分から1分にすると、データは10倍になる。細かく測るほどよいとは限らない。"
        "『何を知りたいか』で間隔を決める（気温の日変化なら10分で十分）。")

st.markdown("#### 表の形をそろえる（野帳と同じ）")
st.dataframe(pd.DataFrame([
    {"列": "時刻", "書き方": "2026/11/16 08:10（年月日と時分）", "なぜ": "あとで並べ替え・日ごとの集計ができる"},
    {"列": "CO2(ppm)", "書き方": "数字だけ。単位は列名に", "なぜ": "セルに『ppm』を書くと計算できない"},
    {"列": "（欠測）", "書き方": "空欄のまま", "なぜ": "0 と書くと、本当に0だったのか区別できない"},
    {"列": "メモ", "書き方": "窓を開けた・水をやった など", "なぜ": "CO2が下がった原因を、光合成と換気に分けられる"},
]), hide_index=True, width="stretch")
ui.reading_card(
    axis="列の数・測る間隔 と 表がいっぱいになるまでの日数", unit="列、分、日（年）",
    control="そろえた：1ファイルの上限（1000万セル）。変えた：列の数と間隔",
    can="間隔を短くするほど、表は早くいっぱいになる（反比例）",
    cannot="その間隔で足りるか（知りたい変化の速さで決まる）・通信が止まったときの抜け",
    protocols=["P1", "P4"], material="3つの数字")
ui.footer("tameru", "📈 見る")
