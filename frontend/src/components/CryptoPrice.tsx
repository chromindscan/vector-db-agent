import React from 'react';
import { MarketData } from '../types';

interface CryptoPriceProps {
  marketData: MarketData;
}

const CryptoPrice: React.FC<CryptoPriceProps> = ({ marketData }) => {
  if (!marketData.symbol && !marketData.current_price) {
    return null;
  }

  return (
    <div className="price-card">
      <h3>Current Market Data</h3>
      {marketData.symbol && (
        <p><strong>Symbol:</strong> {marketData.symbol}</p>
      )}
      {marketData.current_price && (
        <p><strong>Current Price:</strong> ${marketData.current_price.toLocaleString()}</p>
      )}
    </div>
  );
};

export default CryptoPrice; 