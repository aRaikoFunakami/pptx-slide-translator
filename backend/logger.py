"""
ログとメトリクス管理
"""
import json
import os
import logging
import time
from datetime import datetime, timezone
from typing import Optional
from pathlib import Path


class MetricsLogger:
    def __init__(self, log_dir: str = "/app/logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # アプリケーションログの設定
        self.app_logger = logging.getLogger("app")
        self.app_logger.setLevel(logging.INFO)
        
        # ファイルハンドラーの設定
        app_handler = logging.FileHandler(self.log_dir / "app.log", encoding='utf-8')
        # ISO8601 UTC (Z) 形式へ統一。例: 2025-11-10T01:51:40.644Z
        # logging の %(asctime)s はミリ秒3桁までしか扱わないため、Formatter を拡張し converter= time.gmtime を利用。
        # ミリ秒精度: %(msecs)d を組み合わせてフォーマット再構成。
        class ISO8601UTCFormatter(logging.Formatter):
            converter = time.gmtime
            def formatTime(self, record, datefmt=None):
                # record.created は epoch 秒(float)。UTC に変換しミリ秒3桁を付与。
                dt = datetime.fromtimestamp(record.created, tz=timezone.utc)
                return dt.strftime('%Y-%m-%dT%H:%M:%S') + f'.{int(record.msecs):03d}Z'

        app_formatter = ISO8601UTCFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        app_handler.setFormatter(app_formatter)
        self.app_logger.addHandler(app_handler)
        
        # メトリクスログの設定
        self.metrics_logger = logging.getLogger("metrics")
        self.metrics_logger.setLevel(logging.INFO)
        
        metrics_handler = logging.FileHandler(self.log_dir / "metrics.jsonl", encoding='utf-8')
        metrics_formatter = logging.Formatter('%(message)s')
        metrics_handler.setFormatter(metrics_formatter)
        self.metrics_logger.addHandler(metrics_handler)
    
    def log_app(self, level: str, message: str):
        """アプリケーションログ"""
        if level.lower() == "info":
            self.app_logger.info(message)
        elif level.lower() == "error":
            self.app_logger.error(message)
        elif level.lower() == "warning":
            self.app_logger.warning(message)
        else:
            self.app_logger.info(message)
    
    def log_metrics(self, 
                   ip_address: str,
                   filename: str,
                   pages: int,
                   text_count: int,
                   target_lang: str,
                   status: str,
                   processing_time: Optional[float] = None,
                   error_message: Optional[str] = None,
                   file_size: Optional[int] = None,
                   input_tokens: Optional[int] = None,
                   output_tokens: Optional[int] = None,
                   total_tokens: Optional[int] = None,
                   total_cost_usd: Optional[float] = None,
                   model_name: Optional[str] = None):
        """メトリクスログ（JSON Lines形式）"""
        metrics_data = {
            "timestamp": datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
            "ip_address": ip_address,
            "filename": filename,
            "pages": pages,
            "text_count": text_count,
            "target_lang": target_lang,
            "status": status,
            "processing_time": processing_time,
            "file_size": file_size,
            "error_message": error_message,
            # Token usage and cost information
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "total_cost_usd": total_cost_usd,
            "model_name": model_name
        }
        
        self.metrics_logger.info(json.dumps(metrics_data, ensure_ascii=False))
    
    def log_queue_status(self, queue_size: int, processing_count: int):
        """キューの状態ログ"""
        queue_data = {
            "timestamp": datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
            "event_type": "queue_status",
            "queue_size": queue_size,
            "processing_count": processing_count
        }
        
        self.metrics_logger.info(json.dumps(queue_data, ensure_ascii=False))


# グローバルインスタンス
metrics_logger = MetricsLogger()