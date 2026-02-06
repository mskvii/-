# グローバルチャットボット

複数のDiscordサーバー間でチャットを共有できるボットです。

## 🌟 機能

- **グローバルチャット**: 複数サーバー間でリアルタイムチャット
- **翻訳機能**: 自動翻訳で言語の壁を越える
- **サーバー管理**: 参加サーバーの管理
- **フィルタリング**: 不適切な内容のフィルタリング
- **管理者設定**: 各サーバーの管理者が設定可能

## 📝 コマンド

### 管理者用
- `/global_setup` - グローバルチャット設定
- `/global_toggle` - グローバルチャットの有効/無効切り替え
- `/global_filter` - フィルタリング設定

### 一般ユーザー用
- `/global_info` - グローバルチャット情報表示
- `/global_servers` - 参加サーバー一覧

## 🔧 セットアップ

### ローカル環境
1. `.env.example` を `.env` にコピー
2. 環境変数を設定
3. `pip install -r requirements.txt`
4. `python bot.py`

### GitHub + Render デプロイ
1. **GitHubリポジトリにプッシュ**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin <your-repo-url>
   git push -u origin main
   ```

2. **Renderでデプロイ**
   - Render.comにアクセス
   - 「New +」→「Web Service」選択
   - GitHubリポジトリを接続
   - 環境変数を設定：
     - `DISCORD_TOKEN`: あなたのボットトークン
     - `APPLICATION_ID`: あなたのアプリケーションID
   - デプロイ開始

3. **GitHub Actions設定**（任意）
   - リポジトリのSettings→Secretsに環境変数を設定
   - 自動デプロイが有効化

### 環境変数
```env
DISCORD_TOKEN=あなたのDiscordボットトークン
APPLICATION_ID=あなたのアプリケーションID
```

## 📋 必要な権限

- メッセージを送信
- メッセージを読む
- 埋め込みリンクを使用
- 外部コンテンツを表示
