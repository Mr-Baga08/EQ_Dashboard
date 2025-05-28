// frontend/src/pages/index.tsx
import React from 'react';
import Layout from '../components/common/Layout';
import OrderForm from '../components/dashboard/OrderForm';
import { useAppStore } from '../store';

const Dashboard: React.FC = () => {
  const { error, clearError } = useAppStore();

  return (
    <Layout>
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <h1 className="text-3xl font-bold text-gray-900">Trading Dashboard</h1>
          <div className="flex items-center space-x-4">
            <div className="bg-green-100 text-green-800 px-3 py-1 rounded-full text-sm">
              Market Open
            </div>
          </div>
        </div>
        
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-md p-4">
            <div className="flex justify-between items-center">
              <p className="text-red-800">{error}</p>
              <button
                onClick={clearError}
                className="text-red-600 hover:text-red-800"
              >
                ✕
              </button>
            </div>
          </div>
        )}
        
        <OrderForm />
      </div>
    </Layout>
  );
};

export default Dashboard;
