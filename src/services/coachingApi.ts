import axios from 'axios';
import type { WalletBalance, Transaction } from '@/types/coaching';

const API_BASE = 'http://localhost:8000/api/coaching';

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token interceptor (to be configured with actual token)
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const coachingApi = {
  // Wallet endpoints
  getBalance: async (): Promise<WalletBalance> => {
    const { data } = await api.get('/wallet/balance');
    return data;
  },

  getTransactions: async (limit = 10): Promise<Transaction[]> => {
    const { data } = await api.get(`/wallet/transactions?limit=${limit}`);
    return data;
  },

  topup: async (amount_npr: number, payment_method_id: string) => {
    const { data } = await api.post('/wallet/topup', {
      amount_npr,
      payment_method_id,
    });
    return data;
  },
};

