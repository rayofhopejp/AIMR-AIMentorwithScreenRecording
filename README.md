# AI画面監視エージェント

デスクトップ画面を定期的に監視し、AWS Bedrock Claude で分析してAmazon Pollyで音声アドバイスを提供するアプリケーション。

## アイディア
仕事とか作業してるとき、常に画面を見ながら「これは〇〇だね！」とか「〇〇すればいいんじゃない？」とか言ってくるAIエージェントが欲しい
ほぼ cline とか Amazon Q Dev とかの IDE 拡張だけど、それらの監視対象がデスクトップ全体に広がりつつ、かつ能動的に働きかけてくる感じ
pythonで構成されたローカルアプリを実行すると、画面が出てくる。そこにはAWSのシークレットキーなどを入力するところとスイッチがある。スイッチをオンにしている間は、画面のスクリーンショットを指定した時間（分単位）で取得して、その画像をBedrock の Claude で処理してアドバイスやコメントを作成し、それをAmazon Polly で音読する。
これを実現するローカルアプリのpythonコード。

## セットアップ

1. 依存関係のインストール:
```bash
pip install -r requirements.txt
```

2. アプリケーション実行:
```bash
python web_gui_fixed.py
```

## 使用方法

1. AWS認証情報（Access Key ID、Secret Access Key、Region）を入力
2. スクリーンショット間隔（分）を設定
3. 「監視開始」ボタンをクリック
4. AIが画面を分析して音声でアドバイスを提供

## 必要なAWS権限

- bedrock:InvokeModel
- polly:SynthesizeSpeech

Amazon Bedrock で Cross Region Interfaces us.anthropic.claude-3-7-sonnet-20250219-v1:0 が使えるようにする必要があります。

## 注意事項

- macOSの場合、画面録画権限の許可が必要
- AWS料金が発生します（Bedrock、Polly使用量に応じて）
