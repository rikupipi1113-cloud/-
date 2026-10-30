# 依存関係と選定

| ツール | バージョン | 配置・扱い |
|---|---|---|
| Python | 3.10.12 | 既存/usr/bin/python3を利用、変更なし |
| pip | 22.0.2 | venv内、既存システム版変更なし |
| pytest | 8.4.2 | .venv |
| SymPy | 1.14.0 | .venv、厳密有理数・素数・因数分解 |
| NumPy | 2.2.6 | .venv、集計用。等式証明には使わない |
| mpmath | 1.3.0 | .venv、数値的参考計算用。等式証明には使わない |
| jsonschema | 4.25.1 | .venv、状態・査読形式検証 |
| CMake | 3.31.6 | .venv/bin/cmake、C/C++ビルド試験成功 |
| setuptools/wheel | 80.9.0 / 0.45.1 | .venvのみで更新 |
| Git | 2.34.1 | 既存/usr/bin/git |
| GCC/G++ | 11.4.0 | 既存/usr/bin、実コンパイル成功 |
| GNU Make | 4.3 | 既存/usr/bin/make |
| elan | 4.2.4 | .tools/elan/bin、シェル初期化変更なし |
| Lean | 4.19.0 / 6caaee842e94 | .tools/elan/toolchains、リリース版 |
| Lake | 5.0.0-6caaee8 | 同Leanに同梱 |
| mathlib | v4.19.0 / c44e0c8ee63ca166450922a373c7409c5d26b00b | lean/.lake/packages/mathlib |

最新追従は行わずPython 3.10互換の版と、同一タグ対応のLean/mathlibを選定し、実際のビルドで確認。
推移Python依存はrequirements.lock.txt、Lean依存はlake-manifest.jsonに固定。
elan-init.shは公式v4.1.2のスクリプトを取得しましたが、同スクリプトが取得した実バイナリは
4.2.4でした。実測版を記録し、ユーザーの既存elanや既定toolchainは変更していません。
mathlibのlake updateフックが全6641モジュールのキャッシュを取得したため、.lakeは約5.6 GiBです。
その後、指定した3モジュールのキャッシュ照合にも成功しました。

公式手順: [Lean install](https://lean-lang.org/install/manual/)、
[mathlib dependency](https://github.com/leanprover-community/mathlib4/wiki/Using-mathlib4-as-a-dependency)。

## 任意ツールの評価

| ツール | 用途 | 導入費用・判断 |
|---|---|---|
| PARI/GP | 高速な整数論実験 | 当面SymPyで足りるため未導入。将来大量因数分解が必要なら検討 |
| SageMath | 統合的代数計算 | 依存と容量が大きく、今回の基盤試験には不要で未導入 |
| gmpy2 | 多倍長整数高速化 | wheel互換性・GMP依存の追加評価が必要。ボトルネック測定後に検討 |
| Ruff | 静的解析・整形 | 低コストだが必須検証に含めず未導入 |
| mypy | 型検査 | 型注釈整備を伴うため未導入 |

この環境は任意ツールなしで試験を通過しました。浮動小数点の近似計算を証明には使用していません。
