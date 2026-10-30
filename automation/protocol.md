# 自律研究と査読の契約 v1（スケジュール無効）

## 正本と状態遷移

単一のcycle_state.jsonを正本とします。cycle_id、revision、開始・終了UTC時刻、task、
結果（experiment/lemma/hypothesis/failure）、査読、報告、過去サイクルを保持します。
実験結果と失敗はresults、検証済み補題の候補と未証明仮説もkindで区別します。

pending → running → completed → awaiting_review → reviewed。
中断runningは明示復旧でfailed。破損復旧もfailedとし、人間の照合なしに再実行しません。
reviewedかつacceptedでnext_instructionがある場合だけ、未使用cycle_idで次のpendingへ進めます。
changes_requestedは次サイクル開始を拒否します。修正指示の承認フローは将来の運用設計対象です。
初回本番指示は未承認。MOCKだけがテスト内で承認済みとして作成されます。

## Codex

1. 正本JSON、master_state、next_task、前回査読を読み、承認指示と対象を確認する。
2. worker lockを全サイクル中保持し、revision付きbeginで二重開始を防ぐ。
3. 承認範囲内で実験し、整数等式と厳密演算を使う。
4. 必要な補題をLeanで検証し、ソース・固定依存・実出力を保存する。
5. resultsへ範囲、コマンド、入力、結果、失敗を記録する。検証ラベルは実測に基づく。
6. complete、submitでreportを正本内に固定し、awaiting_reviewへ進める。
7. reportの派生JSONと読みやすい報告、関連コード・ログを出力して停止する。

## ChatGPT

共有リポジトリの直接操作権は仮定しません。人間または将来の明示された連携層が、
report、対象Gitコミット、コード、再現コマンド、Leanログを渡します。
ChatGPTは数学的論理を独立に検討し、有限実験と一般証明を区別して欠陥を記録します。
返すJSONの必須項目はreview.schema.jsonに従います。
cycle_id・report_sha256・report_revisionをそのまま返し、verdict、comments、
次の具体的なnext_instructionを記載します。受理でも仮説は仮説のままです。
次の課題を承認しない場合はnext_instructionをnullにします。

## 連携境界

現状は手動JSONエクスポート／インポートのみです。外部APIは呼びません。
人間が出所を確認しCLIのconfirm-review-sourceを指定した後、対象三点を照合してreviewedへ更新します。
古い査読、別サイクルの査読、既に適用した査読を拒否します。
ハッシュは認証ではありません。API連携時には認証、権限、費用上限、再送の冪等性が別途必要です。
trustedな補題として再利用するには、受理済み査読と実際のLean検証証跡を確認します。
confirmed_resultsは受理済みかつlean_kernelのlemmaだけを抽出しますが、ラベルの真偽は実行者が
ログとソースハッシュで保証する必要があります。JSONだけから証明済みとは断定しません。

## アトミック性と復旧

状態全体に結果と報告を埋め込み、一時ファイルをfsyncしてos.replace、親ディレクトリもfsyncします。
更新前の有効状態を.bakへ保存します。派生報告との複数ファイル同時commitは主張しません。
派生ファイルが失われても状態内reportから再生成できます。
同時更新はflockとrevisionで拒否します。Gitコミットは状態トランザクションとは別処理です。
異常終了時のlockはOSが解放し、runningは残します。recoverでfailedへ記録し、再開はしません。
破損時には暗黙のbackup読込をせず、明示復旧で破損原本を保全してfailedへ移します。
