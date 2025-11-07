import React from 'react';
import { JobStatus } from '../../types';

interface JobStatusDisplayProps {
  jobStatus: JobStatus;
  onDownload: () => void;
  onReset: () => void;
  onCancel: () => void;
}

export const JobStatusDisplay: React.FC<JobStatusDisplayProps> = ({
  jobStatus,
  onDownload,
  onReset,
  onCancel,
}) => {
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
          <div className="status-text">しばらくお待ちください...</div>
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
                    <span className="token-value">
                      {jobStatus.total_tokens?.toLocaleString()}
                    </span>
                  </div>
                  <div className="token-stat">
                    <span className="token-label">入力トークン:</span>
                    <span className="token-value">
                      {jobStatus.input_tokens?.toLocaleString()}
                    </span>
                  </div>
                  <div className="token-stat">
                    <span className="token-label">出力トークン:</span>
                    <span className="token-value">
                      {jobStatus.output_tokens?.toLocaleString()}
                    </span>
                  </div>
                  <div className="token-stat cost">
                    <span className="token-label">翻訳費用:</span>
                    <span className="token-value">
                      ${jobStatus.total_cost_usd?.toFixed(6)}
                    </span>
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
                      <span className="token-value">
                        {jobStatus.processing_time.toFixed(1)}秒
                      </span>
                    </div>
                  )}
                </div>
              </div>
            )}

            <p className="status-text">
              ダウンロード後、ファイルはサーバーから即座に削除されます。
            </p>
            <button className="button download-button" onClick={onDownload}>
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

      {/* キューまたは処理中の場合はキャンセルボタン */}
      {jobStatus.status === 'queued' || jobStatus.status === 'processing' ? (
        <button className="button reset-button" onClick={onCancel}>
          キャンセル
        </button>
      ) : jobStatus.status === 'failed' ? (
        <button className="button reset-button" onClick={onReset}>
          新しいファイルを翻訳する
        </button>
      ) : null}
    </div>
  );
};
