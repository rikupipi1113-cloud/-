# 運用手順（WSL Ubuntu-22.04）

## 起動とPython実験

```sh
cd /path/to/erdos-straus-research
source .venv/bin/activate
export ELAN_HOME="$PWD/.tools/elan"
export PATH="$ELAN_HOME/bin:$PATH"
python -m pytest -v
python -c 'from es_research.math import verify_solution; print(verify_solution(2,1,2,2))'
python -m es_research.cli show
```

exportは現在のシェルだけに適用します。ログイン設定は変更していません。

再構築時は新規venvに `python -m pip install -r environment/requirements.lock.txt` を実行し、
続いて `python -m pip install --no-build-isolation --no-deps -e .`。
Python 3.10系に固定しています。lockは今回実際に導入した推移依存を含みます。
ダウンロード済みwheelを保存する仕組みや完全なオフライン再構築は未実装です。

## Lean

```sh
cd /path/to/erdos-straus-research
export ELAN_HOME="$PWD/.tools/elan"
export PATH="$ELAN_HOME/bin:$PATH"
cd lean
lake build
```

固定バージョンはlean-toolchain、固定コミットはlake-manifest.json。
初回依存取得は `lake update`、使用するimportのキャッシュ取得は
`lake exe cache get Mathlib.Data.Nat.Prime.Basic Mathlib.Tactic.NormNum Mathlib.Tactic.Ring`。
ビルド時に各補題の公理依存も表示します。Lean標準の基礎公理と独自追加公理を区別します。

## Codexによる研究開始（将来）

本番JSONは未承認pendingです。今回の作業後に研究を開始しません。
人間が最初の研究課題と査読の受け渡し方法を承認した後、初回指示を登録する運用を決めます。
初回承認用の汎用CLIは意図的に用意していません。
以降のworkerは `with store.lock(worker=True)` の内側で、read、begin、実験、complete、submitを行います。
すべての変更に取得時のrevisionを渡し、競合時は再読込して人間へ報告します。

## 模擬サイクル

```sh
python -m es_research.demo reports/mock-manual-001
```

出力先は未作成フォルダを指定します。既存フォルダへの上書きを拒否します。
既知例の検証→awaiting_review→MOCK査読→次サイクル→中断復旧を実行します。
最後のfailedは異常終了復旧試験の期待状態です。実際のChatGPT査読ではありません。

## 報告確認と査読取り込み

`reports/` と状態内report、`environment/commands.jsonl` を確認してください。
ChatGPTへreport.payloadとsha256、revision、関連ソース・ログを手動で渡します。
返ってきた査読をreviewsに保存し、出所と対象を確認してから実行します。

```sh
python -m es_research.cli apply-review --revision CURRENT_REVISION --review-file reviews/REVIEW.json --confirm-review-source
```

CURRENT_REVISION等は実際の値に置換してください。JSON schemaはautomation/review.schema.json。
ハッシュは整合性用であり、ChatGPTの身元や査読品質の認証ではありません。

## 異常終了からの復旧

1. `python -m es_research.cli show` とログを確認する。
2. runningのままworkerが終了した場合、`python -m es_research.cli recover --revision CURRENT_REVISION`。
   生存workerのlockがあれば拒否します。失敗状態と理由を保存し、勝手に再実行しません。
3. JSONが破損した場合、`python -m es_research.cli restore-backup`。
   壊れたデータを別名保存し、最後の有効backupからfailedへ復旧します。
   backupが古い可能性があるため、自動再開・既存査読の再適用は禁止します。
4. backupも破損・不存在なら停止し、Git履歴とログから人間が調査します。
5. failedを再開するAPIはありません。原因調査後、別IDの指示を人間が承認します。

LinuxローカルFSでのflock、同一ディレクトリrename、fsyncに依存します。
実際のOS強制終了・停電・ディスク破損への耐久性は未検証です。
全workerがlockとAPIを使用する運用が必要で、手編集や悪意ある書換えは防止しません。

## Git

`git status`、`git log --oneline`で履歴を確認します。
研究ごとにソース、指示、状態、報告、査読をまとめて保存してください。
今回のGitコミットはローカル専用の明示IDで作成し、既存の個人情報設定は変更しません。
外部へのpushには別途ユーザー指示が必要です。
