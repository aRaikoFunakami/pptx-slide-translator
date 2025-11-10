import React, { useState, useCallback, useEffect } from 'react';
import { FileInfo, JobStatus, TargetLang } from './types';
import { translationApi } from './services/api';
import { useMonthlyCost, useFileSelection, useJobStatusPolling } from './hooks';
import {
  MonthlyCostCard,
  FileUploadArea,
  FileInfoDisplay,
  JobStatusDisplay,
} from './components';
import { NoticeDialog } from './components/NoticeDialog';

const App: React.FC = () => {
  const [fileInfo, setFileInfo] = useState<FileInfo | null>(null);
  const [targetLang, setTargetLang] = useState<TargetLang>('en');
  const [jobId, setJobId] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isDragOver, setIsDragOver] = useState(false);
  const [showNotice, setShowNotice] = useState(false);
  const [noticeHtml, setNoticeHtml] = useState<string>('');

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
      // 成功時はisUploadingをfalseに戻さない（画面が切り替わるまでボタンを無効化）
    } catch (error) {
      setError(
        error instanceof Error ? error.message : 'アップロードエラーが発生しました'
      );
      setIsUploading(false); // エラー時のみリセット
    }
  }, [file, targetLang, setError]);

  // リセット処理
  const handleReset = useCallback(() => {
    resetFile();
    setFileInfo(null);
    setJobId(null);
    setError(null);
    setIsUploading(false); // アップロード状態もリセット
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

  // キャンセル処理
  const handleCancel = useCallback(async () => {
    if (!jobId) return;

    try {
      await translationApi.cancelJob(jobId);
      // キャンセル後にリセット
      handleReset();
    } catch (error) {
      setError(
        error instanceof Error ? error.message : 'キャンセルに失敗しました'
      );
    }
  }, [jobId, handleReset, setError]);

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

  // 運用上の注意ダイアログ（1日1回）
  useEffect(() => {
    const enabled = process.env.REACT_APP_NOTICE_ENABLED === 'true';
    const htmlFile = process.env.REACT_APP_NOTICE_HTML || 'static/notice.html';
    const freqDays = parseInt(process.env.REACT_APP_NOTICE_FREQUENCY_DAYS || '1', 10);
    if (!enabled) return;

    const key = 'notice_last_shown';
    const today = new Date();
    const todayStr = today.toISOString().slice(0, 10); // YYYY-MM-DD
    const lastShown = localStorage.getItem(key);

    let shouldShow = false;
    if (!lastShown) {
      shouldShow = true;
    } else {
      // 経過日数を判定
      const lastDate = new Date(lastShown);
      const diffMs = today.getTime() - lastDate.getTime();
      const diffDays = diffMs / (1000 * 60 * 60 * 24);
      if (diffDays >= freqDays) {
        shouldShow = true;
      }
    }

    if (!shouldShow) return;

    fetch(`/${htmlFile}`)
      .then((res) => {
        if (!res.ok) throw new Error('notice html fetch failed');
        return res.text();
      })
      .then((html) => {
        setNoticeHtml(html);
        setShowNotice(true);
        localStorage.setItem(key, todayStr);
      })
      .catch(() => {
        // 失敗時は表示しない（ログ出力はブラウザコンソール）
        console.warn('Notice HTML取得に失敗しました');
      });
  }, []);

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
                翻訳完了後、ダウンロード時に即座に削除されます。未ダウンロードの場合は10分後に自動削除されます
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
            onCancel={handleCancel}
          />
        )}
      </div>
      {showNotice && (
        <NoticeDialog html={noticeHtml} onClose={() => setShowNotice(false)} />
      )}
    </div>
  );
};

export default App;
