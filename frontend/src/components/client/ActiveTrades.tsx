// frontend/src/components/client/ActiveTrades.tsx
import React, { useState } from 'react';
import { Trade } from '../../types';
import { tradesApi } from '../../services/api';
import TradeRow from './TradeRow';

interface ActiveTradesProps {
  trades: Trade[];
  onTradeUpdate: () => void;
}

const ActiveTrades: React.FC<ActiveTradesProps> = ({ trades, onTradeUpdate }) => {
  const [exitingTrades, setExitingTrades] = useState<Set<string>>(new Set());

  const handleExitTrade = async (tradeId: string) => {
    setExitingTrades(prev => new Set(prev).add(tradeId));
    
    try {
      await tradesApi.exit(tradeId);
      onTradeUpdate(); // Refresh the trades list
    } catch (error: any) {
      console.error('Error exiting trade:', error);
      alert(error.response?.data?.detail || 'Failed to exit trade');
    } finally {
      setExitingTrades(prev => {
        const newSet = new Set(prev);
        newSet.delete(tradeId);
        return newSet;
      });
    }
  };

  const activeTrades = trades.filter(trade => trade.status === 'ACTIVE');
  const closedTrades = trades.filter(trade => trade.status === 'CLOSED');

  return (
    <div className="bg-white rounded-lg shadow-md overflow-hidden">
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex justify-between items-center">
          <h2 className="text-xl font-semibold text-gray-900">Active Trades</h2>
          <div className="text-sm text-gray-600">
            {activeTrades.length} active • {closedTrades.length} closed
          </div>
        </div>
      </div>
      
      {/* Active Trades */}
      {activeTrades.length > 0 && (
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Trade Details
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Token
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Avg Price
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Current Price
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  P&L
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Quantity
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Margin
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {activeTrades.map((trade) => (
                <TradeRow
                  key={trade.id}
                  trade={trade}
                  onExit={handleExitTrade}
                  isExiting={exitingTrades.has(trade.trade_id)}
                />
              ))}
            </tbody>
          </table>
        </div>
      )}
      
      {activeTrades.length === 0 && (
        <div className="text-center py-8">
          <p className="text-gray-500">No active trades found</p>
        </div>
      )}
      
      {/* Closed Trades Section */}
      {closedTrades.length > 0 && (
        <div className="border-t border-gray-200">
          <div className="px-6 py-4 bg-gray-50">
            <h3 className="text-lg font-medium text-gray-900">Recent Closed Trades</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Trade Details
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Token
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Entry/Exit Price
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Realized P&L
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Duration
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {closedTrades.slice(0, 5).map((trade) => (
                  <tr key={trade.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div>
                        <div className="text-sm font-medium text-gray-900">
                          {trade.trade_id}
                        </div>
                        <div className="text-sm text-gray-500">
                          {trade.execution_type} • {trade.trade_type}
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">
                        {trade.token?.symbol}
                      </div>
                      <div className="text-sm text-gray-500">
                        {trade.token?.exchange}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      ₹{trade.avg_price.toFixed(2)}
                    </td>
                    <td className={`px-6 py-4 whitespace-nowrap text-sm font-medium ${
                      trade.realized_pnl >= 0 ? 'text-green-600' : 'text-red-600'
                    }`}>
                      ₹{trade.realized_pnl.toFixed(2)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {trade.exit_time && new Date(trade.exit_time).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

export default ActiveTrades;