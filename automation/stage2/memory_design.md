# 永続研究記憶 v2

## 保存単位

| 場所 | 内容 | 更新方式 |
|---|---|---|
| events/00000001.json以降 | 連番、前イベントhash、操作、UTC時刻、状態snapshot、イベントhash | 排他的な新規公開。既存ファイルは置換しない |
| objects/SHA256 | 証明全文、検証ログ、仮説、失敗、実験条件と結果、先行研究、課題、指示、査読 | 内容hashによる保存。既存の異なる内容を拒否 |
| latest.json | 最新headと最新研究状態 | 同一FS上の一時ファイルからatomic replace |
| quarantine/ | 明示修復前の破損latest原本 | 排他的保存 |

記録のkindはlemma/hypothesis/failed_approach/experiment/prior_work/open_problem/instruction/review。
すべての研究記録は本文objectと証拠objectを参照します。修正は新規recordを追加し、supersedesで旧版を指します。
旧版、失敗、古い未解決課題も削除しません。過去の全版はcontextにも含めます。
サイクルごとの指示全文、報告全文、査読全文、途中状態もobjectに残します。
JSON Schemaはmemory.schema.jsonとreview.schema.json。

## 検証と継承

開始前にイベント列を全再生し、連番・hash鎖・全objectのhash・schema・latestとの一致を検証します。
開始時に、全記録本文・証拠全文・過去サイクル・各指示を含むcontextを生成します。
呼出元がそのcontextのhashをacknowledgeし、Gitの共有パケットを新規fetchして照合します。
ローカルhead、context hash、指示hash、最後の査読objectが共有側と完全一致する必要があります。
履歴不足、古いcontext、同期失敗、未査読、重複slot、revision競合のどれでも開始を拒否します。
開始イベントにinherited_head、inherited_ids、context_sha256、共有Git commitを保存します。

hash照合が示すのは入力の一致です。AIの意味理解や独立した数学査読の正しさまでは証明しません。
現在のmock試験はPythonの新規読取処理で継承を確認し、別のAIモデルを起動した試験ではありません。

## 確定事項の境界

lemmaには証明全文、Leanビルド成功ログ、toolchainが必要です。sorry/admit/独自axiom、sorryAxを拒否します。
ただしログの出所を暗号学的に認証する仕組みではなく、実行者は実ビルドとsource hashを照合する責任があります。
研究の確定補題として抽出するには、形式検証済みlemmaを査読が明示的にaccepted_lemma_idsへ列挙する必要があります。
仮説や有限実験のIDは受理できません。査読acceptedだけで仮説を補題へ変換しません。
supersedesされた補題は新規再利用の確定リストから外しますが、本文と査読は履歴に残します。
実験のverificationは自動でpython_exactにしません。本文に整数検証の条件・両辺・範囲を保存します。

## 障害時

journalイベントをfsyncして排他的に公開し、その後latestをatomicに更新します。
両者の間で停止した場合、次回は不一致を検出し、研究を開始しません。
明示repairはjournalからlatestだけを再生成し、開始済みサイクルをpendingへ戻しません。
journalまたはobject自体の破損は修復で推測補完せず停止します。Git/共有コピーと人間が照合します。
worker lockをdispatch/resumeのcontext全体で保持し、更新lockとrevisionで競合を防ぎます。
異常終了はチェックポイントとrunningを残します。recoverはfailedにし、次回開始を許しません。

## 制約

信頼されたローカル利用者を前提とします。ファイル所有者による両側全履歴の書換え・全体rollbackは防ぎません。
LinuxローカルFS上のflock、fsync、hard-linkによる排他公開に依存します。
Gitコミットと状態更新は単一トランザクションではありません。開始前の共有照合で不一致を拒否します。
全snapshotと全objectの検証・転送なので長期運用では容量と再生時間が増加します。
共有パケットの読取上限は32 MiBです。長期運用前に追記objectの差分転送と外部anchorを設計する必要があります。
過去ログを削除する自動圧縮は実装していません。
