"""
FastAPI PPTXファイル翻訳Webサービス
"""
import asyncio
import os
import tempfile
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import aiofiles
from fastapi import FastAPI, File, UploadFile, HTTPException, Request, Form
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.translator import translate_pptx_async, analyze_pptx
from backend.logger import metrics_logger


# データモデル
class QueueStatus(BaseModel):
    queue_position: int
    total_in_queue: int
    is_processing: bool


class TranslationJob(BaseModel):
    job_id: str
    filename: str
    target_lang: str
    status: str  # "queued", "processing", "completed", "failed"
    pages: Optional[int] = None
    text_count: Optional[int] = None
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None


class TranslationRequest(BaseModel):
    job_id: str
    file_path: str
    output_path: str
    filename: str
    target_lang: str
    ip_address: str
    file_size: int
    pages: int
    text_count: int


# アプリケーション初期化
app = FastAPI(
    title="PPTX翻訳サービス",
    description="PowerPointファイルを翻訳するWebサービス",
    version="1.0.0"
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静的ファイルの設定（React build結果を配信）
if os.path.exists("/app/frontend/build"):
    app.mount("/static", StaticFiles(directory="/app/frontend/build/static"), name="static")

# グローバル変数
translation_queue: asyncio.Queue = asyncio.Queue()
active_jobs: dict = {}
processing_count = 0
MAX_CONCURRENT_TRANSLATIONS = int(os.getenv("MAX_CONCURRENT_TRANSLATIONS", "1"))
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB

# OpenAI APIキーのチェック
if not os.getenv("OPENAI_API_KEY"):
    metrics_logger.log_app("error", "OPENAI_API_KEYが設定されていません")
    raise RuntimeError("OPENAI_API_KEYが設定されていません")


def get_client_ip(request: Request) -> str:
    """クライアントIPアドレスを取得"""
    # X-Forwarded-Forヘッダーをチェック（プロキシ経由の場合）
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    
    # X-Real-IPヘッダーをチェック
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # 直接接続の場合
    return request.client.host if request.client else "unknown"


async def process_translation_queue():
    """翻訳キューを処理するバックグラウンドタスク"""
    global processing_count
    
    while True:
        try:
            # キューから次のジョブを取得
            translation_request: TranslationRequest = await translation_queue.get()
            
            if processing_count >= MAX_CONCURRENT_TRANSLATIONS:
                # 最大同時実行数に達している場合は再度キューに戻す
                await translation_queue.put(translation_request)
                await asyncio.sleep(1)
                continue
            
            processing_count += 1
            job_id = translation_request.job_id
            
            try:
                # ジョブステータスを処理中に更新
                if job_id in active_jobs:
                    active_jobs[job_id].status = "processing"
                
                metrics_logger.log_app("info", f"翻訳処理開始: {job_id}")
                start_time = time.time()
                
                # 翻訳実行
                pages, text_count, token_metrics = await translate_pptx_async(
                    translation_request.file_path,
                    translation_request.output_path,
                    translation_request.target_lang
                )
                
                processing_time = time.time() - start_time
                
                # ジョブステータスを完了に更新
                if job_id in active_jobs:
                    active_jobs[job_id].status = "completed"
                    active_jobs[job_id].completed_at = datetime.now()
                
                # メトリクスログ（トークン情報を含む）
                metrics_logger.log_metrics(
                    ip_address=translation_request.ip_address,
                    filename=translation_request.filename,
                    pages=pages,
                    text_count=text_count,
                    target_lang=translation_request.target_lang,
                    status="completed",
                    processing_time=processing_time,
                    file_size=translation_request.file_size,
                    input_tokens=token_metrics.get("input_tokens"),
                    output_tokens=token_metrics.get("output_tokens"),
                    total_tokens=token_metrics.get("total_tokens"),
                    total_cost_usd=token_metrics.get("total_cost_usd"),
                    model_name=token_metrics.get("model")
                )
                
                metrics_logger.log_app("info", 
                    f"翻訳処理完了: {job_id}, {pages}ページ, {text_count}テキスト, {processing_time:.2f}秒, "
                    f"トークン: {token_metrics.get('total_tokens', 0)}, 費用: ${token_metrics.get('total_cost_usd', 0.0):.4f}")
                
            except Exception as e:
                error_message = f"翻訳処理中にエラーが発生しました: {str(e)}"
                
                # ジョブステータスを失敗に更新
                if job_id in active_jobs:
                    active_jobs[job_id].status = "failed"
                    active_jobs[job_id].error_message = error_message
                    active_jobs[job_id].completed_at = datetime.now()
                
                # エラーメトリクス（トークン情報は0で記録）
                metrics_logger.log_metrics(
                    ip_address=translation_request.ip_address,
                    filename=translation_request.filename,
                    pages=translation_request.pages,
                    text_count=translation_request.text_count,
                    target_lang=translation_request.target_lang,
                    status="failed",
                    error_message=error_message,
                    file_size=translation_request.file_size,
                    input_tokens=0,
                    output_tokens=0,
                    total_tokens=0,
                    total_cost_usd=0.0,
                    model_name=None
                )
                
                metrics_logger.log_app("error", f"翻訳処理エラー: {job_id}, {error_message}")
                
                # 一時ファイルをクリーンアップ
                try:
                    if os.path.exists(translation_request.file_path):
                        os.remove(translation_request.file_path)
                except:
                    pass
                
            finally:
                processing_count -= 1
                
                # キューの状態をログ
                metrics_logger.log_queue_status(translation_queue.qsize(), processing_count)
                
        except Exception as e:
            metrics_logger.log_app("error", f"キュー処理でエラー: {str(e)}")
            await asyncio.sleep(1)


@app.on_event("startup")
async def startup_event():
    """アプリケーション起動時の処理"""
    metrics_logger.log_app("info", "PPTXトランスレーションサービス開始")
    
    # バックグラウンドタスクを開始
    asyncio.create_task(process_translation_queue())


@app.get("/")
async def read_root():
    """フロントエンドのindex.htmlを配信"""
    if os.path.exists("/app/frontend/build/index.html"):
        return FileResponse("/app/frontend/build/index.html")
    else:
        return {"message": "PPTX翻訳サービス"}


@app.post("/api/upload")
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    target_lang: str = Form(...)
):
    """ファイルアップロードとジョブ作成"""
    
    client_ip = get_client_ip(request)
    
    # ファイルサイズチェック
    if file.size and file.size > MAX_FILE_SIZE:
        error_msg = f"ファイルサイズが大きすぎます（最大500MB）: {file.size / 1024 / 1024:.1f}MB"
        metrics_logger.log_app("warning", f"ファイルサイズエラー: {client_ip}, {file.filename}, {file.size}")
        raise HTTPException(status_code=413, detail=error_msg)
    
    # ファイル形式チェック
    if not file.filename.lower().endswith('.pptx'):
        error_msg = "PPTXファイルのみアップロード可能です"
        metrics_logger.log_app("warning", f"ファイル形式エラー: {client_ip}, {file.filename}")
        raise HTTPException(status_code=400, detail=error_msg)
    
    # 言語チェック
    if target_lang not in ["ja", "en"]:
        error_msg = "対応していない言語です（ja, enのみ）"
        raise HTTPException(status_code=400, detail=error_msg)
    
    job_id = str(uuid.uuid4())
    
    try:
        # 一時ファイルに保存
        temp_dir = tempfile.mkdtemp()
        input_path = os.path.join(temp_dir, f"input_{job_id}.pptx")
        output_path = os.path.join(temp_dir, f"output_{job_id}.pptx")
        
        async with aiofiles.open(input_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        file_size = len(content)
        
        # ファイル分析
        analysis = analyze_pptx(input_path)
        if not analysis["success"]:
            error_msg = f"PPTXファイルの分析に失敗しました: {analysis['error']}"
            metrics_logger.log_app("error", f"ファイル分析エラー: {client_ip}, {file.filename}, {analysis['error']}")
            raise HTTPException(status_code=400, detail=error_msg)
        
        # ジョブを作成
        job = TranslationJob(
            job_id=job_id,
            filename=file.filename,
            target_lang=target_lang,
            status="queued",
            pages=analysis["pages"],
            text_count=analysis["text_count"],
            created_at=datetime.now()
        )
        
        active_jobs[job_id] = job
        
        # 翻訳リクエストをキューに追加
        translation_request = TranslationRequest(
            job_id=job_id,
            file_path=input_path,
            output_path=output_path,
            filename=file.filename,
            target_lang=target_lang,
            ip_address=client_ip,
            file_size=file_size,
            pages=analysis["pages"],
            text_count=analysis["text_count"]
        )
        
        await translation_queue.put(translation_request)
        
        metrics_logger.log_app("info", 
            f"ファイルアップロード: {client_ip}, {file.filename}, {analysis['pages']}ページ, {analysis['text_count']}テキスト")
        
        return {
            "job_id": job_id,
            "filename": file.filename,
            "pages": analysis["pages"],
            "text_count": analysis["text_count"],
            "target_lang": target_lang,
            "queue_position": translation_queue.qsize()
        }
        
    except HTTPException:
        # クリーンアップ
        try:
            if 'input_path' in locals() and os.path.exists(input_path):
                os.remove(input_path)
        except:
            pass
        raise
    except Exception as e:
        # クリーンアップ
        try:
            if 'input_path' in locals() and os.path.exists(input_path):
                os.remove(input_path)
        except:
            pass
        
        error_msg = f"アップロード処理中にエラーが発生しました: {str(e)}"
        metrics_logger.log_app("error", f"アップロードエラー: {client_ip}, {file.filename}, {str(e)}")
        raise HTTPException(status_code=500, detail=error_msg)


@app.get("/api/status/{job_id}")
async def get_job_status(job_id: str):
    """ジョブのステータスを取得"""
    
    if job_id not in active_jobs:
        raise HTTPException(status_code=404, detail="ジョブが見つかりません")
    
    job = active_jobs[job_id]
    
    # キューでの位置を計算
    queue_position = 0
    if job.status == "queued":
        # 簡易的な位置計算（実際のキューの順序は考慮せず）
        queue_position = translation_queue.qsize()
    
    return {
        "job_id": job_id,
        "status": job.status,
        "filename": job.filename,
        "pages": job.pages,
        "text_count": job.text_count,
        "target_lang": job.target_lang,
        "queue_position": queue_position,
        "total_in_queue": translation_queue.qsize(),
        "error_message": job.error_message,
        "created_at": job.created_at,
        "completed_at": job.completed_at
    }


@app.get("/api/download/{job_id}")
async def download_result(job_id: str, request: Request):
    """翻訳結果をダウンロード"""
    
    client_ip = get_client_ip(request)
    
    if job_id not in active_jobs:
        raise HTTPException(status_code=404, detail="ジョブが見つかりません")
    
    job = active_jobs[job_id]
    
    if job.status != "completed":
        raise HTTPException(status_code=400, detail="翻訳がまだ完了していません")
    
    # 出力ファイルパスを推定
    temp_dir = tempfile.gettempdir()
    output_path = None
    
    # temp_dirから該当するファイルを検索
    for temp_subdir in os.listdir(temp_dir):
        potential_path = os.path.join(temp_dir, temp_subdir, f"output_{job_id}.pptx")
        if os.path.exists(potential_path):
            output_path = potential_path
            break
    
    if not output_path or not os.path.exists(output_path):
        raise HTTPException(status_code=404, detail="翻訳済みファイルが見つかりません")
    
    # ファイル名を生成
    base_name = os.path.splitext(job.filename)[0]
    lang_suffix = "ja" if job.target_lang == "ja" else "en"
    download_filename = f"{base_name}_{lang_suffix}.pptx"
    
    metrics_logger.log_app("info", f"ファイルダウンロード: {client_ip}, {job.filename}, {download_filename}")
    
    def cleanup_files():
        """ファイル送信後のクリーンアップ"""
        try:
            # 入力ファイルと出力ファイルを削除
            temp_subdir = os.path.dirname(output_path)
            if os.path.exists(temp_subdir):
                import shutil
                shutil.rmtree(temp_subdir)
            
            # ジョブ情報も削除
            if job_id in active_jobs:
                del active_jobs[job_id]
                
            metrics_logger.log_app("info", f"ファイルクリーンアップ完了: {job_id}")
        except Exception as e:
            metrics_logger.log_app("error", f"クリーンアップエラー: {job_id}, {str(e)}")
    
    # ファイル送信後にクリーンアップを実行
    import threading
    threading.Timer(1.0, cleanup_files).start()
    
    return FileResponse(
        output_path,
        filename=download_filename,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation"
    )


@app.get("/api/queue")
async def get_queue_status():
    """現在のキューの状態を取得"""
    
    queued_jobs = [job for job in active_jobs.values() if job.status == "queued"]
    processing_jobs = [job for job in active_jobs.values() if job.status == "processing"]
    
    return {
        "queue_size": len(queued_jobs),
        "processing_count": len(processing_jobs),
        "max_concurrent": MAX_CONCURRENT_TRANSLATIONS,
        "queued_jobs": [
            {
                "job_id": job.job_id,
                "filename": job.filename,
                "created_at": job.created_at
            } for job in sorted(queued_jobs, key=lambda x: x.created_at)
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)