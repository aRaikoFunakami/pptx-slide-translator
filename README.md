# PPTX Slide Translator

PowerPoint翻訳ツール - OpenAI APIを使用してPPTXファイル内のテキストを翻訳します。

## 特徴

- PowerPointファイル（.pptx）内のテキストを一括翻訳
- OpenAI API（GPT-4、GPT-3.5-turbo等）およびOpenAI互換APIに対応
- ローカル/OSSモデル（Ollama等）にも対応
- 日本語⇔英語の双方向翻訳
- グループ化されたオブジェクトやテーブル内のテキストも翻訳対応
- バッチ処理による高速翻訳
- 進捗表示機能

## インストール

### uv toolでのインストール（推奨）

```bash
uv tool install git+https://github.com/YOUR_USERNAME/pptx-slide-translator.git
```

### pipでのインストール

```bash
pip install git+https://github.com/YOUR_USERNAME/pptx-slide-translator.git
```

## 設定

### OpenAI API

```bash
export OPENAI_API_KEY="your-openai-api-key"
```

### ローカル/OSSモデル（Ollama等）

```bash
export OPENAI_API_KEY="dummy"  # 空でない値が必要
export OPENAI_MODEL="llama3.2"  # または任意のモデル名
export OPENAI_BASEURL="http://localhost:11434/v1"
```

## 使用方法

### 基本的な使用方法

```bash
# 英語に翻訳（デフォルト）
pptx-translate presentation.pptx

# 日本語に翻訳
pptx-translate presentation.pptx -l ja

# 出力ファイル名を指定
pptx-translate presentation.pptx -o translated.pptx
```

### モデルとAPIエンドポイントの指定

```bash
# 特定のOpenAIモデルを使用
pptx-translate presentation.pptx -m gpt-4-turbo

# ローカル/OSSモデルを使用
pptx-translate presentation.pptx -m llama3.2 -u http://localhost:11434/v1
```

## コマンドラインオプション

```text
usage: pptx-translate [-h] [-o OUTPUT] [-l {ja,en}] [-m MODEL] [-u BASEURL] input_file

PPTX翻訳ツール

positional arguments:
  input_file            入力PPTXファイルのパス

options:
  -h, --help            show this help message and exit
  -o OUTPUT, --output OUTPUT
                        出力PPTXファイルのパス (デフォルト: output_translated.pptx)
  -l {ja,en}, --lang {ja,en}
                        翻訳先言語 (ja: 日本語, en: 英語) (デフォルト: en)
  -m MODEL, --model MODEL
                        AIモデル名 (例: gpt-4.1-mini, gpt-oss:20b, local-llama)
  -u BASEURL, --baseurl BASEURL
                        OpenAI互換API のベースURL (例: http://localhost:11434/v1)
```

## 環境変数

- `OPENAI_API_KEY`: OpenAI APIキー（必須）
- `OPENAI_MODEL`: 使用するモデル名（デフォルト: gpt-4.1-mini）
- `OPENAI_BASEURL`: APIのベースURL（OpenAI互換API使用時）

## 対応するOpenAI互換API

- OpenAI API
- Ollama
- LM Studio
- その他のOpenAI互換エンドポイント

## 必要な環境

- Python 3.13以上
- OpenAI APIキー（または互換APIアクセス）

## ライセンス

MIT License