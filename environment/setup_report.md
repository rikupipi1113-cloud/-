# 環境構築報告書（2026-10-30 JST）

環境構築と検証が完了しました。一般証明の研究は開始していません。
研究リポジトリの正本: `/path/to/erdos-straus-research`。
導入版・配置はdependencies.md、実環境はsystem_report.md、操作はoperations.mdを参照。

## 要求された動作試験

| No. | 試験 | 結果 | 実証内容・出力 |
|---|---|---|---|
| 1 | Python仮想環境 | 成功 | environment_checks.json: venv_isolated=true、実行パス.venv/bin/python |
| 2 | SymPy厳密有理数 | 成功 | Rational(1,3)+Rational(1,6)==Rational(1,2) |
| 3 | 素数生成 | 成功 | 20未満: 2,3,5,7,11,13,17,19 |
| 4 | 既知の小解 | 成功 | n=2,3,4,5、整数等式の両辺16,192,144,640。誤候補も拒否 |
| 5 | pytest | 成功 | 最終19 passed in 4.89s |
| 6 | Lean 4 | 成功 | Lean version 4.19.0、Release、6caaee842e94 |
| 7 | mathlib証明ビルド | 成功 | lake build: Build completed successfully、5補題の公理依存表示 |
| 8 | Git追跡 | 成功 | ローカルコミットとgit ls-filesにより検証。git_verification.json参照 |
| 9 | 状態保存・復元 | 成功 | schema検証、再読込、backup、破損原本保全、明示復旧をpytestで実行 |
| 10 | 模擬研究サイクル | 成功 | reports/mock-cycle-final/summary.json。模擬査読、次ID、中断復旧 |
| 11 | 異常終了復旧 | 成功 | 子プロセスos._exit(19)後runningを読み、recoverでfailedへ。保存中断試験も成功 |
| 12 | 未査読の昇格防止 | 成功 | awaiting_reviewから次サイクルを拒否。受理済み仮説もlemmaへ昇格しない |

追加: CMake 3.31.6でGCC/G++ 11.4.0によるC/C++ configure/build/run成功、pip check成功。
二重開始、revision競合、古い査読、重複ID、報告書改竄、生存worker中の復旧を拒否する試験も成功。
模擬サイクルの最後のfailedは中断復旧試験の期待値であり、環境試験の失敗ではありません。

## 最終pytest実出力

```text
============================= test session starts ==============================
platform linux -- Python 3.10.12, pytest-8.4.2, pluggy-1.7.0 -- /path/to/erdos-straus-research/.venv/bin/python
cachedir: .pytest_cache
rootdir: /path/to/erdos-straus-research
configfile: pyproject.toml
testpaths: tests
collecting ... collected 19 items

tests/test_math.py::test_known_solutions_and_rejection PASSED            [  5%]
tests/test_math.py::test_reject_invalid[0] PASSED                        [ 10%]
tests/test_math.py::test_reject_invalid[-1] PASSED                       [ 15%]
tests/test_math.py::test_reject_invalid[True] PASSED                     [ 21%]
tests/test_math.py::test_reject_invalid[1.0] PASSED                      [ 26%]
tests/test_math.py::test_exact_and_number_theory PASSED                  [ 31%]
tests/test_state.py::test_roundtrip_schema_and_no_overwrite PASSED       [ 36%]
tests/test_state.py::test_unapproved_duplicate_and_stale PASSED          [ 42%]
tests/test_state.py::test_initial_unapproved PASSED                      [ 47%]
tests/test_state.py::test_review_binding_and_gate PASSED                 [ 52%]
tests/test_state.py::test_rejected_review_blocks_next PASSED             [ 57%]
tests/test_state.py::test_worker_lock_blocks_recovery PASSED             [ 63%]
tests/test_state.py::test_atomic_interrupted_replace PASSED              [ 68%]
tests/test_state.py::test_corruption_backup_explicit_restore PASSED      [ 73%]
tests/test_state.py::test_actual_killed_worker PASSED                    [ 78%]
tests/test_state.py::test_demo PASSED                                    [ 84%]
tests/test_state.py::test_concurrent_begin_only_one PASSED               [ 89%]
tests/test_state.py::test_tampered_report_rejected PASSED                [ 94%]
tests/test_state.py::test_result_normalizes_json_keys_and_rejects_nan PASSED [100%]

============================== 19 passed in 4.89s ==============================
```

## 最終Leanビルド実出力

```text
ℹ [711/712] Built ErdosStrausResearch
info: ././././ErdosStrausResearch.lean:12:0: 'nat_add_check' depends on axioms: [propext]
info: ././././ErdosStrausResearch.lean:13:0: 'int_square_identity' depends on axioms: [propext]
info: ././././ErdosStrausResearch.lean:14:0: 'six_divides_twelve' depends on axioms: [propext]
info: ././././ErdosStrausResearch.lean:15:0: 'two_is_prime' depends on axioms: [propext, Classical.choice, Quot.sound]
info: ././././ErdosStrausResearch.lean:16:0: 'known_solution_two' depends on axioms: [propext]
Build completed successfully.
```

標準基礎公理propext/Classical.choice/Quot.soundへの依存を表示しています。
独自の公理を追加せず、成功した最終ビルドにsorryAxはありません。
ソースにもsorry/admit/axiomの宣言を含まないことをチェックしました。

## 状態と成果の境界

本番setup-000はpending、承認false、研究成果なし。MOCK査読は本番に適用していません。
実際のChatGPTによる数学査読、外部共有、自動周期実行は未実施です。
完了の範囲は今回指定の環境構築・試験です。3時間周期の自律運用の完成を意味しません。

## 残る制約

- ChatGPT接続、初回指示承認、差戻し・failed後の運用は次段階。automation/README.md参照。
- Windows GitはPATHと標準配置で未検出。WSL Gitを使用し、Windows側への追加導入は不要でした。
- fsyncを伴う試験で約2分のI/O待機を一度観測。長時間安定性、停電、実OS停止は未検証。
- Git/JSONは認証や改竄防止境界ではありません。査読の出所確認と全workerのAPI遵守が必要。
- ログと固定版を保存していますが、wheel一式の保管・完全オフライン再構築は未実施。

失敗履歴と対処はsetup_log.md、全コマンドの実出力はcommands.jsonlに保存しています。
