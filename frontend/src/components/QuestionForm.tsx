import React, { useState } from 'react';

interface QuestionFormProps {
  onSubmit: (question: string) => void;
  isLoading: boolean;
}

const QuestionForm: React.FC<QuestionFormProps> = ({ onSubmit, isLoading }) => {
  const [question, setQuestion] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (question.trim()) {
      onSubmit(question);
    }
  };

  const exampleQuestions = [
    "What is the current price of Bitcoin?",
    "Tell me about Ethereum's history",
    "How does Chromia's blockchain work?",
    "Compare Solana and Cardano",
    "What are the use cases for NEAR Protocol?"
  ];

  const handleExampleClick = (q: string) => {
    setQuestion(q);
    onSubmit(q);
  };

  return (
    <div className="card">
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="question">Ask a question about cryptocurrencies:</label>
          <textarea 
            id="question" 
            rows={3} 
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Example: What is the current price of Bitcoin?"
            disabled={isLoading}
          />
        </div>
        <button type="submit" disabled={!question.trim() || isLoading}>
          {isLoading ? 'Loading...' : 'Ask Question'}
        </button>
      </form>

      <div style={{ marginTop: '1rem' }}>
        <p><strong>Try these examples:</strong></p>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginTop: '0.5rem' }}>
          {exampleQuestions.map((q, idx) => (
            <button 
              key={idx}
              onClick={() => handleExampleClick(q)}
              style={{ 
                fontSize: '0.8rem', 
                padding: '0.4rem 0.8rem', 
                backgroundColor: 'var(--background-color)',
                color: 'var(--text-color)',
                border: '1px solid var(--border-color)'
              }}
              disabled={isLoading}
            >
              {q}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};

export default QuestionForm; 