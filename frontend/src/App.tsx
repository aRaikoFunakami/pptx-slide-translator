import React, { useState, useCallback, useRef } from 'react';

interface FileInfo {
  name: string;
  pages: number;
  textCount: number;
}

interface JobStatus {
  job_id: string;
  status: 'queued' | 'processing' | 'completed' | 'failed';
  filename: string;
  pages: number;
  text_count: number;
  target_lang: string;
  queue_position: number;
  total_in_queue: number;
  error_message?: string;
  created_at: string;
  completed_at?: string;
  // トークン情報（completed時のみ）
  input_tokens?: number;
  output_tokens?: number;
  total_tokens?: number;
  total_cost_usd?: number;
  model_name?: string;
  processing_time?: number;
}

interface MonthlyCost {
  current_month: string;
  total_cost_usd: number;
  total_tokens: number;
  total_transactions: number;
}

const App: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [fileInfo, setFileInfo] = useState<FileInfo | null>(null);
  const [targetLang, setTargetLang] = useState<'ja' | 'en'>('en');
  const [jobId, setJobId] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<JobStatus | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const [monthlyCost, setMonthlyCost] = useState<MonthlyCost | null>(null);
  
  const fileInputRef = useRef<HTMLInputElement>(null);
  const statusCheckInterval = useRef<NodeJS.Timeout | null>(null);

  // 月次コスト取得
  const fetchMonthlyCost = useCallback(async () => {
    try {
      const response = await fetch('/api/cost/monthly');
      if (response.ok) {
        const data: MonthlyCost = await response.json();
        setMonthlyCost(data);
      }
    } catch (error) {
      console.error('月次コスト取得エラー:', error);
    }
  }, []);

  // 初回マウント時に月次コストを取得
  React.useEffect(() => {
    fetchMonthlyCost();
  }, [fetchMonthlyCost]);

  const handleFileSelect = useCallback((selectedFile: File) => {
    // ファイル形式チェック
    if (!selectedFile.name.toLowerCase().endsWith('.pptx')) {
      setError('PPTXファイルのみアップロード可能です');
      return;
    }

    // ファイルサイズチェック (500MB)
    if (selectedFile.size > 500 * 1024 * 1024) {
      setError('ファイルサイズが大きすぎます（最大500MB）');
      return;
    }

    setFile(selectedFile);
    setError(null);
    setFileInfo(null);
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    
    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      handleFileSelect(files[0]);
    }
  }, [handleFileSelect]);

  const handleFileInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      handleFileSelect(files[0]);
    }
  }, [handleFileSelect]);

  const startStatusCheck = useCallback((jobId: string) => {
    const checkStatus = async () => {
      try {
        const response = await fetch(`/api/status/${jobId}`);
        if (response.ok) {
          const status: JobStatus = await response.json();
          setJobStatus(status);
          
          if (status.status === 'completed' || status.status === 'failed') {
            if (statusCheckInterval.current) {
              clearInterval(statusCheckInterval.current);
              statusCheckInterval.current = null;
            }
          }
        }
      } catch (error) {
        console.error('ステータス確認エラー:', error);
      }
    };

    // 初回実行
    checkStatus();
    
    // 定期実行
    statusCheckInterval.current = setInterval(checkStatus, 2000);
  }, []);

  const handleUpload = useCallback(async () => {
    if (!file) return;

    setIsUploading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('target_lang', targetLang);

      const response = await fetch('/api/upload', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'アップロードに失敗しました');
      }

      const result = await response.json();
      
      setJobId(result.job_id);
      setFileInfo({
        name: result.filename,
        pages: result.pages,
        textCount: result.text_count,
      });

      // ステータス確認を開始
      startStatusCheck(result.job_id);

    } catch (error) {
      setError(error instanceof Error ? error.message : 'アップロードエラーが発生しました');
    } finally {
      setIsUploading(false);
    }
  }, [file, targetLang, startStatusCheck]);

  const handleDownload = useCallback(async () => {
    if (!jobId || !jobStatus || jobStatus.status !== 'completed') return;

    try {
      const response = await fetch(`/api/download/${jobId}`);
      if (!response.ok) {
        throw new Error('ダウンロードに失敗しました');
      }

      const blob = await response.blob();
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

      // ダウンロード後にリセット
      handleReset();
    } catch (error) {
      setError('ダウンロードエラーが発生しました');
    }
  }, [jobId, jobStatus]);

  const handleReset = useCallback(() => {
    setFile(null);
    setFileInfo(null);
    setJobId(null);
    setJobStatus(null);
    setError(null);
    
    if (statusCheckInterval.current) {
      clearInterval(statusCheckInterval.current);
      statusCheckInterval.current = null;
    }
    
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  }, []);

  const renderUploadArea = () => (
    <div
      className={`upload-area ${isDragOver ? 'drag-over' : ''}`}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      onClick={() => fileInputRef.current?.click()}
    >
      <div className="upload-icon">📄</div>
      <div className="upload-text">
        PPTXファイルをドラッグ&ドロップ
      </div>
      <div className="upload-subtext">
        またはクリックしてファイルを選択
      </div>
      <input
        ref={fileInputRef}
        type="file"
        accept=".pptx"
        className="file-input"
        onChange={handleFileInputChange}
      />
    </div>
  );

  const renderFileInfo = () => {
    if (!file) return null;

    return (
      <div className="file-info">
        <h3>選択されたファイル</h3>
        <p><strong>ファイル名:</strong> {file.name}</p>
        <p><strong>ファイルサイズ:</strong> {(file.size / 1024 / 1024).toFixed(1)} MB</p>
        {fileInfo && (
          <>
            <p><strong>ページ数:</strong> {fileInfo.pages} ページ</p>
            <p><strong>翻訳対象テキスト数:</strong> {fileInfo.textCount} 個</p>
          </>
        )}
      </div>
    );
  };

  const renderStatus = () => {
    if (!jobStatus) return null;

    const getStatusText = () => {
      switch (jobStatus.status) {
        case 'queued':
          return `キューで待機中 (${jobStatus.queue_position}番目)`;
        case 'processing':
          return '翻訳処理中...';
        case 'completed':
          return '翻訳完了！';
        case 'failed':
          return '翻訳に失敗しました';
        default:
          return '状態不明';
      }
    };

    const getProgressPercentage = () => {
      switch (jobStatus.status) {
        case 'queued':
          return 25;
        case 'processing':
          return 75;
        case 'completed':
          return 100;
        case 'failed':
          return 0;
        default:
          return 0;
      }
    };

    return (
      <div className="status-area">
        <div className="status-card">
          <div className="status-title">{getStatusText()}</div>
          
          {jobStatus.status !== 'failed' && (
            <div className="progress-bar">
              <div 
                className="progress-fill" 
                style={{ width: `${getProgressPercentage()}%` }}
              />
            </div>
          )}

          {jobStatus.status === 'queued' && jobStatus.total_in_queue > 0 && (
            <div className="queue-info">
              現在 {jobStatus.total_in_queue} 件の翻訳が待機中です
            </div>
          )}

          {jobStatus.status === 'processing' && (
            <div className="status-text">
              しばらくお待ちください...
            </div>
          )}

          {jobStatus.status === 'completed' && (
            <div className="success">
              <p>翻訳が完了しました！ファイルをダウンロードしてください。</p>
              
              {/* トークン情報表示 */}
              {jobStatus.total_tokens !== undefined && (
                <div className="token-info">
                  <h4>💰 翻訳コスト情報</h4>
                  <div className="token-stats">
                    <div className="token-stat">
                      <span className="token-label">使用トークン数:</span>
                      <span className="token-value">{jobStatus.total_tokens?.toLocaleString()}</span>
                    </div>
                    <div className="token-stat">
                      <span className="token-label">入力トークン:</span>
                      <span className="token-value">{jobStatus.input_tokens?.toLocaleString()}</span>
                    </div>
                    <div className="token-stat">
                      <span className="token-label">出力トークン:</span>
                      <span className="token-value">{jobStatus.output_tokens?.toLocaleString()}</span>
                    </div>
                    <div className="token-stat cost">
                      <span className="token-label">翻訳費用:</span>
                      <span className="token-value">${jobStatus.total_cost_usd?.toFixed(6)}</span>
                    </div>
                    {jobStatus.model_name && (
                      <div className="token-stat">
                        <span className="token-label">使用モデル:</span>
                        <span className="token-value">{jobStatus.model_name}</span>
                      </div>
                    )}
                    {jobStatus.processing_time && (
                      <div className="token-stat">
                        <span className="token-label">処理時間:</span>
                        <span className="token-value">{jobStatus.processing_time.toFixed(1)}秒</span>
                      </div>
                    )}
                  </div>
                </div>
              )}
              
              <p className="status-text">
                ダウンロード後、ファイルはサーバーから即座に削除されます。
              </p>
              <button 
                className="button download-button"
                onClick={handleDownload}
              >
                翻訳済みファイルをダウンロード
              </button>
            </div>
          )}

          {jobStatus.status === 'failed' && jobStatus.error_message && (
            <div className="error">
              <h4>エラーが発生しました</h4>
              <p>{jobStatus.error_message}</p>
            </div>
          )}
        </div>

        <button 
          className="button reset-button"
          onClick={handleReset}
        >
          新しいファイルを翻訳する
        </button>
      </div>
    );
  };

  return (
    <div className="app">
      <div className="container">
        <div className="header">
          <h1 className="title">PPTX翻訳サービス</h1>
          <p className="subtitle">
            PowerPointファイルを高品質に翻訳します<br />
            ファイルは翻訳後に自動削除され、プライバシーを保護します
          </p>
        </div>

        {/* 月次コスト表示 */}
        {monthlyCost && (
          <div className="monthly-cost-card">
            <h3>📊 今月の翻訳コスト</h3>
            <div className="cost-summary">
              <div className="cost-item">
                <span className="cost-label">対象月:</span>
                <span className="cost-value">{monthlyCost.current_month}</span>
              </div>
              <div className="cost-item highlight">
                <span className="cost-label">累計費用:</span>
                <span className="cost-value">${monthlyCost.total_cost_usd.toFixed(6)}</span>
              </div>
              <div className="cost-item">
                <span className="cost-label">累計トークン:</span>
                <span className="cost-value">{monthlyCost.total_tokens.toLocaleString()}</span>
              </div>
              <div className="cost-item">
                <span className="cost-label">翻訳回数:</span>
                <span className="cost-value">{monthlyCost.total_transactions.toLocaleString()} 回</span>
              </div>
            </div>
          </div>
        )}

        {!jobStatus ? (
          <>
            {renderUploadArea()}
            
            {renderFileInfo()}

            {file && (
              <div className="form-group">
                <label className="label">翻訳先言語</label>
                <select 
                  className="select"
                  value={targetLang}
                  onChange={(e) => setTargetLang(e.target.value as 'ja' | 'en')}
                >
                  <option value="en">英語</option>
                  <option value="ja">日本語</option>
                </select>
              </div>
            )}

            {file && (
              <div className="warning">
                ⚠️ アップロードしたファイルは翻訳完了後に即座にサーバーから削除されます
              </div>
            )}

            {error && (
              <div className="error">
                <h4>エラー</h4>
                <p>{error}</p>
              </div>
            )}

            <button 
              className="button button-primary"
              onClick={handleUpload}
              disabled={!file || isUploading}
            >
              {isUploading ? '翻訳を開始しています...' : '翻訳を開始'}
            </button>
          </>
        ) : (
          renderStatus()
        )}
      </div>
    </div>
  );
};

export default App;