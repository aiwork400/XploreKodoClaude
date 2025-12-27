export interface WalletBalance {
  balance: number;
  reserved_balance: number;
  available_balance: number;
  currency: string;
}

export interface Transaction {
  transaction_id: string;
  transaction_type: 'topup' | 'reserve' | 'charge' | 'refund' | 'bonus';
  amount: number;
  balance_before: number;
  balance_after: number;
  session_id?: string | null;
  payment_method_id?: string | null;
  description?: string | null;
  created_at: string;
}

