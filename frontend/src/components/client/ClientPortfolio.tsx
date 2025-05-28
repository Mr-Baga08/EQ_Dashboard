// frontend/src/components/client/ClientPortfolio.tsx
import React from 'react';
import { Client } from '../../types';
import { 
  CurrencyDollarIcon, 
  ArrowUpIcon, 
  ArrowTrendingDownIcon,
  ChartBarIcon 
} from '@heroicons/react/24/outline';

interface ClientPortfolioProps {
  client: Client;
  portfolio: any;
}

const ClientPortfolio: React.FC<ClientPortfolioProps> = ({ client, portfolio }) => {
  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 2,
    }).format(amount);
  };

  const portfolioStats = [
    {
      title: 'Available Funds',
      value: formatCurrency(client.available_funds),
      icon: CurrencyDollarIcon,
      color: 'blue',
    },
    {
      title: 'Total P&L',
      value: formatCurrency(client.total_pnl),
      icon: client.total_pnl >= 0 ? ArrowUpIcon : ArrowTrendingDownIcon,
      color: client.total_pnl >= 0 ? 'green' : 'red',
    },
    {
      title: 'Margin Used',
      value: formatCurrency(client.margin_used),
      icon: ChartBarIcon,
      color: 'orange',
    },
    {
      title: 'Margin Available',
      value: formatCurrency(client.margin_available),
      icon: ChartBarIcon,
      color: 'purple',
    },
  ];

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-xl font-semibold text-gray-900 mb-6">Portfolio Overview</h2>
      
      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {portfolioStats.map((stat) => {
          const Icon = stat.icon;
          return (
            <div key={stat.title} className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center">
                <div className={`p-2 rounded-md bg-${stat.color}-100`}>
                  <Icon className={`w-6 h-6 text-${stat.color}-600`} />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">{stat.title}</p>
                  <p className={`text-lg font-semibold ${
                    stat.color === 'green' ? 'text-green-600' :
                    stat.color === 'red' ? 'text-red-600' :
                    'text-gray-900'
                  }`}>
                    {stat.value}
                  </p>
                </div>
              </div>
            </div>
          );
        })}
      </div>
      
      {/* Portfolio Details */}
      {portfolio && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Positions */}
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-4">Current Positions</h3>
            <div className="space-y-3">
              {portfolio.positions?.map((position: any, index: number) => (
                <div key={index} className="flex justify-between items-center p-3 bg-gray-50 rounded-md">
                  <div>
                    <div className="font-medium text-gray-900">{position.symbol}</div>
                    <div className="text-sm text-gray-600">
                      {position.buyquantity > 0 ? 'Long' : 'Short'} • Qty: {Math.abs(position.buyquantity || position.sellquantity)}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className={`font-medium ${
                      position.marktomarket >= 0 ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {formatCurrency(position.marktomarket || 0)}
                    </div>
                    <div className="text-sm text-gray-600">
                      LTP: ₹{position.LTP || 0}
                    </div>
                  </div>
                </div>
              ))}
              {(!portfolio.positions || portfolio.positions.length === 0) && (
                <p className="text-gray-500 text-center py-4">No positions found</p>
              )}
            </div>
          </div>
          
          {/* Recent Orders */}
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-4">Recent Orders</h3>
            <div className="space-y-3">
              {portfolio.orders?.slice(0, 5).map((order: any, index: number) => (
                <div key={index} className="flex justify-between items-center p-3 bg-gray-50 rounded-md">
                  <div>
                    <div className="font-medium text-gray-900">{order.symbol}</div>
                    <div className="text-sm text-gray-600">
                      {order.buyorsell} • {order.ordertype} • Qty: {order.orderqty}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className={`text-sm font-medium ${
                      order.orderstatus === 'Traded' ? 'text-green-600' :
                      order.orderstatus === 'Rejected' ? 'text-red-600' :
                      'text-yellow-600'
                    }`}>
                      {order.orderstatus}
                    </div>
                    <div className="text-sm text-gray-600">
                      ₹{order.price || 'Market'}
                    </div>
                  </div>
                </div>
              ))}
              {(!portfolio.orders || portfolio.orders.length === 0) && (
                <p className="text-gray-500 text-center py-4">No orders found</p>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ClientPortfolio;