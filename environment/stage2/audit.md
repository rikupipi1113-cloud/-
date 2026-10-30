# 第1段階環境の再監査

2026-10-30 JSTに再実行しました。

| 項目 | 実測結果 |
|---|---|
| 既存pytest | 19 passed in 0.74s |
| Lean | 4.19.0 / 6caaee842e94 / Release |
| mathlib | 固定v4.19.0、lake build成功、sorryAxなし |
| 状態保存と復元 | 既存19件内で保存、破損復旧、実プロセス異常終了を再検証 |
| サイクル管理 | 未承認開始、二重開始、古い査読、未査読の次回開始の拒否が成功 |
| Git | git fsck正常、元履歴1c4e760まで保持、監査開始時差分なし、remoteなし |
| Codex CLI | 0.166.0-alpha.5.1、exec/resumeヘルプ取得、AI実行は未実施 |
| Python依存 | 既存venvと固定版を継続、pip check成功、新規インストールなし |

プロジェクト外からLeanを版指定なしで呼ぶとdefault toolchain未設定で失敗しました。
これは専用elanでグローバルdefaultを設定していない意図どおりの動作です。
leanフォルダ内、または明示+leanprover/lean4:v4.19.0で成功しました。
一度ログスクリプト相対パスを誤参照しましたが、正本パスで再実行して記録しました。
production初期化は最初システムpythonで実行してmodule未検出、専用venvで実行し成功しました。
既存ファイルや依存を削除・上書きして回避していません。

実出力はenvironment/commands.jsonl、Lean出力はenvironment/stage2/lean_audit.txt。
第1版のソース・テスト・状態JSON・固定依存ファイルは1c4e760から変更していません。
