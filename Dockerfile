# マルチステージビルド: フロントエンドのビルド
FROM node:18-alpine AS frontend-builder

WORKDIR /app/frontend

# ソースコードをコピー
COPY frontend/ .

# 依存関係をインストールしてビルド
RUN npm install && npm run build

# メインステージ: バックエンドとフロントエンドの統合
FROM python:3.11-slim

# システムの依存関係をインストール
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 作業ディレクトリを設定
WORKDIR /app

# Pythonの依存関係をインストール
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# バックエンドのソースコードをコピー
COPY backend/ ./backend/

# 既存の翻訳ロジックをコピー
COPY pptx_slide_translator/ ./pptx_slide_translator/

# フロントエンドのビルド結果をコピー
COPY --from=frontend-builder /app/frontend/build ./frontend/build

# ログディレクトリを作成
RUN mkdir -p /app/logs

# 環境変数の設定
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# デフォルトの環境変数
ENV OPENAI_MODEL=gpt-4o-mini
ENV MAX_CONCURRENT_TRANSLATIONS=1

# ポートを公開
EXPOSE 8000

# アプリケーションを起動
CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]