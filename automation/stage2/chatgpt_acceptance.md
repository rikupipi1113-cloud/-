# 実ChatGPT往復の受け入れ試験（未実施）

用意済み診断入力: reports/stage2/integration-probe/request.json。
これは研究課題の承認や模擬査読ではなく、別のChatGPTからの取得・返却を検証する専用nonce付き診断です。

1. ユーザーが別ChatGPTチャットを開き、request.jsonを添付する。
   GitHub経由にする場合は、承認された書込経路で診断ファイルを配置した後、そのcommit指定URLを渡す。
2. ChatGPTへ「これは接続試験。challenge_idとrequest_sha256を返し、n=2,x=1,y=z=2の整数等式を独立に確認し、
   response.schema.jsonに従うJSONを返す。研究開始を承認しない」と依頼する。
3. ChatGPTの返却JSONをreviewsの新規ファイルへ人間が保存する。出所のチャットと日時を記録する。
4. environment/stage2/validate_probe.pyへ入力・応答・出所確認を渡す。
5. ユーザーが実際の往復を確認してから、実連携の実証として記録する。

```sh
python environment/stage2/validate_probe.py reports/stage2/integration-probe/request.json reviews/PROBE_RESPONSE.json --confirm-source
```

validatorのMOCK自己試験は別途実施しますが、それを実ChatGPT往復とは扱いません。
この診断成功だけでも定期実行は有効になりません。次に実研究の報告・査読の継承、
共有側への保存完了、production adapter、初回課題、ユーザー承認を確認する必要があります。
