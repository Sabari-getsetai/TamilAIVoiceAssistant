// API Response Types
export interface UploadResponse {
  success: boolean;
  message: string;
  files: Array<{
    filename: string;
    path: string;
    size: string;
  }>;
  upload_dir: string;
}

export interface IngestionStatusResponse {
  session_id: string;
  status: 'pending' | 'loading' | 'chunking' | 'embedding' | 'indexing' | 'completed' | 'failed';
  progress?: number;
  message?: string;
  started_at?: string;
  completed_at?: string;
  indexed_count?: number;
  error?: string;
}

export interface Document {
  id: string;
  filename: string;
  file_size: number;
  chunk_count: number;
  upload_date: string;
  status: 'indexed' | 'processing' | 'failed';
  text_preview?: string;
  indexed_at?: string;
  metadata?: Record<string, unknown>;
}

export interface DocumentsResponse {
  documents: Document[];
  total: number;
}

export interface DocumentDetailResponse extends Document {
  text_preview: string;
  indexed_at: string;
}

export interface ReindexResponse {
  success: boolean;
  message: string;
  chunks_reindexed?: number;
  documents_reindexed?: number;
}

export interface IndexStatsResponse {
  exists?: boolean;
  message?: string;
  total_documents?: number;
  total_chunks?: number;
  index_size_mb?: number;
  last_updated?: string;
  embedding_model?: string;
  embedding_dimension?: number;
}

// Component Props Types
export interface StatsCardProps {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  color?: 'primary' | 'secondary' | 'success' | 'error' | 'warning' | 'info';
  loading?: boolean;
}

export interface DocumentCardProps {
  document: Document;
  onDelete: (id: string) => void;
  deleting?: boolean;
}

// Form Types
export interface UploadFormData {
  files: File[];
}

// API Error Type
export interface ApiError {
  detail?: string;
  message?: string;
}
