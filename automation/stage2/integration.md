# ChatGPTとCodexの共有方法の調査（2026-10-30）

## 指定GitHubリポジトリでの実測

対象: [rikupipi1113-cloud/-](https://github.com/rikupipi1113-cloud/-)

| 調査 | 実結果 | 解釈 |
|---|---|---|
| GitHub連携list_repositories | 空配列 | 一覧だけでは対象repoの可否は判断できなかった |
| get_repo（直接指定） | 成功、public、default main、pull=true、push=false | 現チャットの連携は読取可・書込不可 |
| contents取得 | README.md 1件、3 bytes | 容量表示0でも空repoではない |
| fetch_file（commit指定） | README.md本文 `# -` を取得 | コネクタで実ファイルの読み取りに成功 |
| Git ls-remote | main/HEAD=9601c6438d50f4ca2eaec01b72777f4d9bc00eab | WSLからの匿名読取成功 |
| research-memory refのfetch | 失敗：remote refなし | 研究共有パケットはまだ配置されていない |
| 研究データの書込・査読の書込 | 未実施 | 権限なし。書込済み、実往復済みとは報告しない |

生のコネクタ結果はenvironment/stage2/connector_probe.json、Gitコマンドはenvironment/commands.jsonl。
これはCodexチャットの接続を調べた結果です。独立したChatGPTチャットの実行・接続を証明するものではありません。
公開repoのREADME読取成功は、本研究の報告や査読が読めることの実証でもありません。

## 方法の比較

| 方法 | 正式な機能 | このセッションで実証した範囲 | 残る作業 |
|---|---|---|---|
| GitHub plugin | ChatGPT/Codexで利用可能なpluginがある | Codex側の指定repo読取、書込不可の権限情報 | ChatGPT側で同じrepoを読む／査読を書込む試験、書込権限と公開範囲の承認 |
| 手動ファイル添付 | ChatGPTへのcontext添付と出力の受渡し | JSON exportとimport検証コード、MOCK往復 | 別ChatGPTへ渡し、実査読JSONを人間経由で取り込む試験 |
| ChatGPT Library | optional file upload/select/download拡張 | 公式仕様のみ確認 | 現セッションでLibraryを定期読書きするAPIは未提供。共有DBやWSL自動同期として使えると仮定しない |
| custom MCP plugin | ChatGPTは接続済みMCPの読書きツールを利用できる | 公式仕様のみ確認 | 認証、サーバー／トンネル、接続承認、対象範囲、実往復試験。今回は作成・公開しない |

[公式Plugins](https://learn.chatgpt.com/docs/plugins)、
[Libraryの公式file API仕様](https://developers.openai.com/plugins/reference#file-apis)、
[公式custom MCP接続](https://developers.openai.com/api/docs/guides/custom-mcp-server)。
Libraryが利用可能な全アカウントに永続共有書込みAPIがある、という仕様ではありません。
OpenAI APIを使う方式はChatGPT製品の査読チャットとは別の実装・認証・費用を伴うため、今回は接続しません。

## 実装した境界

GitExchange.read_handoffは指定refから一時repoへfetchし、commit内のexchange/package.jsonだけを読みます。
全イベントと全objectを検証し、handoff/contextとの一致を確認して返します。
外部repoのスクリプト実行や自動mergeを行いません。取得失敗時は次の研究を開始しません。
GitExchange.publish_localはMOCKかつ指定lab内のローカルbare repoだけへ書込みます。
ネットワークrepoやproduction記憶の送信を拒否します。GitHub書込adapterは未実装です。

共有候補ブランチ: refs/heads/research-memory。
共有パケット: protocol、handoff（memory_head/context_sha256/instruction_sha256/last_review）、
context（全本文・証拠）、files（events/objects/latest）を含むJSON。
査読JSONはcycle_id/report_sha256/memory_headで対象に結び付け、reviewer_kind、verdict、
accepted_lemma_ids、comments、next_instruction、reviewed_atを保存します。
ハッシュとreviewer文字列は認証ではなく、人間または将来の認証済みadapterが出所を確認します。

## 承認後の推奨ルート

最初に手動添付で実ChatGPT往復を一度実証するのが最小構成です。
その後、指定GitHubの書込権限と、公開repoへ研究記録を送る範囲を承認し、専用ブランチに限定します。
ChatGPTで読取だけ可能な場合は査読JSONを手動で返す運用を続け、自律運用完了とは扱いません。
今回はremote追加・push・ファイル更新・Issue投稿・認証変更を行っていません。
