# PPTX翻訳Webサービス

PowerPointファイルを翻訳するWebサービスです。FastAPI + React + Dockerで構築されており、シンプルかつ手堅い実装になっています。

## 🌟 特徴

- **簡単操作**: ドラッグ&ドロップでPPTXファイルをアップロード
- **高品質翻訳**: OpenAI GPT-4o-miniを使用した高品質な翻訳
- **プライバシー保護**: ファイルは翻訳後に即座に削除
- **リアルタイム進捗**: キューの待機状況と翻訳進捗をリアルタイム表示
- **詳細ログ**: 全ての処理ログとメトリクスを記録
- **Docker対応**: 1つのコマンドで簡単にデプロイ可能

## 🚀 クイックスタート

### 前提条件

- Docker & Docker Compose
- OpenAI APIキー

### 1. リポジトリをクローン

```bash
git clone https://github.com/aRaikoFunakami/pptx-slide-translator.git
cd pptx-slide-translator
```

### 2. 環境変数を設定

```bash
cp .env.example .env
```

`.env`ファイルを編集してOpenAI APIキーを設定：

```env
OPENAI_API_KEY=your-openai-api-key-here
```

### 3. サービスを起動

```bash
docker-compose up -d
```

### 4. Webブラウザでアクセス

```
http://localhost:8000
```

## 📋 使用方法

1. **ファイルアップロード**: PPTXファイルをドラッグ&ドロップまたはクリックで選択
2. **翻訳言語選択**: 日本語 ⇔ 英語を選択
3. **翻訳開始**: 「翻訳を開始」ボタンをクリック
4. **進捗確認**: キューでの待機状況と翻訳進捗をリアルタイムで確認
5. **ダウンロード**: 翻訳完了後、翻訳済みファイルをダウンロード

## ⚙️ 設定

### 環境変数

| 変数名 | 必須 | デフォルト | 説明 |
|--------|------|------------|------|
| `OPENAI_API_KEY` | ✅ | - | OpenAI APIキー |
| `OPENAI_MODEL` | ❌ | `gpt-4o-mini` | 使用する翻訳モデル |
| `OPENAI_BASEURL` | ❌ | - | カスタムAPIエンドポイント（ローカルLLM用） |
| `MAX_CONCURRENT_TRANSLATIONS` | ❌ | `1` | 同時翻訳処理数 |

### ローカルLLMを使用する場合

Ollamaなどのローカルモデルを使用する場合：

```env
OPENAI_API_KEY=dummy
OPENAI_MODEL=gemma3:12b
OPENAI_BASEURL=http://localhost:11434/v1
```

## 📊 ログとメトリクス

### ログファイル

- `logs/app.log`: アプリケーションログ
- `logs/metrics.jsonl`: メトリクスログ（JSON Lines形式）

### メトリクス情報

各翻訳リクエストについて以下の情報を記録：

- IPアドレス
- ファイル名・サイズ
- ページ数・テキスト数
- 翻訳言語
- 処理時間
- 成功/失敗状況
- エラー詳細（失敗時）

### ログ分析例

```bash
# 翻訳成功率を確認
cat logs/metrics.jsonl | jq -r 'select(.status) | .status' | sort | uniq -c

# IPアドレス別の使用状況
cat logs/metrics.jsonl | jq -r 'select(.ip_address) | .ip_address' | sort | uniq -c

# 平均処理時間
cat logs/metrics.jsonl | jq -r 'select(.processing_time) | .processing_time' | awk '{sum+=$1} END {print sum/NR}'
```

## 🛠️ 開発・カスタマイズ

### 開発環境での起動

バックエンドのみ起動する場合：

```bash
cd backend
pip install -r requirements.txt
export OPENAI_API_KEY=your-key
python main.py
```

フロントエンド開発：

```bash
cd frontend
npm install
npm start
```

### ファイルサイズ制限の変更

`backend/main.py`の`MAX_FILE_SIZE`を変更：

```python
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB
```

### 同時処理数の変更

環境変数で調整可能：

```env
MAX_CONCURRENT_TRANSLATIONS=3
```

## 🔒 セキュリティ

- **ファイル保護**: アップロードされたファイルは翻訳後に即座に削除
- **サイズ制限**: 最大500MBまでのファイルのみ受付
- **形式制限**: PPTXファイルのみ受付
- **タイムアウト**: 5分でタイムアウト

## 📈 パフォーマンス

- **並列処理**: テキストを10個ずつバッチ処理で並列翻訳
- **メモリ効率**: 一時ファイルの適切な管理
- **非同期処理**: FastAPIの非同期機能を活用

## 🐛 トラブルシューティング

### よくある問題

1. **「OPENAI_API_KEYが設定されていません」エラー**
   - `.env`ファイルにAPIキーが正しく設定されているか確認

2. **翻訳が失敗する**
   - `logs/app.log`でエラー詳細を確認
   - APIキーの残高・制限を確認

3. **ファイルがアップロードできない**
   - ファイルサイズ（500MB以下）と形式（.pptx）を確認

### ログの確認

```bash
# リアルタイムでログを確認
docker-compose logs -f pptx-translator

# エラーログのみ表示
docker-compose logs pptx-translator | grep ERROR
```

## 📄 ライセンス

MIT License

## 🤝 コントリビューション

プルリクエストやイシューの報告を歓迎します。

---

**注意**: このサービスはOpenAI APIを使用するため、翻訳処理には料金が発生します。使用量にご注意ください。