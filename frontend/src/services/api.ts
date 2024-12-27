import axios from 'axios';
import { Document, Relationship } from '@/types';

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
});

interface FetchDocumentsParams {
  page: number;
  pageSize: number;
  source?: string | null;
  documentType?: string | null;
  startDate?: string | null;
  endDate?: string | null;
}

interface DocumentsResponse {
  documents: Document[];
  total: number;
}

export async function fetchDocuments(params: FetchDocumentsParams): Promise<DocumentsResponse> {
  const { data } = await api.get('/documents', {
    params: {
      page: params.page,
      page_size: params.pageSize,
      source: params.source,
      document_type: params.documentType,
      start_date: params.startDate,
      end_date: params.endDate,
    },
  });
  return data;
}

export async function fetchDocument(documentId: string): Promise<Document> {
  const { data } = await api.get(`/documents/${documentId}`);
  return data;
}

export async function fetchDocumentRelationships(documentId: string): Promise<Relationship[]> {
  const { data } = await api.get(`/documents/${documentId}/relationships`);
  return data;
}

interface IngestParams {
  source: 'federal_register' | 'far_dfars' | 'standards';
  startDate?: string;
  endDate?: string;
  documentType?: string;
}

export async function triggerIngestion(params: IngestParams): Promise<{ job_id: string }> {
  const { data } = await api.post(`/ingest/${params.source}`, {
    start_date: params.startDate,
    end_date: params.endDate,
    document_type: params.documentType,
  });
  return data;
}

export async function checkIngestionStatus(jobId: string): Promise<{
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress?: number;
  error?: string;
}> {
  const { data } = await api.get(`/ingest/status/${jobId}`);
  return data;
}

// Error handling interceptor
api.interceptors.response.use(
  response => response,
  error => {
    // Handle specific error cases
    if (error.response) {
      switch (error.response.status) {
        case 401:
          // Handle unauthorized
          break;
        case 403:
          // Handle forbidden
          break;
        case 404:
          // Handle not found
          break;
        case 422:
          // Handle validation error
          break;
        case 500:
          // Handle server error
          break;
      }
    }
    return Promise.reject(error);
  }
); 