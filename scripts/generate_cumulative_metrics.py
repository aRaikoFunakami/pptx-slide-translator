#!/usr/bin/env python3
"""
既存のメトリクスログから累積データを生成するスクリプト
"""
import json
import sys
from datetime import datetime
from pathlib import Path

def process_metrics_log(input_file, output_file):
    """既存のメトリクスログから累積データを生成"""
    
    cumulative_tokens = 0
    cumulative_cost_usd = 0.0
    cumulative_requests = 0
    
    # 出力用のデータを格納
    output_lines = []
    
    print(f"Processing {input_file}...")
    
    # 既存のログを読み込み
    with open(input_file, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
                
            try:
                data = json.loads(line)
                
                # 既存の行をそのまま追加
                output_lines.append(line)
                
                # completedステータスでtoken情報があるエントリを処理
                if (data.get('status') == 'completed' and 
                    'total_tokens' in data and 
                    data['total_tokens'] is not None):
                    
                    # 累積値を更新
                    cumulative_tokens += data['total_tokens']
                    cumulative_requests += 1
                    
                    if 'total_cost_usd' in data and data['total_cost_usd'] is not None:
                        cumulative_cost_usd += data['total_cost_usd']
                    
                    # 累積メトリクスエントリを生成
                    cumulative_entry = {
                        "timestamp": data['timestamp'],
                        "event_type": "cumulative_metrics",
                        "cumulative_total_tokens": cumulative_tokens,
                        "cumulative_cost_usd": round(cumulative_cost_usd, 6),
                        "cumulative_requests": cumulative_requests
                    }
                    
                    output_lines.append(json.dumps(cumulative_entry, ensure_ascii=False))
                    
                    print(f"Line {line_num}: Added cumulative entry - "
                          f"Tokens: {cumulative_tokens}, "
                          f"Cost: ${cumulative_cost_usd:.4f}, "
                          f"Requests: {cumulative_requests}")
                    
            except json.JSONDecodeError as e:
                print(f"Warning: Invalid JSON at line {line_num}: {e}")
                continue
    
    # 結果を出力ファイルに書き込み
    with open(output_file, 'w', encoding='utf-8') as f:
        for line in output_lines:
            f.write(line + '\n')
    
    print(f"\nProcessing completed!")
    print(f"Final cumulative values:")
    print(f"  Total Tokens: {cumulative_tokens}")
    print(f"  Total Cost: ${cumulative_cost_usd:.4f}")
    print(f"  Total Requests: {cumulative_requests}")
    print(f"Output written to: {output_file}")

if __name__ == "__main__":
    # デフォルトのパス
    input_file = Path("/Users/raiko.funakami/GitHub/pptx-slide-translator/logs/metrics.jsonl")
    output_file = Path("/Users/raiko.funakami/GitHub/pptx-slide-translator/logs/metrics_with_cumulative.jsonl")
    
    if len(sys.argv) > 1:
        input_file = Path(sys.argv[1])
    if len(sys.argv) > 2:
        output_file = Path(sys.argv[2])
    
    if not input_file.exists():
        print(f"Error: Input file not found: {input_file}")
        sys.exit(1)
    
    process_metrics_log(input_file, output_file)