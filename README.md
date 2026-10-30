<!-- Initial upstream README preserved -->
# hello-


# エルデシュ・シュトラウス研究基盤

構築対象は研究環境と検証基盤です。予想の一般証明は試みていません。
正本のリポジトリ: `/path/to/erdos-straus-research`（WSL2のLinuxファイルシステム）。
Windows作業フォルダの同名ディレクトリは閲覧用コピーです。コピー側で状態を更新しないでください。

- 環境・検証の結果: `environment/setup_report.md`
- 実環境調査: `environment/system_report.md`
- 全実行出力: `environment/commands.jsonl`（失敗も保持、UTC時刻）
- 起動・試験・復旧: `environment/operations.md`
- 研究と査読の受け渡し: `automation/protocol.md`
- 次段階の制約: `automation/README.md`

ローカルGitのみ。外部リモート、認証、公開、スケジュールは設定しません。

## 第2段階（2026-10-30）

継承基盤と3サイクル模擬試験を追加しました。41件成功。実ChatGPT往復は未検証のため本番停止中です。
報告: reports/stage2/report.md。操作: automation/stage2/README.md。

## 公開用同期について

このmainは既存GitHub履歴を保持した公開用スナップショットです。ローカル原履歴はprivateに保全し、端末情報・生ログ・生成bundle・キャッシュを除外しています。
公開上の `/path/to/erdos-straus-research` は配置先に置換してください。実ChatGPT往復は未実証、本番スケジュールは無効です。
