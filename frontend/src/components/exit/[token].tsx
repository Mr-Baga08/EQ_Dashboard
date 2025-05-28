// frontend/src/pages/exit/[token].tsx
import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import Layout from '../../components/common/Layout';
import { tokensApi, tradesApi } from '../../services/api';
import { Token } from '../../types';
import TokenExitTable from '../../components/exit/TokenExitTable';

const TokenExitPage: React.FC = () => {
  const router = useRouter();
  const { token: tokenId } = router.query;
  const [token, setToken] = useState<Token | null>(null);
  const [holders, setHolders] = useState<any[]>([]);
  const [selectedClients, setSelectedClients] = useState<Set<number>>(new Set());
  const [isLoading, setIsLoading] = useState(true);
  const [isExiting, setIsExiting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (tokenId) {
      fetchTokenAndHolders();
    }
  }, [tokenId]);

  const fetchTokenAndHolders = async () => {
    try {
      setIsLoading(true);
      const tokenIdNum = parseInt(tokenId as string);
      
      const [tokenResponse, holdersResponse] = await Promise.all([
        tokensApi.getById(tokenIdNum),
        tokensApi.getHolders(tokenIdNum)
      ]);
      
      setToken(tokenResponse.data);
      setHolders(holdersResponse.data);
      
      // Select all clients by default
      const allClientIds = new Set(holdersResponse.data.map((holder: any) => holder.client.id));
      setSelectedClients(allClientIds);
      
    } catch (error: any) {
      setError(error.response?.data?.detail || 'Failed to fetch token data');
      console.error('Token exit data fetch error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleClientSelection = (clientId: number, selected: boolean) => {
    setSelectedClients(prev => {
      const newSet = new Set(prev);
      if (selected) {
        newSet.add(clientId);
      } else {
        newSet.delete(clientId);
      }
      return newSet;
    });
  };

  const handleSelectAll = () => {
    const allClientIds = new Set(holders.map(holder => holder.client.id));
    setSelectedClients(allClientIds);
  };

  const handleDeselectAll = () => {
    setSelectedClients(new Set());
  };

  const handleBatchExit = async () => {
    if (selectedClients.size === 0) {
      alert('Please select at least one client to exit');
      return;
    }

    if (!confirm(`Are you sure you want to exit positions for ${selectedClients.size} clients?`)) {
      return;
    }

    try {
      setIsExiting(true);
      const tokenIdNum = parseInt(tokenId as string);
      const clientIds = Array.from(selectedClients);
      
      const response = await tradesApi.exitByToken(tokenIdNum, clientIds);
      
      console.log('Batch exit results:', response.data);
      
      // Refresh data
      await fetchTokenAndHolders();
      
      alert(`Successfully processed exit orders for ${response.data.total_trades} trades`);
      
    } catch (error: any) {
      setError(error.response?.data?.detail || 'Failed to execute batch exit');
      console.error('Batch exit error:', error);
    } finally {
      setIsExiting(false);
    }
  };

  if (isLoading) {
    return (
      <Layout>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      </Layout>
    );
  }

  if (error || !token) {
    return (
      <Layout>
        <div className="text-center py-12">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Error</h2>
          <p className="text-gray-600 mb-4">{error || 'Token not found'}</p>
          <button
            onClick={() => router.push('/')}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            Back to Dashboard
          </button>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Exit Positions</h1>
            <p className="text-gray-600">Token: {token.symbol} • Current Price: ₹{token.ltp.toFixed(2)}</p>
          </div>
          <button
            onClick={() => router.push('/')}
            className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700"
          >
            Back to Dashboard
          </button>
        </div>
        
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-md p-4">
            <p className="text-red-800">{error}</p>
          </div>
        )}
        
        {/* Token Exit Management */}
        <TokenExitTable
          token={token}
          holders={holders}
          selectedClients={selectedClients}
          onClientSelection={handleClientSelection}
          onSelectAll={handleSelectAll}
          onDeselectAll={handleDeselectAll}
          onBatchExit={handleBatchExit}
          isExiting={isExiting}
        />
      </div>
    </Layout>
  );
};

export default TokenExitPage;