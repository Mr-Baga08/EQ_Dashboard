// frontend/src/components/common/Header.tsx
import React from 'react';
import { useRouter } from 'next/router';

const Header: React.FC = () => {
  const router = useRouter();

  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <h1 className="text-2xl font-bold text-gray-900">
              Multi-Client Trading Platform
            </h1>
            <nav className="flex space-x-4">
              <button
                onClick={() => router.push('/')}
                className={`px-3 py-2 rounded-md text-sm font-medium ${
                  router.pathname === '/' 
                    ? 'bg-blue-100 text-blue-700' 
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                Dashboard
              </button>
            </nav>
          </div>
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-green-400 rounded-full"></div>
              <span className="text-sm text-gray-600">Connected</span>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;