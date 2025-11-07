export interface FileInfo {
  name: string;
  pages: number;
  textCount: number;
}

export interface JobStatus {
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

export interface MonthlyCost {
  current_month: string;
  total_cost_usd: number;
  total_tokens: number;
  total_transactions: number;
}

export type TargetLang = 'ja' | 'en';
