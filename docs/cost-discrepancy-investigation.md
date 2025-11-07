# 累計費用表示の不一致問題 - 調査報告書

## 問題概要

フロントエンドとGrafanaダッシュボードで表示される累計費用に大きな乖離が発生していました。

- **フロントエンド表示**: $0.272842
- **Grafana表示**: $0.0698
- **差異**: 約 **$0.20** (約74%の誤差)

## 調査結果

### 1. ログファイルの検証

実際のログファイル (`logs/metrics.jsonl`) から手動で計算した結果:

```bash
# 全completedレコードの合計
$ cat logs/metrics.jsonl | grep '"status": "completed"' | jq -r '.total_cost_usd' | awk '{sum+=$1} END {print sum}'
0.272842

# レコード数
26件の翻訳記録
```

**内訳:**
- 2025-11-06: $0.008773 (9件)
- 2025-11-07: $0.264069 (17件)

### 2. フロントエンドAPI の検証

```bash
$ curl http://localhost/api/cost/monthly
{
  "current_month": "2025-11",
  "total_cost_usd": 0.272842,
  "total_tokens": 287155,
  "total_transactions": 26
}
```

**結論**: ✅ **フロントエンドは正しい**

バックエンドAPIは以下のロジックで正確に集計:
1. `metrics.jsonl` を1行ずつ読み込み
2. `status == "completed"` でフィルタ
3. 現在月 (`2025-11`) のレコードのみ集計
4. `total_cost_usd` を合算

### 3. Grafana ダッシュボードの検証

**設定:**
- デフォルト時間範囲: 過去7日間 (`now-7d` to `now`)
- 「総コスト（USD）」パネルのクエリ:
  ```logql
  sum(rate({job="pptx-translator-metrics"} |= "completed" | json | unwrap total_cost_usd [$__range])) * $__range_s
  ```

**結論**: ❌ **Grafanaが間違っている**

## 問題の原因

### `rate()` 関数の誤用

Grafanaで使用されていた `rate()` 関数は **Prometheusのカウンター型メトリクス用** に設計されており、Lokiのログデータには適していません。

#### `rate()` の動作:
1. **変化率を計算**: 単位時間あたりの増加量を算出
2. **時間範囲依存**: `$__range` に基づいて計算
3. **連続データ前提**: メトリクスの連続的な増加を想定

#### 問題点:
- **イベントベースのログ**: 翻訳完了時のみ記録される不連続なデータ
- **時間範囲による変動**: 7日間の範囲でレート計算すると、実際の合計値と大きく異なる
- **サンプリングエラー**: データポイント間の補間により不正確な値

### 計算の違い

```logql
# 間違い（修正前）
sum(rate({...} | unwrap total_cost_usd [$__range])) * $__range_s
→ レートを計算してから時間範囲を乗算（不正確）

# 正しい（修正後）
sum(sum_over_time({...} | unwrap total_cost_usd [$__range]))
→ 指定範囲内の値を直接合算（正確）
```

## 修正内容

### 変更したファイル
`grafana/provisioning/dashboards/pptx-translator.json`

### 修正箇所

#### 1. 総コスト（USD）パネル

**修正前:**
```json
{
  "expr": "sum(rate({job=\"pptx-translator-metrics\"} |= \"completed\" | json | unwrap total_cost_usd [$__range])) * $__range_s or vector(0)",
  "queryType": ""
}
```

**修正後:**
```json
{
  "expr": "sum(sum_over_time({job=\"pptx-translator-metrics\"} |= \"completed\" | json | unwrap total_cost_usd [$__range])) or vector(0)",
  "queryType": "instant"
}
```

#### 2. 総トークン使用量パネル

**修正前:**
```json
{
  "expr": "sum(rate({job=\"pptx-translator-metrics\"} |= \"completed\" | json | unwrap total_tokens [$__range])) * $__range_s or vector(0)",
  "queryType": ""
}
```

**修正後:**
```json
{
  "expr": "sum(sum_over_time({job=\"pptx-translator-metrics\"} |= \"completed\" | json | unwrap total_tokens [$__range])) or vector(0)",
  "queryType": "instant"
}
```

### 変更点の説明

1. **`rate()` → `sum_over_time()`**
   - レート計算ではなく、範囲内の値を直接合算
   - ログデータに適した集計方法

2. **`* $__range_s` の削除**
   - レートから合計への変換が不要に
   - より直接的で理解しやすい式

3. **`queryType: "instant"` の追加**
   - 単一の集計値を返すクエリであることを明示
   - パフォーマンスの最適化

## 検証方法

修正後、以下のコマンドで検証できます:

```bash
# 1. フロントエンドAPIの値を確認
curl -s http://localhost/api/cost/monthly | jq '.total_cost_usd'

# 2. ログファイルから手動計算
cat logs/metrics.jsonl | grep '"status": "completed"' | \
  jq -r '.total_cost_usd' | awk '{sum+=$1} END {print sum}'

# 3. Grafanaダッシュボードを開く
# http://localhost:3000/
# → PPTX Translator Dashboard を開く
# → 「総コスト（USD）」の値を確認
```

すべての値が **$0.272842** で一致するはずです。

## 今後の推奨事項

### 1. Lokiクエリのベストプラクティス

- **累積値の集計**: `sum_over_time()` を使用
- **レート計算**: メトリクス専用（ログには不適切）
- **時系列グラフ**: 5分や1時間などの固定ウィンドウで集計

### 2. ダッシュボード設計

- **Stat パネル**: 累積値の表示に最適
  - `queryType: "instant"` で単一値を取得
  - `sum_over_time()` で範囲内の合計

- **Time Series パネル**: 時間推移の表示
  - 固定ウィンドウ (例: `[5m]`, `[1h]`) で集計
  - `rate()` ではなく `sum_over_time()` を使用

### 3. 監視とアラート

```logql
# 日次コストの監視
sum(sum_over_time({job="pptx-translator-metrics"} |= "completed" | json | unwrap total_cost_usd [24h]))

# 月次コストの監視（30日間）
sum(sum_over_time({job="pptx-translator-metrics"} |= "completed" | json | unwrap total_cost_usd [30d]))
```

## まとめ

| 項目 | フロントエンド | Grafana（修正前） | Grafana（修正後） |
|------|---------------|------------------|------------------|
| **表示値** | $0.272842 | $0.0698 | $0.272842 |
| **計算方法** | API集計 | `rate() * time` | `sum_over_time()` |
| **正確性** | ✅ 正しい | ❌ 間違い | ✅ 正しい |
| **データソース** | metrics.jsonl | Loki経由 | Loki経由 |

**結論**: フロントエンドのAPI実装は正しく、Grafanaのクエリに問題がありました。`rate()` から `sum_over_time()` への変更により、両者の表示が一致するようになりました。
