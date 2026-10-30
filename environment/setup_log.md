# 構築ログ案内

正本: commands.jsonl。UTC時刻、cwd、argv/command、終了コード、実出力を保存しています。
文字コード対応後はraw_base64も保存し、Windows出力の原本を保持します。
初期調査ではshell command形式、その後はargv形式です。末尾に追記します。
ファイル生成・配置はCodexのローカルPythonとcpで行い、対象は新規専用リポジトリだけです。
一時venvプローブは/tmp/es-venv-probeに作成しました。既存環境は変更していません。

## 発生した失敗と対処（成功ログと区別）

1. 通常サンドボックスでgithub.com/PyPIのDNS解決失敗、Windows interop socket失敗。
   制限外での同じ読取・通信は成功。システム設定を変更せず専用ディレクトリで実施。
2. 初回PowerShellのwsl短縮名がPATHで解決できず。Linux側からwsl.exeを明示して取得成功。
3. Windowsディスク取得のCIMクエリ引用符が不正。不要なクエリを除きGet-PSDriveで取得成功。
4. wsl.exe出力がUTF-16LEのためUTF-8デコード失敗。生バイト保存と文字コード判別に修正。
5. 初回pytestは生成したテスト内の改行文字列の構文ミスでcollection失敗。修正後16件成功。
6. Leanの実行ログスクリプトをlean/environmentと誤参照。../environmentへ訂正。
7. cache getに依存パッケージ内のファイル相対パスを指定して失敗。モジュール名指定で成功。
8. Nat.Prime 2をnorm_numだけで証明できずビルド失敗。Nat.prime_twoで証明して成功。
   失敗時にLeanが出したsorryAxを含む未完成宣言は検証済みとして採用していません。
9. 修正時の作業ディレクトリ違いで一度ファイル参照失敗。絶対パスで修正し再ビルド成功。
10. 復旧処理をfail-closedに強化し、同時開始と報告改竄の試験を追加。18件成功。その後JSON正規化・非有限数拒否を追加して最終19件成功。
    途中の18件のpytestに121.74秒かかり、/procでLinux FSのjournal/page同期待ちを観測。
    永続化の保証を削る回避はせず正常終了を待ちました。将来の性能監視対象です。

apt、sudo、管理者操作、既存ツールの削除、外部認証、push、スリープ変更、サービス登録、
自動スケジュール登録は実施していません。venv内setuptoolsのみ隔離環境内で更新しました。
