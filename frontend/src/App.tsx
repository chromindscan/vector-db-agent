import React, { useState } from 'react';
import { askQuestion } from './api';
import { CryptoResponse } from './types';
import QuestionForm from './components/QuestionForm';
import RelatedAnswers from './components/RelatedAnswers';
import CryptoPrice from './components/CryptoPrice';
import AddTextForm from './components/AddTextForm';
import './index.css';

// Define tab types
type TabType = 'ask' | 'add';

const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TabType>('ask');
  const [isLoading, setIsLoading] = useState(false);
  const [response, setResponse] = useState<CryptoResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmitQuestion = async (question: string) => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await askQuestion(question);
      setResponse(response);
    } catch (err) {
      setError('Error fetching data. Please try again.');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="container">
      <header className="app-header">
        <h1 className="app-title">Crypto Research Agent</h1>
        <h2 className="app-subtitle">Powered by CoinGecko and Vector DB</h2>
      </header>

      <div className="tabs">
        <button 
          className={`tab ${activeTab === 'ask' ? 'active' : ''}`}
          onClick={() => setActiveTab('ask')}
        >
          Ask Questions
        </button>
        <button 
          className={`tab ${activeTab === 'add' ? 'active' : ''}`}
          onClick={() => setActiveTab('add')}
        >
          Add Knowledge
        </button>
      </div>

      {activeTab === 'ask' && (
        <>
          <QuestionForm onSubmit={handleSubmitQuestion} isLoading={isLoading} />

          {isLoading && <div className="loading"></div>}

          {error && <div className="card" style={{ color: 'red' }}>{error}</div>}

          {response && !isLoading && (
            <div className="response-container">
              {response.market_data && (
                <CryptoPrice marketData={response.market_data} />
              )}

              <div className="card">
                <h3>Answer</h3>
                <p style={{ whiteSpace: 'pre-line' }}>{response.answer}</p>
              </div>

              <RelatedAnswers relatedAnswers={response.related_answers} />
            </div>
          )}
        </>
      )}

      {activeTab === 'add' && (
        <AddTextForm onSuccess={() => {
          // You could add a success notification here
        }} />
      )}

      <footer style={{ textAlign: 'center', marginTop: '2rem', color: '#6c757d' }}>
        <p>Chromia Vector DB Crypto Research Agent © {new Date().getFullYear()}</p>
      </footer>
    </div>
  );
};

export default App; 