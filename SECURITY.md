# セキュリティについて

## このアプリが守っていること

| 層 | 対策 | 置き場所 |
|---|---|---|
| 秘密 | **鍵・パスワード・トークンの入力欄を置かない**（`type="password"` が無いことをテストで確認）。公開前の点検は**ファイル名だけ**で判定し、中身は受け取らない | `iot_core.risky_files()`・`tests/test_security.py` |
| 通信 | 実機・クラウド・メールに**つながない**（requests・socket・smtplib 等を import しないことをテストで確認）。まとめメールは文面をつくるだけ | `tests/test_security.py` |
| アップロード | CSVのみ・1MBまで・10万行まで。セッションの中だけで使い保存しない。数字の列は数値に変換し、`=1+1` のような文字は数字として扱わない | `ops_core.read_csv_bytes()`・`.streamlit/config.toml` |
| 入力 | 文字数の上限。ダウンロードするテキストから制御文字を除去 | `guard.clean_text()` |
| 画面 | HTML を出す箇所は `html.escape` を通す | `ui.py` |
| サーバー設定 | XSRF・CORS を有効、static 公開なし、アップロード上限1MB、エラー詳細を表示しない、開発者メニューを隠す | `.streamlit/config.toml` |
| リポジトリ | `.env`・`secrets.toml`・`service_account*.json`・`token*.json`・`*.pem`・写真・`data/` を入れない | `.gitignore`（テストで確認） |
| CI | GitHub Actions はコミットSHAで固定、トークンは読み取りのみ。pip-audit・bandit・CodeQL を実行 | `.github/workflows/` |

## GitHub 側で設定してほしいこと（リポジトリ管理者が画面で行う）

設定の変更は管理者の画面からしかできないため、ここに手順をまとめています。所要時間は5分ほどです。

| # | 場所 | 操作 |
|---|---|---|
| 1 | Settings → Rules → Rulesets → **New ruleset ▾ → Import a ruleset** | `.github/rulesets/main-protection.json` を読み込んで **Create**（main の削除・強制pushの禁止、PR必須、`test`・`scan` の成功が必須） |
| 2 | Settings → Advanced Security | **Dependabot alerts**・**Dependabot security updates**・**Private vulnerability reporting** を Enable |
| 3 | Settings → Actions → General → Workflow permissions | **Read repository contents and packages permissions** を選んで Save |
| 4 | Settings → General → Pull Requests | **Automatically delete head branches** にチェック |

ルールセットを入れたあとは、main に直接 push できなくなります（変更はブランチ → PR → チェック成功 → マージ）。
JSON の `integration_id: 15368` は GitHub Actions を表す番号です（チェックの出どころを GitHub Actions に限る）。

## 実機（IoTキット）側で守ること

このダッシュボードの外の話ですが、授業で必ず確認します（「🔁 運用する」の点検表と同じ）。

- クラウドの鍵ファイルを GitHub に置かない。すでに公開してしまった鍵は**無効にして作り直す**（.gitignore に足しても履歴に残る）
- 遠隔操作のパスワードを初期値から変える
- カメラに人・表札・車のナンバーが写らない向きにする
- 警報メールの宛先は、同意した大人のアドレスだけ
- 料金の上限・警告を設定する

## 守っていないこと（限界）

- 公開前の点検・言葉の点検は、決まった形を探す補助です。「見つからなかった」は「安全」「問題ない」を意味しません。
- 健康診断の範囲・目安は仮の値です。誤報や見落としがありえます。

## 脆弱性の報告

Security タブの **Report a vulnerability**（非公開の報告）からお知らせください。
