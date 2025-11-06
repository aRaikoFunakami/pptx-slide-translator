#!/usr/bin/env python3
"""
現在の時刻で累積メトリクスエントリを作成
"""
import json
from datetime import datetime

# 既存データから最終的な累積値を計算
final_cumulative_tokens = 24235
final_cumulative_cost_usd = 0.004093
final_cumulative_requests = 4

# 現在時刻での累積メトリクスエントリ
current_time = datetime.now().isoformat()
cumulative_entry = {
    "timestamp": current_time,
    "event_type": "cumulative_metrics",
    "cumulative_total_tokens": final_cumulative_tokens,
    "cumulative_cost_usd": final_cumulative_cost_usd,
    "cumulative_requests": final_cumulative_requests
}

# メトリクスファイルに追加
metrics_file = "/Users/raiko.funakami/GitHub/pptx-slide-translator/logs/metrics.jsonl"
with open(metrics_file, 'a', encoding='utf-8') as f:
    f.write(json.dumps(cumulative_entry, ensure_ascii=False) + '\n')

print(f"Added current cumulative entry: {cumulative_entry}")