import { useQuery } from '@tanstack/react-query';
import { coachingApi } from '@/services/coachingApi';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Wallet, TrendingUp, Clock, Plus } from 'lucide-react';

export function WalletDashboard() {
  const { data: balance, isLoading: balanceLoading } = useQuery({
    queryKey: ['wallet-balance'],
    queryFn: coachingApi.getBalance,
  });

  const { data: transactions = [], isLoading: txLoading } = useQuery({
    queryKey: ['wallet-transactions'],
    queryFn: () => coachingApi.getTransactions(10),
  });

  const formatCurrency = (amount: number) => `NPR ${amount.toFixed(2)}`;
  const formatDate = (dateString: string) => new Date(dateString).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });

  if (balanceLoading) {
    return <div className="flex items-center justify-center h-64">Loading wallet...</div>;
  }

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Coaching Wallet</h1>
          <p className="text-muted-foreground">Manage your coaching credits</p>
        </div>
        <Button className="gap-2">
          <Plus className="h-4 w-4" />
          Top Up
        </Button>
      </div>

      {/* Balance Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Available Balance</CardTitle>
            <Wallet className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {formatCurrency(balance?.available_balance || 0)}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Ready to use for sessions
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Reserved</CardTitle>
            <Clock className="h-4 w-4 text-orange-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-orange-600">
              {formatCurrency(balance?.reserved_balance || 0)}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Held for active sessions
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Lifetime Spent</CardTitle>
            <TrendingUp className="h-4 w-4 text-blue-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">
              {formatCurrency(balance?.balance || 0)}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Total wallet balance
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Bonus Tiers Info */}
      <Card className="bg-gradient-to-r from-blue-50 to-indigo-50">
        <CardHeader>
          <CardTitle className="text-lg">Bonus Tiers</CardTitle>
          <CardDescription>Get extra credits when you top up!</CardDescription>
        </CardHeader>
        <CardContent className="space-y-2">
          <div className="flex justify-between items-center">
            <span className="text-sm">Top up NPR 1,000+</span>
            <span className="font-semibold text-green-600">+10% Bonus</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-sm">Top up NPR 2,000+</span>
            <span className="font-semibold text-green-600">+20% Bonus</span>
          </div>
        </CardContent>
      </Card>

      {/* Transaction History */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Transactions</CardTitle>
          <CardDescription>Your last 10 wallet activities</CardDescription>
        </CardHeader>
        <CardContent>
          {txLoading ? (
            <div className="text-center py-4">Loading transactions...</div>
          ) : transactions.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              No transactions yet. Top up to get started!
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Date</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Description</TableHead>
                  <TableHead className="text-right">Amount</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {transactions.map((tx) => (
                  <TableRow key={tx.transaction_id}>
                    <TableCell className="text-sm">{formatDate(tx.created_at)}</TableCell>
                    <TableCell>
                      <span
                        className={`px-2 py-1 rounded-full text-xs font-medium ${
                          tx.transaction_type === 'topup' || tx.transaction_type === 'bonus'
                            ? 'bg-green-100 text-green-800'
                            : tx.transaction_type === 'refund'
                            ? 'bg-blue-100 text-blue-800'
                            : 'bg-red-100 text-red-800'
                        }`}
                      >
                        {tx.transaction_type}
                      </span>
                    </TableCell>
                    <TableCell className="text-sm">{tx.description || 'N/A'}</TableCell>
                    <TableCell
                      className={`text-right font-medium ${
                        tx.amount > 0 ? 'text-green-600' : 'text-red-600'
                      }`}
                    >
                      {tx.transaction_type === 'topup' || tx.transaction_type === 'bonus' || tx.transaction_type === 'refund' ? '+' : ''}
                      {formatCurrency(Math.abs(tx.amount))}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

