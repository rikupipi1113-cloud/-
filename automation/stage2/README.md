# 第2段階：継承基盤（本番停止中）

正本: `/path/to/erdos-straus-research`。第1版Storeは変更せず残しています。
第2版の記憶は `research/memory-v2/`、設定は `automation/stage2/schedule.json`。
**実ChatGPT往復は未検証のため、第2段階全体の完了条件はまだ満たしていません。**
設定はenabled=false / integration_verified=false。スケジュールは登録していません。
設定だけをtrueへ変更してもproduction研究開始はハードガードで拒否します。

- 記憶と整合性: memory_design.md
- 時刻と中断方式: schedule_design.md
- 共有手段と実測権限: integration.md
- 操作と復旧: operations.md
- 承認前の実往復試験: chatgpt_acceptance.md
- 報告書: reports/stage2/report.md

mockは研究開始・査読・同期を模擬する専用モードです。MOCK査読はproductionへ取り込めません。
第1版の手動CLIには第2版の継承ゲートがないため、将来の定期実行から呼び出してはいけません。
