"""🔁 運用する：1週間の健康診断・公開前の点検・引きつぎ書"""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import guard
import iot_core as ic
import ops_core as oc
import ui

BLUE, ORANGE, RED = "#3f6584", "#c9822b", "#b03a2e"
ui.hero("段7 運用する ｜ 終章（課題研究の進め方）× 情報Ⅰ 情報セキュリティ・システムの保守",
        "🔁 運用する：作って終わりにしない",
        "IoTは、動きはじめてからが本番。止まった・固まった・ずれた、を毎週見つけて直す。"
        "変えるのは1か所ずつ。前の週とくらべれば、直した効果が言える（対照実験と同じ）。", stage="運用する")

tab1, tab2, tab3 = st.tabs(["① 1週間の健康診断", "② 運用の輪と公開前の点検", "③ 引きつぎ書"])

with tab1:
    df, label, synthetic = ui.week_data("uy_data")
    if synthetic:
        with st.expander("架空データに入れる『故障』を変える"):
            g1, g2, g3, g4 = st.columns(4)
            out_on = g1.toggle("4日目の午後に止まる", True, key="uy_out")
            stuck = g2.toggle("3日目に湿度が固まる", True, key="uy_stuck")
            spikes = g3.slider("CO2のありえない値（点）", 0, 10, 2, key="uy_spikes")
            drift = g4.slider("CO2のずれ（ppm/日）", 0, 60, 0, 5, key="uy_drift")
            df = oc.synth_week(outage=(4, 13.0, 19.0) if out_on else None, stuck_day=2 if stuck else None,
                               spikes=spikes, drift_ppm_per_day=float(drift))
    interval = oc.guess_interval(df["時刻"])
    h = oc.health(df, interval)
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("稼働率", f"{h['uptime']:.1%}", f"{h['rows']:,} / {h['expected']:,} 行", delta_color="off", delta_arrow="off")
    k2.metric("止まった回数", f"{len(h['gaps'])} 回",
              f"合計 {sum(g['止まっていた分'] for g in h['gaps']) / 60:.1f} 時間" if h["gaps"] else "なし",
              delta_color="off", delta_arrow="off")
    k3.metric("気になる点", f"{len(h['issues'])} 件")
    k4.metric("CO2 夜の基準線の動き", f"{round(h['drift']) + 0:+d} ppm/日" if "CO2" in df else "─",
              help=f"毎日 {oc.NIGHT_HOURS[0]}〜{oc.NIGHT_HOURS[1]} 時の中央値をつないだ傾き。±{oc.DRIFT_PPM_PER_DAY:.0f} をこえたら注意")
    if h["issues"]:
        st.dataframe(pd.DataFrame(h["issues"], columns=["重さ", "何が", "どうする"]), hide_index=True, width="stretch")
    else:
        st.success("気になる点は見つからなかった。それでも週に1回は、ハウスで数字と実物を見くらべる。", icon="✅")

    cols = [c for c in df.columns if c != "時刻"]
    col = st.selectbox("グラフで見る列", cols, index=cols.index("CO2") if "CO2" in cols else 0, key="uy_col")
    fp = oc.for_plot(df, col, interval)
    fig = go.Figure(go.Scatter(x=fp["時刻"], y=fp[col], mode="lines", line=dict(color=BLUE, width=1.5), name=col,
                               connectgaps=False))
    lo, hi = oc.PLAUSIBLE.get(col, (None, None))
    if lo is not None:
        v = pd.to_numeric(df[col], errors="coerce")
        valid, bad = v[v.between(lo, hi)], df[(v < lo) | (v > hi)]
        if len(valid):
            pad = (float(valid.max()) - float(valid.min())) * 0.08 + 1
            top = float(valid.max()) + pad * 2              # ありえない値は、この高さに×で置く
            fig.update_yaxes(range=[float(valid.min()) - pad, top + pad if len(bad) else float(valid.max()) + pad])
            if len(bad):
                fig.add_trace(go.Scatter(x=pd.to_datetime(bad["時刻"]), y=[top] * len(bad), mode="markers",
                                         marker=dict(color=RED, size=10, symbol="x"), name="ありえない値（グラフの上端に表示）"))
    for g in h["gaps"]:
        fig.add_vrect(x0=g["止まった直前"], x1=g["再開"], fillcolor=ORANGE, opacity=0.25, line_width=0)
    if col == "CO2":
        base = oc.night_baseline(df)
        fig.add_trace(go.Scatter(x=pd.to_datetime(base.index) + pd.Timedelta(hours=2.5), y=base.values, mode="lines+markers",
                                 line=dict(color=ORANGE, dash="dash"), name="夜の基準線（0〜5時の中央値）"))
    fig.update_layout(height=340, margin=dict(t=20, b=10, l=10, r=10), legend=dict(orientation="h", y=1.12),
                      yaxis_title=f"{col}（{oc.UNITS.get(col, '')}）")
    st.plotly_chart(fig, width="stretch")
    st.caption("オレンジの帯＝記録が止まっていた時間。×＝ありえない値（本当の値は大きすぎるので、グラフの上端に置いて表示）。")
    ui.hint("夜のハウスは光合成がなく、作物と土の呼吸でCO2が少しずつたまる。毎晩の『夜の基準線』が日に日に上がる（下がる）なら、"
            "作物が育った・換気が変わった・センサーがずれた、のどれか。外気の中で数分測ってくらべると、センサーのずれを分けられる。")
    st.markdown("##### 日ごとのまとめ（ありえない値は除く）")
    st.dataframe(oc.daily_table(df), hide_index=True, width="stretch")
    ui.reading_card(
        axis="時刻（横） と 記録の値（縦）・止まった時間", unit=f"日時、{oc.UNITS.get(col, '')}、%",
        control="そろえた：置き場所・測る間隔・ありえない値の範囲。変えた：日（1週間）",
        can="いつ止まったか・どの値がありえないか・夜の基準線が動いているか",
        cannot="ずれの原因（センサーか、作物の生長か、換気か）をこのグラフだけで決めること",
        protocols=["P2", "P3"], material="1週間のグラフと健康診断の表")

with tab2:
    st.markdown("#### 運用の輪：1周ごとに、変えるのは1か所だけ")
    st.dataframe(pd.DataFrame(ic.OPS_LOOP, columns=["輪の段", "AIの運用（MLOps）では", "このフィールドワークでは"]),
                 hide_index=True, width="stretch")
    st.markdown("#### 🔐 公開する前の点検（情報セキュリティ）")
    st.caption("このしくみは、クラウドの鍵・メールの送信・カメラの写真を扱う。プログラムを GitHub で公開するなら、下を1つずつ確かめる。")
    checked = [st.checkbox(f"{q}（{why}）", key=f"uy_sec_{i}") for i, (q, why, _) in enumerate(ic.SECURITY_CHECKS)]
    score = ic.security_score(checked)
    st.session_state["uy_score"] = score
    st.progress(score / ic.SECURITY_MAX, text=f"点検 {score} / {ic.SECURITY_MAX} 点")
    if score == ic.SECURITY_MAX:
        st.success("すべて確認できた。鍵を作り直したときや人が入れかわったときに、もう一度点検する。")
    elif not all(checked[:2]):
        st.error("上の2つ（鍵を置かない・.gitignore）が済むまでは、公開しない。")
    st.markdown("##### ファイル名だけで点検する")
    st.caption("公開するフォルダの**ファイル名だけ**を1行に1つ書く。鍵やパスワードの**中身は絶対に貼らない**（この欄も、名前しか受け取らない設計です）。")
    raw = st.text_area("ファイル名（1行に1つ）", "main.py\nconfig.ini\nservice_account.json\ntoken.json\nREADME.md",
                       height=130, max_chars=1500, key="uy_files")
    names_in = [guard.clean_text(x, 120) for x in raw.splitlines() if x.strip()][:60]
    risky = ic.risky_files(names_in)
    if risky:
        st.dataframe(pd.DataFrame(risky, columns=["ファイル名", "気をつける理由"]), hide_index=True, width="stretch")
        st.markdown("`.gitignore` に書く行：")
        st.code("\n".join(ic.gitignore_lines(names_in)), language="text")
        st.caption("すでに公開してしまった鍵は、.gitignore に足しても履歴に残る。その鍵はクラウド側で無効にして、作り直す。")
    else:
        st.success("名前から見て危なそうなファイルは見つからなかった（中身までは確かめていないので、設定ファイルは自分の目で見る）。")

with tab3:
    st.markdown("#### 引きつぎ書をつくる")
    h_now = oc.health(df, oc.guess_interval(df["時刻"]))
    with st.form("uy_handover"):
        place = st.text_input("置き場所（個人の住所は書かない。例：ハウスの北側の棚）", max_chars=80)
        rule = st.text_area("警報と水やりの規則（何を見たら、何をするか）", max_chars=400, height=80)
        trouble = st.text_area("止まったときに最初に見るところ", max_chars=400, height=80,
                               value="電源 → Wi-Fi → 表の書きこみ（鍵の期限）の順に見る")
        nextq = st.text_input("次の人にためしてほしいこと（変えるのは1か所）", max_chars=200)
        made = st.form_submit_button("引きつぎ書をつくる")
    if made:
        lines = ["🔁 IoTフィールドワーク 引きつぎ書", f"問い：{ic.LEAD_QUESTION}",
                 f"直近の記録：{label}・稼働率 {h_now['uptime']:.1%}・気になる点 {len(h_now['issues'])} 件",
                 f"公開前の点検：{st.session_state.get('uy_score', 0)} / {ic.SECURITY_MAX} 点", "",
                 f"■ 置き場所\n{guard.clean_text(place, 80) or '（未記入）'}",
                 f"■ 警報と水やりの規則\n{guard.clean_text(rule, 400) or '（未記入）'}",
                 f"■ 止まったときに最初に見るところ\n{guard.clean_text(trouble, 400) or '（未記入）'}",
                 f"■ 次の人にためしてほしいこと\n{guard.clean_text(nextq, 200) or '（未記入）'}", "",
                 "■ 気になる点（健康診断）"]
        lines += [f"・{s} {w} → {d}" for s, w, d in h_now["issues"]] or ["・なし"]
        lines += ["", "※ 鍵・パスワード・個人の連絡先は、この紙に書かない。"]
        st.download_button("⬇️ 引きつぎ書（テキスト）をダウンロード", "\n".join(lines).encode("utf-8"),
                           "iot_hikitsugi.txt", "text/plain")
        st.caption("入力はこの画面の中だけで使い、サーバーには保存しません。")
ui.footer("unyo", "🛒 届ける")
