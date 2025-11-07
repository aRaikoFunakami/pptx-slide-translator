import { JobStatus, MonthlyCost } from '../types';

export const translationApi = {
  /**
   * ファイルをアップロードして翻訳ジョブを開始
   */
  uploadFile: async (file: File, targetLang: string): Promise<JobStatus> => {
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

    return response.json();
  },

  /**
   * ジョブのステータスを取得
   */
  getJobStatus: async (jobId: string): Promise<JobStatus> => {
    const response = await fetch(`/api/status/${jobId}`);
    
    if (!response.ok) {
      throw new Error('ステータス取得に失敗しました');
    }

    return response.json();
  },

  /**
   * 翻訳済みファイルをダウンロード
   */
  downloadFile: async (jobId: string): Promise<Blob> => {
    const response = await fetch(`/api/download/${jobId}`);
    
    if (!response.ok) {
      throw new Error('ダウンロードに失敗しました');
    }

    return response.blob();
  },

  /**
   * 月次コスト情報を取得
   */
  getMonthlyCost: async (): Promise<MonthlyCost> => {
    const response = await fetch('/api/cost/monthly');
    
    if (!response.ok) {
      throw new Error('月次コスト取得に失敗しました');
    }

    return response.json();
  },

  /**
   * ジョブをキャンセル
   */
  cancelJob: async (jobId: string): Promise<void> => {
    const response = await fetch(`/api/cancel/${jobId}`, {
      method: 'POST',
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'キャンセルに失敗しました');
    }
  },
};
