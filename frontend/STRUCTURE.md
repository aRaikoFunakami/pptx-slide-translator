# フロントエンド構造説明

## ディレクトリ構成

```
frontend/src/
├── App.tsx                 # メインアプリケーションコンポーネント
├── index.tsx              # エントリーポイント
├── index.css              # グローバルスタイル
├── types/
│   └── index.ts          # TypeScript型定義
├── services/
│   └── api.ts            # APIクライアント
├── hooks/
│   └── index.ts          # カスタムReactフック
└── components/
    ├── index.ts                    # コンポーネントエクスポート
    ├── MonthlyCostCard/
    │   └── index.tsx              # 月次コスト表示カード
    ├── FileUploadArea/
    │   └── index.tsx              # ファイルアップロードエリア
    ├── FileInfoDisplay/
    │   └── index.tsx              # ファイル情報表示
    └── JobStatusDisplay/
        └── index.tsx              # ジョブステータス表示
```

## ファイル説明

### App.tsx
メインアプリケーションコンポーネント。各種カスタムフックとコンポーネントを組み合わせて、
翻訳サービスのUI全体を構成します。

**責任範囲:**
- アプリケーション全体の状態管理
- ユーザーインタラクションのオーケストレーション
- コンポーネント間の連携

### types/index.ts
アプリケーション全体で使用する型定義。

**型:**
- `FileInfo` - アップロードファイルの情報
- `JobStatus` - 翻訳ジョブのステータス
- `MonthlyCost` - 月次コスト情報
- `TargetLang` - 翻訳先言語（'ja' | 'en'）

### services/api.ts
バックエンドAPIとの通信を担当。

**API関数:**
- `uploadFile()` - ファイルアップロードと翻訳ジョブ開始
- `getJobStatus()` - ジョブステータス取得
- `downloadFile()` - 翻訳済みファイルダウンロード
- `getMonthlyCost()` - 月次コスト情報取得

### hooks/index.ts
再利用可能なビジネスロジックをカスタムフックとして提供。

**フック:**
- `useMonthlyCost()` - 月次コスト管理
  - 月次コスト取得と更新
  - 初回マウント時に自動取得
  
- `useJobStatusPolling()` - ジョブステータス監視
  - 2秒間隔でステータスポーリング
  - 完了時に自動停止とコールバック実行
  
- `useFileSelection()` - ファイル選択管理
  - ファイル形式バリデーション（.pptx）
  - ファイルサイズチェック（最大500MB）
  - エラーハンドリング

### components/

#### MonthlyCostCard
月次の翻訳コストサマリーを表示。

**Props:**
- `monthlyCost: MonthlyCost` - 表示する月次コスト情報

**表示内容:**
- 対象月
- 累計費用（USD）
- 累計トークン数
- 翻訳回数

#### FileUploadArea
ファイルのドラッグ&ドロップとファイル選択UI。

**Props:**
- `isDragOver: boolean` - ドラッグオーバー状態
- `fileInputRef: RefObject<HTMLInputElement>` - ファイル入力要素への参照
- `onFileSelect: (file: File) => void` - ファイル選択時のコールバック

**機能:**
- ドラッグ&ドロップによるファイル選択
- クリックによるファイル選択ダイアログ表示

#### FileInfoDisplay
選択されたファイルの情報を表示。

**Props:**
- `file: File` - 選択されたファイル
- `fileInfo: FileInfo | null` - サーバーから取得した追加情報

**表示内容:**
- ファイル名
- ファイルサイズ
- ページ数（取得後）
- 翻訳対象テキスト数（取得後）

#### JobStatusDisplay
翻訳ジョブの進行状況と結果を表示。

**Props:**
- `jobStatus: JobStatus` - ジョブステータス
- `onDownload: () => void` - ダウンロードボタンクリック時のコールバック
- `onReset: () => void` - リセットボタンクリック時のコールバック

**機能:**
- ステータス別の表示切り替え（queued/processing/completed/failed）
- プログレスバー表示
- 翻訳コスト情報表示（完了時）
- エラーメッセージ表示（失敗時）

## リファクタリングの利点

### 1. 保守性の向上
- 各ファイルが単一責任を持つ
- 変更の影響範囲が明確
- テストが書きやすい構造

### 2. 再利用性
- カスタムフックで共通ロジックを抽出
- コンポーネントの独立性が高い
- 他のプロジェクトへの移植が容易

### 3. 可読性
- ファイルサイズが小さく理解しやすい
- 命名が明確で意図が伝わりやすい
- ディレクトリ構造が役割を表現

### 4. スケーラビリティ
- 新機能追加時の影響が限定的
- チーム開発での並行作業が容易
- 段階的な機能拡張が可能

## 開発ガイドライン

### 新しいコンポーネントの追加
1. `components/` 配下にディレクトリを作成
2. `index.tsx` にコンポーネントを実装
3. `components/index.ts` にエクスポートを追加

### 新しいAPIエンドポイントの追加
1. 型定義を `types/index.ts` に追加
2. API関数を `services/api.ts` に追加
3. 必要に応じてカスタムフックを作成

### 状態管理のベストプラクティス
- グローバルな状態は `App.tsx` で管理
- ローカルな状態はコンポーネント内で管理
- 複雑なロジックはカスタムフックに抽出
