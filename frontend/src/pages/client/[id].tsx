// frontend/src/pages/client/[id].tsx
import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import Layout from '../../components/common/Layout';
import { clientsApi, tradesApi } from '../../services/api';
import { Client, Trade } from '../../types';
import ActiveTrades from '../../components/client/ActiveTrades';
import ClientPortfolio from '../../components/client/ClientPortfolio';

const ClientDetailPage: React.FC = () => {
  const router = useRouter();
  const { id } = router.query;
  const [client, setClient] = useState<Client | null>(null);
  const [trades, setTrades] = useState<Trade[]>([]);
  const [portfolio, setPortfolio] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (id) {
      fetchClientData();
    }
  }, [id]);

  const fetchClientData = async () => {
    try {
      setIsLoading(true);
      const clientId = parseInt(id as string);
      
      // Fetch client details, trades, and portfolio concurrently
      const [clientResponse, tradesResponse, portfolioResponse] = await Promise.all([
        clientsApi.getById(clientId),
        tradesApi.getAll({ client_id: clientId }),
        clientsApi.getPortfolio(clientId)
      ]);
      
      setClient(clientResponse.data);
      setTrades(tradesResponse.data);
      setPortfolio(portfolioResponse.data);
      
    } catch (error: any) {
      setError(error.response?.data?.detail || 'Failed to fetch client data');
      console.error('Client data fetch error:', error);
    } finally {
      setIsLoading(false);
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

  if (error || !client) {
    return (
      <Layout>
        <div className="text-center py-12">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Error</h2>
          <p className="text-gray-600 mb-4">{error || 'Client not found'}</p>
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
            <h1 className="text-3xl font-bold text-gray-900">{client.name}</h1>
            <p className="text-gray-600">Client ID: {client.motilal_client_id}</p>
          </div>
          <button
            onClick={() => router.push('/')}
            className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700"
          >
            Back to Dashboard
          </button>
        </div>
        
        {/* Portfolio Overview */}
        <ClientPortfolio client={client} portfolio={portfolio} />
        
        {/* Active Trades */}
        <ActiveTrades trades={trades} onTradeUpdate={fetchClientData} />
      </div>
    </Layout>
  );
};

export default ClientDetailPage;