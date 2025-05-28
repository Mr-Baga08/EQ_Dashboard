// frontend/src/components/client/TradeRow.tsx
import React from 'react';
import { Trade } from '../../types';

interface TradeRowProps {
  trade: Trade;
  onExit: (tradeId: string) => void;
  isExiting: boolean;
}

const TradeRow: React.FC<TradeRowProps> = ({ trade, onExit, isExiting }) => {
  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 2,
    }).format(amount);
  };

  const getPnlColor = (pnl: number) => {
    if (pnl > 0) return 'text-green-600';
    if (pnl < 0) return 'text-red-600';
    return 'text-gray-600';
  };

  const getExecutionTypeColor = (type: string) => {
    return type === 'BUY' ? 'text-green-600' : 'text-red-600';
  };

  return (
    <tr className="hover:bg-gray-50">
      <td className="px-6 py-4 whitespace-nowrap">
        <div>
          <div className="text-sm font-medium text-gray-900">{trade.trade_id}</div>
          <div className="text-sm text-gray-500">
            <span className={`font-medium ${getExecutionTypeColor(trade.execution_type)}`}>
              {trade.execution_type}
            </span>
            {' • '}
            {trade.trade_type}
          </div>
          <div className="text-xs text-gray-400">
            {new Date(trade.entry_time).toLocaleString()}
          </div>
        </div>
      </td>
      <td className="px-6 py-4 whitespace-nowrap">
        <div>
          <div className="text-sm font-medium text-gray-900">
            {trade.token?.symbol || 'N/A'}
          </div>
          <div className="text-sm text-gray-500">
            {trade.token?.exchange} • ID: {trade.token?.token_id}
          </div>
        </div>
      </td>
      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
        ₹{trade.avg_price.toFixed(2)}
      </td>
      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
        ₹{trade.current_price.toFixed(2)}
      </td>
      <td className="px-6 py-4 whitespace-nowrap">
        <div>
          <div className={`text-sm font-medium ${getPnlColor(trade.total_pnl)}`}>
            {formatCurrency(trade.total_pnl)}
          </div>
          <div className={`text-xs ${getPnlColor(trade.unrealized_pnl)}`}>
            Unrealized: {formatCurrency(trade.unrealized_pnl)}
          </div>
        </div>
      </td>
      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
        {trade.quantity.toLocaleString()}
      </td>
      <td className="px-6 py-4 whitespace-nowrap">
        <div>
          <div className="text-sm text-gray-900">
            Required: {formatCurrency(trade.margin_required)}
          </div>
          <div className="text-xs text-gray-500">
            Blocked: {formatCurrency(trade.margin_blocked)}
          </div>
        </div>
      </td>
      <td className="px-6 py-4 whitespace-nowrap">
        <button
          onClick={() => onExit(trade.trade_id)}
          disabled={isExiting}
          className="px-3 py-1 bg-red-600 text-white text-sm rounded hover:bg-red-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
        >
          {isExiting ? 'Exiting...' : 'Exit'}
        </button>
      </td>
    </tr>
  );
};

export default TradeRow;