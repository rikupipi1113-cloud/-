# 第2版の操作手順

```sh
cd /path/to/erdos-straus-research
source .venv/bin/activate
python -m es_research.stage2_cli status
python -m es_research.stage2_cli context
python -m es_research.stage2_cli plan
python -m pytest -v -rA
```

statusはjournal全再生とlatest/object検証を行います。破損や不一致は終了コード2で停止します。
第1版の状態はautomation/cycle_state.jsonにそのまま残り、未承認pendingです。
第2版はresearch/memory-v2/latest.json、初期pending・bootstrap_approved=falseです。

## 模擬試験の再現

```sh
python -m es_research.stage2_cli demo --output reports/stage2/new-three-cycle
```

未作成ディレクトリを指定します。既存の模擬結果は上書きしません。
実ChatGPTを起動せず、ローカルbare GitとMOCK査読で3サイクルを実行します。
execution.jsonl、summary.json、memory/events、objects、review-*.jsonが残ります。
最終版の保存済み試験はreports/stage2/three-cycle-finalです。
three-cycleは開発途中の形式による過去試験として保存し、schema snapshotも添付しています。

## 手動受け渡し

```sh
python -m es_research.stage2_cli export --output reports/stage2/handoff-UNIQUE.json
python -m es_research.stage2_cli apply-review --root PATH_TO_MEMORY --revision CURRENT_REVISION --review reviews/REVIEW.json --confirm-source
```

exportは未使用ファイル名だけを許可し、全履歴と証拠を含めます。
現初期状態には未査読の研究報告がないため、初期exportへ研究査読を適用することはできません。
ChatGPT実連携試験はchatgpt_acceptance.mdの診断パケットを使います。
productionにmock査読を取り込むことはできません。出所確認フラグは暗号学的な認証ではありません。

## 共有確認

```sh
python -m es_research.stage2_cli probe-shared
```

現在は研究共有refが存在しないため終了コード2が期待されます。状態を変更しません。
READMEが読めることだけでは研究継承の確認になりません。

## 復旧

```sh
python -m es_research.stage2_cli repair --root PATH_TO_MEMORY
python -m es_research.stage2_cli recover --root PATH_TO_MEMORY --revision CURRENT_REVISION
```

repairはlatestのみ破損した場合に、原本をquarantineへ保存してjournalから再構築します。
開始済みのサイクルがpendingに戻ることはありません。journal/object自体が破損していれば停止します。
recoverは生存workerのlockを取得できる場合だけ、runningをfailedにします。
failedは次の研究をブロックします。失敗を無視してIDを再利用する手順は提供しません。
pausedの正常な途中状態はresume_session APIで同じID・同じ期限内に再開できます。
workerはdispatch/resume_sessionのwithブロックを終了するまでlockを保持する必要があります。

## 既存環境の扱い

第1版のコード、19件のテスト、Python依存、Lean/mathlib固定版は変更していません。
第2版も既存venvを使用し、追加の外部パッケージは導入していません。
新規コードと記憶・報告をGitへ追加します。remoteは追加せず、pushもしません。
