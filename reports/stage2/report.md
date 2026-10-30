# 第2段階 構築・検証報告（2026-10-30 JST）

**継承基盤と模擬検証は完了。独立した実ChatGPTとの往復が未実証のため、第2段階全体は未完了です。**
本番は未承認pending、スケジュール未登録・無効です。数学研究は開始していません。
正本: /path/to/erdos-straus-research。

## 完了条件の実証状況

| 条件 | 判定 | 根拠・限界 |
|---|---|---|
| 1. Codexが前回状態を読む | 基盤確認済み | 現Codexから全記憶を読取。MOCKの各サイクルで全contextを新規Git読取結果と照合。別AI研究workerの理解は未検証 |
| 2. ChatGPTが研究結果を取得 | 未実証 | 現Codexコネクタで公開README取得成功。独立ChatGPTで本研究結果の取得は未試験 |
| 3. ChatGPT査読をCodexが取得 | 未実証 | schema・手動import・MOCK往復は成功。実ChatGPTの返却は未取得 |
| 4. 未査読を確定事項にしない | 模擬検証成功 | 次回開始拒否、仮説の補題昇格拒否、明示的補題承認の境界を試験 |
| 5. 履歴を失わず複数サイクル | 模擬検証成功 | 3サイクル、10記録、全版・失敗・課題・指示全文・証拠全文を保存 |
| 6. 設定方法と制約 | 文書化・時刻試験済み | JSTの4研究枠／4査読枠、期限、未完了保留、途中保存、権限とPC制約を記載。本番起動は未試験 |

## 環境監査

第1段階の19件を再実行して成功。Lean/mathlibのlake buildも成功。
既存の数学関数、Store、19件のテスト、依存、固定Lean版は変更せず、新規モジュールとして追加しました。
第2版も既存venvを利用します。追加パッケージや管理者操作はありません。
詳細: environment/stage2/audit.md。

## 実装

追記イベント列＋内容hashによる全文object保存＋最新projectionを分離しました。
修正はsupersedes付きの新記録とし、元の記録を残します。
全履歴の検証、最新contextの確認hash、共有Gitの同じhead、承認査読、次回指示が揃わなければ開始を拒否します。
worker lock、revision、slot IDで重複・競合を拒否し、異常終了・破損・同期失敗を開始許可に変換しません。
production起動は設定のenabledだけでは解除できないハードガードで停止しています。
GitHub書込adapterや実AI起動driverは実装済みとは扱いません。

## 最低3サイクルの試験

- サイクル1: 仮説、未解決課題、既存Lean証拠、先行情報の出所、n=2の既知実験を保存。
- サイクル2: サイクル1の全本文を取得。仮説と課題を参照し、失敗方針と改訂課題、n=3の実験を追記。
- サイクル3: サイクル1・2の指示・報告・査読と全記録を参照し、未解決課題を継続、n=4を検証。
- 毎回ローカルbare Gitへ保存し、別の一時Git readerから全パケットをfetchして一致を照合。
- 査読は明記されたMOCK。実ChatGPTによる数学査読ではなく、既存小例による基盤試験。

保存先: reports/stage2/three-cycle-final/。
実行ログexecution.jsonl、全イベントmemory/events、全文memory/objects、査読review-*.json、共有Git履歴shared.bundle。

```json
{
  "all_contexts_matched": true,
  "cycles": 3,
  "final_head": "10f160543828ecbfdb54dd376bf64b3582e69c8c316c26806e563078d4dd2c4a",
  "history_preserved": true,
  "mock_only": true,
  "real_chatgpt_roundtrip": false,
  "records": 10,
  "status": "reviewed",
  "unreviewed_lemmas_promoted": false
}
```

## 異常系と実出力

最終試験: **41 passed in 5.33s**（既存19＋新規22）。
個別結果: test_results.json、pytest-final.xml。各異常系の観測出力はenvironment/stage2/pytest-final.txt。

| 異常系 | 実際に確認した動作 |
|---|---|
| 状態破損 | latest破損で開始拒否、原本保全後journalから同一headへ修復。journal/object破損は停止 |
| 古い査読 | cycle_id/report hash/memory headの不一致、再適用、出所未確認を拒否 |
| Codex異常終了 | Python模擬workerをos._exit(23)で実終了。checkpoint保持→failedへ復旧→次開始拒否。実AIは未起動 |
| ChatGPT査読未完了 | awaiting_reviewと不完全JSONで次回開始を拒否。実ChatGPT停止を起こした試験ではない |
| 重複スケジュール | 実Python dispatcher2本で1本だけ開始、もう1本拒否。受理済みでも同slotの再利用拒否 |
| 更新競合 | 同revisionの2回更新の後発を拒否、最新checkpointを保持 |
| 共有同期失敗 | 不存在remote・古い共有headで開始前に停止し、journal無変更。実GitHub共有ref不存在も検出 |
| 保存途中終了 | journal公開後latest更新失敗を注入し、次起動拒否。修復後もrunningを保って再実行を阻止 |
| 時間枠 | JST変換、4研究/査読時刻、5分超の追いつき拒否、遅延開始でも元期限、期限切れresume拒否 |

## 実GitHubと連携候補

指定repo https://github.com/rikupipi1113-cloud/- はpublic。
現コネクタ権限はpull=true/push=false。READMEのcommit指定取得とWSL Git読取は成功しました。
研究共有ref refs/heads/research-memory はなく、probe-sharedは終了2で停止しました。
既存READMEを変更せず、remote追加、push、認証変更、Issue等への投稿はしていません。

ChatGPT Libraryはoptionalのfile APIが公式にありますが、ここから定期読書きできるAPIは未提供です。
MCPは正式な読書き経路の候補ですが、認証・接続・配置の実証が必要です。
詳細と公式出典: automation/stage2/integration.md。

## 次の承認に向けた具体物

- 時刻設計と登録方法: automation/stage2/schedule_design.md
- 研究／査読プロンプト案: automation/stage2/prompt.md、review_prompt.md
- 手動実ChatGPT受入試験: automation/stage2/chatgpt_acceptance.md
- nonce付き診断入力: reports/stage2/integration-probe/request.json
- 診断応答schemaとvalidator: environment/stage2/response.schema.json、validate_probe.py

MOCK診断応答はvalidator成功、出所未確認は終了2で拒否しました。実ChatGPTの返却はまだありません。
最小の次段階は、別ChatGPTへ診断ファイルを渡して応答を返し、手動往復を実証することです。
自動GitHub往復には接続の書込権限と公開範囲の承認、共有adapter、実研究指示の初回承認が必要です。
本番有効化、PC設定変更、認証や公開の変更は次の明示指示まで行いません。

## 実際の制限

5時間の実AI連続実行は未検証。短い小課題＋同一cycleのcheckpoint/resume方式を提案し、その基盤だけ試験しました。
ログとhashは整合性確認であり査読者認証や数学的正しさの保証ではありません。
全履歴snapshot再生と32MiB共有パケット上限は長期運用前の拡張対象です。
最新状態と追記履歴の分離は確認済みですが、停電・実OS停止・長期安定運転は未試験です。
