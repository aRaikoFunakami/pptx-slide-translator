#!/usr/bin/env python3
"""
コスト集計スクリプト
logs/metrics.jsonl からコストデータを読み取り、日次・週次・月次の集計を出力します。
"""

import json
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple


class CostSummaryReporter:
    """コスト集計レポーター"""
    
    def __init__(self, metrics_file: str = "logs/metrics.jsonl"):
        """
        初期化
        
        Args:
            metrics_file: メトリクスファイルのパス
        """
        self.metrics_file = Path(metrics_file)
        
    def parse_metrics(self) -> List[Dict]:
        """
        メトリクスファイルをパースして翻訳記録を取得
        
        Returns:
            翻訳記録のリスト
        """
        records = []
        
        if not self.metrics_file.exists():
            print(f"⚠️  メトリクスファイルが見つかりません: {self.metrics_file}")
            return records
        
        with open(self.metrics_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                    
                try:
                    data = json.loads(line)
                    # completedステータスのみを集計対象とする
                    if data.get('status') == 'completed':
                        records.append(data)
                except json.JSONDecodeError as e:
                    print(f"⚠️  JSON解析エラー: {e}")
                    continue
        
        return records
    
    def aggregate_by_period(self, records: List[Dict]) -> Dict[str, Dict]:
        """
        期間別にコストを集計
        
        Args:
            records: 翻訳記録のリスト
            
        Returns:
            期間別集計データ {period_type: {period_key: {cost, tokens, count}}}
        """
        daily = defaultdict(lambda: {'cost': 0.0, 'tokens': 0, 'count': 0})
        weekly = defaultdict(lambda: {'cost': 0.0, 'tokens': 0, 'count': 0})
        monthly = defaultdict(lambda: {'cost': 0.0, 'tokens': 0, 'count': 0})
        
        for record in records:
            timestamp_str = record.get('timestamp', '')
            cost = record.get('total_cost_usd', 0.0)
            tokens = record.get('total_tokens', 0)
            
            try:
                # ISO8601形式のタイムスタンプをパース
                dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                
                # 日次集計 (YYYY-MM-DD)
                day_key = dt.strftime('%Y-%m-%d')
                daily[day_key]['cost'] += cost
                daily[day_key]['tokens'] += tokens
                daily[day_key]['count'] += 1
                
                # 週次集計 (YYYY-Www: ISO週番号)
                week_key = dt.strftime('%Y-W%W')
                weekly[week_key]['cost'] += cost
                weekly[week_key]['tokens'] += tokens
                weekly[week_key]['count'] += 1
                
                # 月次集計 (YYYY-MM)
                month_key = dt.strftime('%Y-%m')
                monthly[month_key]['cost'] += cost
                monthly[month_key]['tokens'] += tokens
                monthly[month_key]['count'] += 1
                
            except (ValueError, AttributeError) as e:
                print(f"⚠️  タイムスタンプ解析エラー: {timestamp_str} - {e}")
                continue
        
        return {
            'daily': dict(daily),
            'weekly': dict(weekly),
            'monthly': dict(monthly)
        }
    
    def format_summary_table(self, data: Dict[str, Dict], title: str) -> str:
        """
        集計データをテーブル形式にフォーマット
        
        Args:
            data: 集計データ {period: {cost, tokens, count}}
            title: テーブルタイトル
            
        Returns:
            フォーマットされた文字列
        """
        if not data:
            return f"\n{title}\n{'=' * 70}\n(データなし)\n"
        
        lines = [
            f"\n{title}",
            "=" * 70,
            f"{'期間':<20} {'費用 (USD)':<15} {'トークン数':<15} {'翻訳回数':<10}",
            "-" * 70
        ]
        
        # 期間でソート
        sorted_periods = sorted(data.keys(), reverse=True)
        
        total_cost = 0.0
        total_tokens = 0
        total_count = 0
        
        for period in sorted_periods:
            info = data[period]
            cost = info['cost']
            tokens = info['tokens']
            count = info['count']
            
            total_cost += cost
            total_tokens += tokens
            total_count += count
            
            lines.append(
                f"{period:<20} ${cost:<14.6f} {tokens:<15,} {count:<10,}"
            )
        
        lines.extend([
            "-" * 70,
            f"{'合計':<20} ${total_cost:<14.6f} {total_tokens:<15,} {total_count:<10,}",
            "=" * 70
        ])
        
        return "\n".join(lines)
    
    def generate_report(self, period_type: str = 'all') -> str:
        """
        コスト集計レポートを生成
        
        Args:
            period_type: 'daily', 'weekly', 'monthly', 'all'
            
        Returns:
            レポート文字列
        """
        records = self.parse_metrics()
        
        if not records:
            return "📊 コスト集計レポート\n" + "=" * 70 + "\n\n翻訳記録が見つかりませんでした。\n"
        
        aggregated = self.aggregate_by_period(records)
        
        report_parts = [
            "📊 コスト集計レポート",
            "=" * 70,
            f"生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"データソース: {self.metrics_file}",
            f"総レコード数: {len(records)}",
            ""
        ]
        
        if period_type in ['daily', 'all']:
            report_parts.append(self.format_summary_table(
                aggregated['daily'], 
                "📅 日次コスト集計"
            ))
        
        if period_type in ['weekly', 'all']:
            report_parts.append(self.format_summary_table(
                aggregated['weekly'], 
                "📆 週次コスト集計"
            ))
        
        if period_type in ['monthly', 'all']:
            report_parts.append(self.format_summary_table(
                aggregated['monthly'], 
                "📈 月次コスト集計"
            ))
        
        # 直近7日間のサマリー
        recent_summary = self._get_recent_summary(aggregated['daily'])
        if recent_summary:
            report_parts.append(recent_summary)
        
        return "\n".join(report_parts)
    
    def _get_recent_summary(self, daily_data: Dict[str, Dict]) -> str:
        """
        直近7日間のサマリーを生成
        
        Args:
            daily_data: 日次集計データ
            
        Returns:
            サマリー文字列
        """
        if not daily_data:
            return ""
        
        today = datetime.now().date()
        recent_days = [(today - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(7)]
        
        total_cost = 0.0
        total_tokens = 0
        total_count = 0
        days_with_data = 0
        
        for day in recent_days:
            if day in daily_data:
                total_cost += daily_data[day]['cost']
                total_tokens += daily_data[day]['tokens']
                total_count += daily_data[day]['count']
                days_with_data += 1
        
        if days_with_data == 0:
            return ""
        
        avg_cost = total_cost / days_with_data if days_with_data > 0 else 0
        
        lines = [
            "\n🔍 直近7日間のサマリー",
            "=" * 70,
            f"期間: {recent_days[-1]} ～ {recent_days[0]}",
            f"総費用: ${total_cost:.6f}",
            f"総トークン数: {total_tokens:,}",
            f"総翻訳回数: {total_count:,}",
            f"アクティブ日数: {days_with_data} 日",
            f"1日あたり平均費用: ${avg_cost:.6f}",
            "=" * 70
        ]
        
        return "\n".join(lines)
    
    def export_to_file(self, report: str, output_file: str = None) -> str:
        """
        レポートをファイルに出力
        
        Args:
            report: レポート文字列
            output_file: 出力ファイル名（Noneの場合は自動生成）
            
        Returns:
            出力ファイルパス
        """
        if output_file is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"logs/cost_summary_{timestamp}.txt"
        
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        return str(output_path)


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(
        description='PPTX翻訳サービスのコスト集計レポート生成',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  # 全期間の集計を表示
  python scripts/cost_summary.py
  
  # 日次集計のみ表示
  python scripts/cost_summary.py --period daily
  
  # 週次集計のみ表示
  python scripts/cost_summary.py --period weekly
  
  # 月次集計のみ表示
  python scripts/cost_summary.py --period monthly
  
  # ファイルに出力
  python scripts/cost_summary.py --output logs/report.txt
  
  # カスタムメトリクスファイルを指定
  python scripts/cost_summary.py --metrics-file path/to/metrics.jsonl
        """
    )
    
    parser.add_argument(
        '--period',
        choices=['daily', 'weekly', 'monthly', 'all'],
        default='all',
        help='集計期間タイプ (デフォルト: all)'
    )
    
    parser.add_argument(
        '--metrics-file',
        default='logs/metrics.jsonl',
        help='メトリクスファイルのパス (デフォルト: logs/metrics.jsonl)'
    )
    
    parser.add_argument(
        '--output',
        help='レポートを出力するファイルパス（指定しない場合は標準出力）'
    )
    
    args = parser.parse_args()
    
    # レポート生成
    reporter = CostSummaryReporter(metrics_file=args.metrics_file)
    report = reporter.generate_report(period_type=args.period)
    
    # 出力
    if args.output:
        output_path = reporter.export_to_file(report, args.output)
        print(f"✅ レポートを出力しました: {output_path}")
        print("\n" + "=" * 70)
        print(report)
    else:
        print(report)


if __name__ == '__main__':
    main()
