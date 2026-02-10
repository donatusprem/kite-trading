/**
 * Kite Account Data Integration
 * All data is now fetched from the live API - no hardcoded values
 */

export interface KiteAccountData {
  netMargin: number;
  cashBalance: number;
  collateral: number;

  holdings: Array<{
    symbol: string;
    quantity: number;
    avgPrice: number;
    currentPrice: number;
    value: number;
    pnl: number;
    pnlPercent: number;
  }>;

  positions: Array<{
    symbol: string;
    quantity: number;
    avgPrice: number;
    currentPrice: number;
    pnl: number;
    pnlPercent: number;
    product: string;
  }>;

  orders: Array<{
    orderId: string;
    symbol: string;
    quantity: number;
    price: number;
    status: string;
    orderType: string;
    timestamp: string;
  }>;
}

export interface BacktestResult {
  strategy: string;
  capital: number;
  returnPercent: number;
  profitAmount: number;
  winRate: number;
  trades: number;
  winners: number;
  losers: number;
}

// Backtest results are historical and static - these don't change
export const backtestResults: BacktestResult[] = [
  {
    strategy: "Buying Calls (EMA20)",
    capital: 35000,
    returnPercent: 131.66,
    profitAmount: 46081,
    winRate: 68.4,
    trades: 19,
    winners: 13,
    losers: 6
  },
  {
    strategy: "Buying Calls (RSI2)",
    capital: 35000,
    returnPercent: 117.58,
    profitAmount: 41152,
    winRate: 64.7,
    trades: 17,
    winners: 11,
    losers: 6
  },
  {
    strategy: "Credit Spreads",
    capital: 35000,
    returnPercent: -91.83,
    profitAmount: -32141,
    winRate: 50.0,
    trades: 8,
    winners: 4,
    losers: 4
  },
  {
    strategy: "Iron Condor",
    capital: 35000,
    returnPercent: -84.70,
    profitAmount: -29645,
    winRate: 40.0,
    trades: 5,
    winners: 2,
    losers: 3
  }
];

// Helper function to format currency
export const formatINR = (amount: number): string => {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0
  }).format(amount);
};

// Helper function to format percentage
export const formatPercent = (value: number): string => {
  return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
};
