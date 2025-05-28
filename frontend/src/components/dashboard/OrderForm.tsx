// frontend/src/components/dashboard/OrderForm.tsx
import React, { useState } from 'react';
import { useAppStore } from '../../store';
import TokenSelector from './TokenSelector';
import ClientTable from './ClientTable';
import { ordersApi } from '../../services/api';
import { BatchOrder } from '../../types';

const OrderForm: React.FC = () => {
  const { selectedToken, clients, setLoading, setError } = useAppStore();
  const [formData, setFormData] = useState({
    tradeType: 'INTRADAY' as 'MTF' | 'INTRADAY' | 'DELIVERY',
    orderType: 'MARKET' as 'MARKET' | 'LIMIT',
    executionType: 'BUY' as 'BUY' | 'SELL' | 'EXIT',
    price: '',
  });
  
  const [clientQuantities, setClientQuantities] = useState<Record<number, number>>({});
  const [isExecuting, setIsExecuting] = useState(false);

  const handleQuantityChange = (clientId: number, quantity: number) => {
    setClientQuantities(prev => ({
      ...prev,
      [clientId]: quantity
    }));
  };

  const executeAllOrders = async () => {
    if (!selectedToken) {
      setError('Please select a token first');
      return;
    }

    const clientOrders = Object.entries(clientQuantities)
      .filter(([_, quantity]) => quantity > 0)
      .map(([clientId, quantity]) => ({
        client_id: parseInt(clientId),
        quantity
      }));

    if (clientOrders.length === 0) {
      setError('Please set quantities for at least one client');
      return;
    }

    const batchOrder: BatchOrder = {
      token_id: selectedToken.id,
      execution_type: formData.executionType,
      order_type: formData.orderType,
      trade_type: formData.tradeType,
      price: formData.price ? parseFloat(formData.price) : undefined,
      client_orders: clientOrders
    };

    try {
      setIsExecuting(true);
      setLoading(true);
      
      const response = await ordersApi.executeAll(batchOrder);
      
      // Show success message with results
      console.log('Batch order results:', response.data);
      
      // Reset form
      setClientQuantities({});
      
    } catch (error: any) {
      setError(error.response?.data?.detail || 'Failed to execute orders');
      console.error('Order execution error:', error);
    } finally {
      setIsExecuting(false);
      setLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-xl font-semibold text-gray-900 mb-6">Order Management</h2>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Order Configuration */}
        <div className="space-y-4">
          <TokenSelector />
          
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Trade Type
              </label>
              <select
                value={formData.tradeType}
                onChange={(e) => setFormData(prev => ({ 
                  ...prev, 
                  tradeType: e.target.value as typeof formData.tradeType 
                }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="INTRADAY">Intraday</option>
                <option value="DELIVERY">Delivery</option>
                <option value="MTF">MTF</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Order Type
              </label>
              <select
                value={formData.orderType}
                onChange={(e) => setFormData(prev => ({ 
                  ...prev, 
                  orderType: e.target.value as typeof formData.orderType 
                }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="MARKET">Market</option>
                <option value="LIMIT">Limit</option>
              </select>
            </div>
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Execution Type
              </label>
              <select
                value={formData.executionType}
                onChange={(e) => setFormData(prev => ({ 
                  ...prev, 
                  executionType: e.target.value as typeof formData.executionType 
                }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="BUY">Buy</option>
                <option value="SELL">Sell</option>
                <option value="EXIT">Exit</option>
              </select>
            </div>
            
            {formData.orderType === 'LIMIT' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Price
                </label>
                <input
                  type="number"
                  step="0.05"
                  value={formData.price}
                  onChange={(e) => setFormData(prev => ({ ...prev, price: e.target.value }))}
                  placeholder="Enter price"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
            )}
          </div>
        </div>
        
        {/* Order Summary */}
        <div className="bg-gray-50 rounded-lg p-4">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Order Summary</h3>
          
          {selectedToken ? (
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-gray-600">Token:</span>
                <span className="font-medium">{selectedToken.symbol}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Current Price:</span>
                <span className="font-medium">₹{selectedToken.ltp.toFixed(2)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Total Clients:</span>
                <span className="font-medium">
                  {Object.values(clientQuantities).filter(q => q > 0).length}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Total Quantity:</span>
                <span className="font-medium">
                  {Object.values(clientQuantities).reduce((sum, q) => sum + q, 0)}
                </span>
              </div>
              <div className="flex justify-between font-semibold text-lg border-t pt-2">
                <span>Estimated Value:</span>
                <span>
                  ₹{(Object.values(clientQuantities).reduce((sum, q) => sum + q, 0) * selectedToken.ltp).toLocaleString()}
                </span>
              </div>
            </div>
          ) : (
            <p className="text-gray-500 text-center py-4">Select a token to see order summary</p>
          )}
        </div>
      </div>
      
      {/* Client Table */}
      <div className="mt-6">
        <ClientTable 
          onQuantityChange={handleQuantityChange}
          quantities={clientQuantities}
        />
      </div>
      
      {/* Execute Button */}
      <div className="mt-6 flex justify-center">
        <button
          onClick={executeAllOrders}
          disabled={!selectedToken || isExecuting || Object.values(clientQuantities).every(q => q === 0)}
          className="px-8 py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
        >
          {isExecuting ? 'Executing Orders...' : 'Execute All Orders'}
        </button>
      </div>
    </div>
  );
};

export default OrderForm;