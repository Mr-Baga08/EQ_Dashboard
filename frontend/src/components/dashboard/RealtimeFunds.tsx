// frontend/src/components/dashboard/RealtimeFunds.tsx
import React, { useState, useEffect } from 'react';
import { 
  ArrowUpIcon, 
  ArrowDownIcon, 
  RefreshIcon,
  ExclamationTriangleIcon,
  CurrencyDollarIcon,
  TrendingUpIcon,
  ChartBarIcon
} from '@heroicons/react/24/outline';
import { clientsApi } from '../../services/api';
import { useAppStore } from '../../store';
import { Client } from '../../types';
import { useWebSocket } from '../../services/websocket';

interface FundsUpdateData {
  client_id: number;
  available_funds: number;
  margin_used: number;
  margin_available: number;
  total_pnl: number;
  timestamp: string;
}

interface PortfolioUpdate {
  type: 'portfolio_update';
  client_id: string;
  data: {
    available_funds: number;
    margin_used: number;
    margin_available: number;
    total_pnl: number;
    positions: any[];
  };
  timestamp: string;
}

const RealtimeFunds: React.FC = () => {
  const { clients, setClients } = useAppStore();
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<'connected' | 'disconnected' | 'connecting'>('disconnected');
  const [updateHistory, setUpdateHistory] = useState<Map<number, FundsUpdateData>>(new Map());
  const [refreshCount, setRefreshCount] = useState(0);

  // WebSocket connection for real-time updates
  const { sendMessage } = useWebSocket('dashboard', (data: PortfolioUpdate) => {
    handleRealtimeUpdate(data);
  });

  useEffect(() => {
    fetchInitialData();
    setConnectionStatus('connecting');
    
    // Set up periodic refresh (every 30 seconds)
    const interval = setInterval(() => {
      refreshFundsData();
    }, 30000);

    return () => {
      clearInterval(interval);
    };
  }, []);

  const fetchInitialData = async () => {
    try {
      setIsRefreshing(true);
      setConnectionStatus('connecting');
      const response = await clientsApi.getAll();
      setClients(response.data);
      setLastUpdated(new Date());
      setConnectionStatus('connected');
    } catch (error) {
      console.error('Error fetching initial data:', error);
      setConnectionStatus('disconnected');
    } finally {
      setIsRefreshing(false);
    }
  };

  const refreshFundsData = async () => {
    try {
      // Call backend endpoint to refresh funds from Motilal
      const response = await fetch('/api/v1/admin/refresh-portfolio', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      const result = await response.json();
      
      if (result.status === 'SUCCESS') {
        // Update clients with fresh data
        setClients(result.data.clients);
        setLastUpdated(new Date());
        setRefreshCount(prev => prev + 1);
      }
    } catch (error) {
      console.error('Error refreshing funds data:', error);
    }
  };

  const handleRealtimeUpdate = (update: PortfolioUpdate) => {
    const clientId = parseInt(update.client_id);
    
    setClients(prevClients => 
      prevClients.map(client => {
        if (client.id === clientId) {
          const updatedClient = {
            ...client,
            available_funds: update.data.available_funds,
            margin_used: update.data.margin_used,
            margin_available: update.data.margin_available,
            total_pnl: update.data.total_pnl,
          };

          // Store update history
          const updateData: FundsUpdateData = {
            client_id: clientId,
            available_funds: update.data.available_funds,
            margin_used: update.data.margin_used,
            margin_available: update.data.margin_available,
            total_pnl: update.data.total_pnl,
            timestamp: update.timestamp
          };

          setUpdateHistory(prev => new Map(prev.set(clientId, updateData)));
          
          return updatedClient;
        }
        return client;
      })
    );
    
    setLastUpdated(new Date());
  };

  const handleManualRefresh = async () => {
    try {
      setIsRefreshing(true);
      await refreshFundsData();
    } catch (error) {
      console.error('Error during manual refresh:', error);
    } finally {
      setIsRefreshing(false);
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const formatCurrencyDetailed = (amount: number) => {
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

  const getPnlIcon = (pnl: number) => {
    if (pnl > 0) return ArrowUpIcon;
    if (pnl < 0) return ArrowDownIcon;
    return null;
  };

  const getConnectionStatusColor = () => {
    switch (connectionStatus) {
      case 'connected': return 'text-green-600';
      case 'connecting': return 'text-yellow-600';
      case 'disconnected': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  const getTotalStats = () => {
    const totalFunds = clients.reduce((sum, client) => sum + client.available_funds, 0);
    const totalPnl = clients.reduce((sum, client) => sum + client.total_pnl, 0);
    const totalMarginUsed = clients.reduce((sum, client) => sum + client.margin_used, 0);
    const totalMarginAvailable = clients.reduce((sum, client) => sum + client.margin_available, 0);
    
    return { totalFunds, totalPnl, totalMarginUsed, totalMarginAvailable };
  };

  const { totalFunds, totalPnl, totalMarginUsed, totalMarginAvailable } = getTotalStats();

  return (
    <div className="bg-white rounded-lg shadow-md">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex justify-between items-center">
          <div className="flex items-center space-x-4">
            <h2 className="text-xl font-semibold text-gray-900">
              Real-time Portfolio Summary
            </h2>
            <div className="flex items-center space-x-2">
              <div className={`w-2 h-2 rounded-full ${
                connectionStatus === 'connected' ? 'bg-green-400' :
                connectionStatus === 'connecting' ? 'bg-yellow-400 animate-pulse' :
                'bg-red-400'
              }`}></div>
              <span className={`text-sm font-medium ${getConnectionStatusColor()}`}>
                {connectionStatus.charAt(0).toUpperCase() + connectionStatus.slice(1)}
              </span>
            </div>
            {refreshCount > 0 && (
              <div className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
                {refreshCount} updates
              </div>
            )}
          </div>
          
          <div className="flex items-center space-x-4">
            {lastUpdated && (
              <div className="text-sm text-gray-500">
                Last updated: {lastUpdated.toLocaleTimeString()}
              </div>
            )}
            <button
              onClick={handleManualRefresh}
              disabled={isRefreshing}
              className="flex items-center space-x-2 px-3 py-1 bg-blue-100 text-blue-700 rounded-md hover:bg-blue-200 disabled:opacity-50 transition-colors"
            >
              <RefreshIcon className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
              <span>Refresh</span>
            </button>
          </div>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="p-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
          <div className="bg-blue-50 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-blue-600">Total Available Funds</p>
                <p className="text-2xl font-bold text-blue-900">
                  {formatCurrency(totalFunds)}
                </p>
                <p className="text-xs text-blue-600 mt-1">
                  Live from Motilal API
                </p>
              </div>
              <div className="p-2 bg-blue-100 rounded-md">
                <CurrencyDollarIcon className="w-6 h-6 text-blue-600" />
              </div>
            </div>
          </div>

          <div className={`${totalPnl >= 0 ? 'bg-green-50' : 'bg-red-50'} rounded-lg p-4`}>
            <div className="flex items-center justify-between">
              <div>
                <p className={`text-sm font-medium ${totalPnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  Total P&L
                </p>
                <p className={`text-2xl font-bold ${totalPnl >= 0 ? 'text-green-900' : 'text-red-900'}`}>
                  {formatCurrency(totalPnl)}
                </p>
                <div className="flex items-center mt-1">
                  {(() => {
                    const Icon = getPnlIcon(totalPnl);
                    return Icon ? (
                      <Icon className={`w-3 h-3 mr-1 ${getPnlColor(totalPnl)}`} />
                    ) : null;
                  })()}
                  <p className={`text-xs ${getPnlColor(totalPnl)}`}>
                    {totalPnl >= 0 ? 'Profit' : 'Loss'}
                  </p>
                </div>
              </div>
              <div className={`p-2 ${totalPnl >= 0 ? 'bg-green-100' : 'bg-red-100'} rounded-md`}>
                <TrendingUpIcon className={`w-6 h-6 ${totalPnl >= 0 ? 'text-green-600' : 'text-red-600'}`} />
              </div>
            </div>
          </div>

          <div className="bg-orange-50 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-orange-600">Margin Used</p>
                <p className="text-2xl font-bold text-orange-900">
                  {formatCurrency(totalMarginUsed)}
                </p>
                <p className="text-xs text-orange-600 mt-1">
                  {totalMarginUsed > 0 ? `${((totalMarginUsed / (totalMarginUsed + totalMarginAvailable)) * 100).toFixed(1)}% utilized` : 'No margin used'}
                </p>
              </div>
              <div className="p-2 bg-orange-100 rounded-md">
                <ChartBarIcon className="w-6 h-6 text-orange-600" />
              </div>
            </div>
          </div>

          <div className="bg-purple-50 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-purple-600">Margin Available</p>
                <p className="text-2xl font-bold text-purple-900">
                  {formatCurrency(totalMarginAvailable)}
                </p>
                <p className="text-xs text-purple-600 mt-1">
                  Ready to trade
                </p>
              </div>
              <div className="p-2 bg-purple-100 rounded-md">
                <ChartBarIcon className="w-6 h-6 text-purple-600" />
              </div>
            </div>
          </div>
        </div>

        {/* Client-wise Details */}
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Client
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Available Funds
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  P&L
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Margin Used
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Margin Available
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Last Update
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {clients.map((client) => {
                const lastUpdate = updateHistory.get(client.id);
                const PnlIcon = getPnlIcon(client.total_pnl);
                
                return (
                  <tr key={client.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div>
                        <div className="text-sm font-medium text-gray-900">{client.name}</div>
                        <div className="text-sm text-gray-500">{client.motilal_client_id}</div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">
                        {formatCurrencyDetailed(client.available_funds)}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        {PnlIcon && <PnlIcon className={`w-4 h-4 mr-1 ${getPnlColor(client.total_pnl)}`} />}
                        <span className={`text-sm font-medium ${getPnlColor(client.total_pnl)}`}>
                          {formatCurrencyDetailed(client.total_pnl)}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {formatCurrencyDetailed(client.margin_used)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {formatCurrencyDetailed(client.margin_available)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {lastUpdate ? new Date(lastUpdate.timestamp).toLocaleTimeString() : 'N/A'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        client.is_active 
                          ? 'bg-green-100 text-green-800' 
                          : 'bg-red-100 text-red-800'
                      }`}>
                        {client.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {clients.length === 0 && (
          <div className="text-center py-8">
            <ExclamationTriangleIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-500">No clients found</p>
            <button
              onClick={fetchInitialData}
              className="mt-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              Retry Loading
            </button>
          </div>
        )}

        {/* Connection Status Warning */}
        {connectionStatus === 'disconnected' && (
          <div className="mt-4 bg-red-50 border border-red-200 rounded-md p-4">
            <div className="flex items-center">
              <ExclamationTriangleIcon className="w-5 h-5 text-red-600 mr-2" />
              <div>
                <p className="text-sm font-medium text-red-800">
                  Connection Lost
                </p>
                <p className="text-sm text-red-600">
                  Real-time updates are currently unavailable. Data may be outdated.
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default RealtimeFunds;