// frontend/src/components/exit/TokenExitTable.tsx
import React from 'react';
import { Token } from '../../types';

interface TokenExitTableProps {
  token: Token;
  holders: any[];
  selectedClients: Set<number>;
  onClientSelection: (clientId: number, selected: boolean) => void;
  onSelectAll: () => void;
  onDeselectAll: () => void;
  onBatchExit: () => void;
  isExiting: boolean;
}

const TokenExitTable: React.FC<TokenExitTableProps> = ({
  token,
  holders,
  selectedClients,
  onClientSelection,
  onSelectAll,
  onDeselectAll,
  onBatchExit,
  isExiting,
}) => {
  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 2,
    }).format(amount);
  };

  const getTotalValue = () => {
    return holders
      .filter(holder => selectedClients.has(holder.client.id))
      .reduce((sum, holder) => sum + (holder.total_quantity * token.ltp), 0);
  };

  const getTotalQuantity = () => {
    return holders
      .filter(holder => selectedClients.has(holder.client.id))
      .reduce((sum, holder) => sum + holder.total_quantity, 0);
  };

  return (
    <div className="bg-white rounded-lg shadow-md overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
        <div className="flex justify-between items-center">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">
              {token.symbol} Holders
            </h2>
            <p className="text-sm text-gray-600">
              {holders.length} holders • {selectedClients.size} selected
            </p>
          </div>
          <div className="flex items-center space-x-3">
            <button
              onClick={onSelectAll}
              className="px-3 py-1 text-sm bg-blue-100 text-blue-700 rounded hover:bg-blue-200"
            >
              Select All
            </button>
            <button
              onClick={onDeselectAll}
              className="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
            >
              Deselect All
            </button>
          </div>
        </div>
      </div>

      {/* Summary */}
      {selectedClients.size > 0 && (
        <div className="px-6 py-4 bg-yellow-50 border-b border-yellow-200">
          <div className="flex justify-between items-center">
            <div className="text-sm text-yellow-800">
              <strong>{selectedClients.size}</strong> clients selected • 
              <strong> {getTotalQuantity().toLocaleString()}</strong> total quantity • 
              <strong> {formatCurrency(getTotalValue())}</strong> estimated value
            </div>
            <button
              onClick={onBatchExit}
              disabled={isExiting || selectedClients.size === 0}
              className="px-6 py-2 bg-red-600 text-white font-medium rounded-lg hover:bg-red-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
            >
              {isExiting ? 'Exiting Positions...' : `Exit ${selectedClients.size} Positions`}
            </button>
          </div>
        </div>
      )}

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                <input
                  type="checkbox"
                  checked={selectedClients.size === holders.length && holders.length > 0}
                  onChange={(e) => e.target.checked ? onSelectAll() : onDeselectAll()}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Client
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Quantity
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
                Market Value
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Trades
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {holders.map((holder) => {
              const pnl = (token.ltp - holder.avg_price) * holder.total_quantity;
              const marketValue = holder.total_quantity * token.ltp;
              const isSelected = selectedClients.has(holder.client.id);
              
              return (
                <tr key={holder.client.id} className={`hover:bg-gray-50 ${isSelected ? 'bg-blue-50' : ''}`}>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <input
                      type="checkbox"
                      checked={isSelected}
                      onChange={(e) => onClientSelection(holder.client.id, e.target.checked)}
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div>
                      <div className="text-sm font-medium text-gray-900">
                        {holder.client.name}
                      </div>
                      <div className="text-sm text-gray-500">
                        {holder.client.motilal_client_id}
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {holder.total_quantity.toLocaleString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    ₹{holder.avg_price.toFixed(2)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    ₹{token.ltp.toFixed(2)}
                  </td>
                  <td className={`px-6 py-4 whitespace-nowrap text-sm font-medium ${
                    pnl >= 0 ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {formatCurrency(pnl)}
                    <div className="text-xs text-gray-500">
                      {((pnl / (holder.avg_price * holder.total_quantity)) * 100).toFixed(2)}%
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {formatCurrency(marketValue)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {holder.trades.length} trades
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      
      {holders.length === 0 && (
        <div className="text-center py-12">
          <p className="text-gray-500">No holders found for this token</p>
        </div>
      )}
    </div>
  );
};

export default TokenExitTable;
