// frontend/src/components/dashboard/TokenSelector.tsx
import React, { useState, useEffect } from 'react';
import { MagnifyingGlassIcon } from '@heroicons/react/24/outline';
import { tokensApi } from '../../services/api';
import { useAppStore } from '../../store';
import { Token } from '../../types';

const TokenSelector: React.FC = () => {
  const { 
    tokens, 
    selectedToken, 
    tokenSearchQuery,
    setTokens, 
    setSelectedToken, 
    setTokenSearchQuery,
    setLoading,
    setError 
  } = useAppStore();
  
  const [isOpen, setIsOpen] = useState(false);
  const [searchResults, setSearchResults] = useState<Token[]>([]);

  useEffect(() => {
    if (tokenSearchQuery.length > 0) {
      searchTokens();
    } else {
      setSearchResults([]);
    }
  }, [tokenSearchQuery]);

  const searchTokens = async () => {
    try {
      setLoading(true);
      const response = await tokensApi.search(tokenSearchQuery);
      setSearchResults(response.data);
      setIsOpen(true);
    } catch (error) {
      setError('Failed to search tokens');
      console.error('Token search error:', error);
    } finally {
      setLoading(false);
    }
  };

  const selectToken = (token: Token) => {
    setSelectedToken(token);
    setTokenSearchQuery(token.symbol);
    setIsOpen(false);
  };

  return (
    <div className="relative">
      <label className="block text-sm font-medium text-gray-700 mb-2">
        Select Token
      </label>
      <div className="relative">
        <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
        <input
          type="text"
          value={tokenSearchQuery}
          onChange={(e) => setTokenSearchQuery(e.target.value)}
          onFocus={() => setIsOpen(true)}
          placeholder="Search tokens..."
          className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        />
      </div>
      
      {isOpen && searchResults.length > 0 && (
        <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg max-h-60 overflow-auto">
          {searchResults.map((token) => (
            <button
              key={token.id}
              onClick={() => selectToken(token)}
              className="w-full px-4 py-3 text-left hover:bg-gray-50 border-b border-gray-100 last:border-b-0"
            >
              <div className="flex justify-between items-center">
                <div>
                  <div className="font-medium text-gray-900">{token.symbol}</div>
                  <div className="text-sm text-gray-500">
                    {token.exchange} • {token.instrument_type}
                  </div>
                </div>
                <div className="text-right">
                  <div className="font-medium text-gray-900">₹{token.ltp.toFixed(2)}</div>
                  <div className={`text-sm ${
                    token.ltp > token.close_price ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {((token.ltp - token.close_price) / token.close_price * 100).toFixed(2)}%
                  </div>
                </div>
              </div>
            </button>
          ))}
        </div>
      )}
      
      {selectedToken && (
        <div className="mt-3 p-3 bg-blue-50 border border-blue-200 rounded-md">
          <div className="flex justify-between items-center">
            <div>
              <div className="font-medium text-blue-900">{selectedToken.symbol}</div>
              <div className="text-sm text-blue-700">
                {selectedToken.exchange} • Token ID: {selectedToken.token_id}
              </div>
            </div>
            <div className="text-right">
              <div className="font-bold text-blue-900">₹{selectedToken.ltp.toFixed(2)}</div>
              <div className="text-sm text-blue-700">
                Vol: {selectedToken.volume.toLocaleString()}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TokenSelector;