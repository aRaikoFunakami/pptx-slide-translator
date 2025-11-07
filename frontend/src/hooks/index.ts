import { useState, useCallback, useRef, useEffect } from 'react';
import { JobStatus, MonthlyCost } from '../types';
import { translationApi } from '../services/api';

/**
 * 月次コスト管理フック
 */
export const useMonthlyCost = () => {
  const [monthlyCost, setMonthlyCost] = useState<MonthlyCost | null>(null);

  const fetchMonthlyCost = useCallback(async () => {
    try {
      const data = await translationApi.getMonthlyCost();
      setMonthlyCost(data);
    } catch (error) {
      console.error('月次コスト取得エラー:', error);
    }
  }, []);

  useEffect(() => {
    fetchMonthlyCost();
  }, [fetchMonthlyCost]);

  return { monthlyCost, fetchMonthlyCost };
};

/**
 * ジョブステータス監視フック
 */
export const useJobStatusPolling = (
  jobId: string | null,
  onComplete?: () => void
) => {
  const [jobStatus, setJobStatus] = useState<JobStatus | null>(null);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  const checkStatus = useCallback(async () => {
    if (!jobId) return;

    try {
      const status = await translationApi.getJobStatus(jobId);
      setJobStatus(status);

      if (status.status === 'completed' || status.status === 'failed') {
        if (intervalRef.current) {
          clearInterval(intervalRef.current);
          intervalRef.current = null;
        }

        if (status.status === 'completed' && onComplete) {
          onComplete();
        }
      }
    } catch (error) {
      console.error('ステータス確認エラー:', error);
    }
  }, [jobId, onComplete]);

  useEffect(() => {
    if (!jobId) {
      setJobStatus(null);
      return;
    }

    // 初回実行
    checkStatus();

    // 定期実行
    intervalRef.current = setInterval(checkStatus, 2000);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [jobId, checkStatus]);

  return jobStatus;
};

/**
 * ファイル選択管理フック
 */
export const useFileSelection = () => {
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

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
  }, []);

  const resetFile = useCallback(() => {
    setFile(null);
    setError(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  }, []);

  return {
    file,
    error,
    fileInputRef,
    handleFileSelect,
    resetFile,
    setError,
  };
};
