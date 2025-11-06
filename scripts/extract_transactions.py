#!/usr/bin/env python3
"""
既存のmetrics.jsonlから完了したトランザクションのみを抽出し、
新しいmetrics.jsonlファイルを生成する。

cumulative_metricsとqueue_statusエントリは除外される。
"""

import json
from datetime import datetime
from pathlib import Path

# ファイルパス
LOGS_DIR = Path(__file__).parent.parent / "logs"
INPUT_FILE = LOGS_DIR / "metrics.jsonl"
OUTPUT_FILE = LOGS_DIR / "metrics_transactions_only.jsonl"
BACKUP_FILE = LOGS_DIR / "metrics_backup.jsonl"

def extract_transactions():
    """完了したトランザクションのみを抽出"""
    
    if not INPUT_FILE.exists():
        print(f"エラー: {INPUT_FILE} が見つかりません")
        return
    
    # バックアップを作成
    print(f"バックアップを作成: {BACKUP_FILE}")
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        with open(BACKUP_FILE, 'w', encoding='utf-8') as backup:
            backup.write(f.read())
    
    # トランザクションを抽出
    transactions = []
    skipped = 0
    
    print(f"\n{INPUT_FILE} を読み込み中...")
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            
            try:
                data = json.loads(line)
                event_type = data.get('event_type', '')
                status = data.get('status', '')
                
                # completedトランザクションのみを保持
                # event_typeがない場合はstatusがcompletedならトランザクション
                if status == 'completed' and event_type != 'cumulative_metrics':
                    transactions.append(data)
                    print(f"  ✓ 行 {line_num}: {data.get('filename', 'N/A')} - "
                          f"{data.get('total_tokens', 0)} tokens, "
                          f"${data.get('total_cost_usd', 0):.6f}")
                else:
                    skipped += 1
                    skip_reason = event_type if event_type else f"status={status}"
                    print(f"  ✗ 行 {line_num}: {skip_reason} (スキップ)")
            
            except json.JSONDecodeError as e:
                print(f"  ⚠ 行 {line_num}: JSON解析エラー - {e}")
                skipped += 1
    
    # 新しいファイルに書き込み
    print(f"\n{OUTPUT_FILE} に書き込み中...")
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        for transaction in transactions:
            f.write(json.dumps(transaction, ensure_ascii=False) + '\n')
    
    # サマリー
    print("\n" + "=" * 60)
    print("抽出完了")
    print("=" * 60)
    print(f"抽出されたトランザクション: {len(transactions)}")
    print(f"スキップされたエントリ: {skipped}")
    
    if transactions:
        total_tokens = sum(t.get('total_tokens', 0) for t in transactions)
        total_cost = sum(t.get('total_cost_usd', 0) for t in transactions)
        print(f"\n合計トークン: {total_tokens}")
        print(f"合計コスト: ${total_cost:.6f}")
    
    print(f"\n出力ファイル: {OUTPUT_FILE}")
    print(f"バックアップ: {BACKUP_FILE}")
    print("\n次のステップ:")
    print(f"  1. {OUTPUT_FILE} の内容を確認")
    print(f"  2. 問題なければ: mv {OUTPUT_FILE} {INPUT_FILE}")
    print(f"  3. Alloyコンテナを再起動: docker compose restart alloy")

if __name__ == "__main__":
    extract_transactions()
