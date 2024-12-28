import axios from 'axios';

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: BASE_URL,
});

export interface FederalRegisterStats {
  total_documents: number;
  documents_by_type: {
    type: string;
    count: number;
  }[];
  documents_by_agency: {
    agency: string;
    count: number;
  }[];
  documents_over_time: {
    date: string;
    count: number;
  }[];
}

export async function getFederalRegisterStats(): Promise<FederalRegisterStats> {
  const response = await api.get('/api/federal-register/stats');
  return response.data;
} 