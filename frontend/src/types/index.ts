export interface Document {
  document_id: string;
  title: string;
  source: 'federal_register' | 'far_dfars' | 'nist' | 'iso';
  document_type: string;
  publication_date: string;
  updated_at: string;
  metadata: {
    content_summary?: string;
    agency?: string;
    citation?: string;
    effective_date?: string;
    comments_due_date?: string;
    docket_numbers?: string[];
    regulation_id_numbers?: string[];
    cfr_references?: string[];
    topics?: string[];
    keywords?: string[];
    [key: string]: any;
  };
}

export interface Relationship {
  source_id: string;
  source_title: string;
  target_id: string;
  target_title: string;
  relationship_type: string;
  metadata: {
    confidence_score?: number;
    extracted_date?: string;
    context?: string;
    [key: string]: any;
  };
}

export interface DocumentFilter {
  source?: string;
  document_type?: string;
  start_date?: string;
  end_date?: string;
  agency?: string;
  topic?: string;
  keyword?: string;
}

export interface PaginationParams {
  page: number;
  page_size: number;
}

export interface SortParams {
  sort_by: string;
  sort_order: 'asc' | 'desc';
}

export interface DocumentsResponse {
  documents: Document[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface RelationshipsResponse {
  relationships: Relationship[];
  total: number;
}

export interface IngestionJob {
  job_id: string;
  source: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress?: number;
  error?: string;
  created_at: string;
  updated_at: string;
  metadata: {
    total_documents?: number;
    processed_documents?: number;
    failed_documents?: number;
    start_date?: string;
    end_date?: string;
    document_type?: string;
    [key: string]: any;
  };
}

export interface ErrorResponse {
  status: number;
  message: string;
  details?: {
    [key: string]: any;
  };
} 