import React, { useState, useCallback } from 'react';
import { FileInfo, JobStatus, TargetLang } from './types';
import { translationApi } from './services/api';
import { useMonthlyCost, useFileSelection, useJobStatusPolling } from './hooks';
import {
  MonthlyCostCard,
  FileUploadArea,
  FileInfoDisplay,
  JobStatusDisplay,
} from './components';

const App: React.FC = () => {
  const [fileInfo, setFileInfo] = useState<FileInfo | null>(null);
  const [targetLang, setTargetLang] = useState<TargetLang>('en');
  const [jobId, setJobId] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isDragOver, setIsDragOver] = useState(false);

  // カスタムフック
  const { monthlyCost, fetchMonthlyCost } = useMonthlyCost();
  const { file, error, fileInputRef, handleFileSelect, resetFile, setError } =
    useFileSelection();

  // ジョブステータスの監視
  const jobStatus = useJobStatusPolling(jobId, fetchMonthlyCost);

  // ファイルアップロード処理
  const handleUpload = useCallback(async () => {
    if (!file) return;

    setIsUploading(true);
    setError(null);

    try {
      const result = await translationApi.uploadFile(file, targetLang);

      setJobId(result.job_id);
      setFileInfo({
        name: result.filename,
        pages: result.pages,
        textCount: result.text_count,
      });
    } catch (error) {
      setError(
        error instanceof Error ? error.message : 'アップロードエラーが発生しました'
      );
    } finally {
      setIsUploading(false);
    }
  }, [file, targetLang, setError]);

  // リセット処理
  const handleReset = useCallback(() => {
    resetFile();
    setFileInfo(null);
    setJobId(null);
    setError(null);
  }, [resetFile, setError]);

  // ダウンロード処理
  const handleDownload = useCallback(async () => {
    if (!jobId || !jobStatus || jobStatus.status !== 'completed') return;

    try {
      const blob = await translationApi.downloadFile(jobId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;

      // ファイル名を生成
      const baseName = jobStatus.filename.replace(/\.pptx$/i, '');
      const langSuffix = jobStatus.target_lang === 'ja' ? 'ja' : 'en';
      a.download = `${baseName}_${langSuffix}.pptx`;

      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);

      // 月次コストを再取得
      await fetchMonthlyCost();

      // ダウンロード後にリセット
      handleReset();
    } catch (error) {
      setError('ダウンロードエラーが発生しました');
    }
  }, [jobId, jobStatus, fetchMonthlyCost, handleReset, setError]);

  // ドラッグ&ドロップハンドラー
  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragOver(false);
      const files = Array.from(e.dataTransfer.files);
      if (files.length > 0) {
        handleFileSelect(files[0]);
      }
    },
    [handleFileSelect]
  );

  return (
    <div className="app">
      <div className="container">
        <div className="header">
          <h1 className="title">PPTX翻訳サービス</h1>
          <p className="subtitle">
            PowerPointファイルを高品質に翻訳します
            <br />
            ファイルは翻訳後に自動削除され、プライバシーを保護します
          </p>
        </div>

        {/* 月次コスト表示 */}
        {monthlyCost && <MonthlyCostCard monthlyCost={monthlyCost} />}

        {!jobStatus ? (
          <>
            {/* ファイルアップロードエリア */}
            <div
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
            >
              <FileUploadArea
                isDragOver={isDragOver}
                fileInputRef={fileInputRef}
                onFileSelect={handleFileSelect}
              />
            </div>

            {/* ファイル情報表示 */}
            {file && <FileInfoDisplay file={file} fileInfo={fileInfo} />}

            {/* 言語選択 */}
            {file && (
              <div className="form-group">
                <label className="label">翻訳先言語</label>
                <select
                  className="select"
                  value={targetLang}
                  onChange={(e) => setTargetLang(e.target.value as TargetLang)}
                >
                  <option value="en">英語</option>
                  <option value="ja">日本語</option>
                </select>
              </div>
            )}

            {/* 警告メッセージ */}
            {file && (
              <div className="warning">
                ⚠️
                アップロードしたファイルは翻訳完了後に即座にサーバーから削除されます
              </div>
            )}

            {/* エラー表示 */}
            {error && (
              <div className="error">
                <h4>エラー</h4>
                <p>{error}</p>
              </div>
            )}

            {/* アップロードボタン */}
            <button
              className="button button-primary"
              onClick={handleUpload}
              disabled={!file || isUploading}
            >
              {isUploading ? '翻訳を開始しています...' : '翻訳を開始'}
            </button>
          </>
        ) : (
          <JobStatusDisplay
            jobStatus={jobStatus}
            onDownload={handleDownload}
            onReset={handleReset}
          />
        )}
      </div>
    </div>
  );
};

export default App;
