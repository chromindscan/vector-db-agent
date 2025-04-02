import React, { useState } from 'react';
import { RelatedAnswer as RelatedAnswerType } from '../types';

interface RelatedAnswersProps {
  relatedAnswers: RelatedAnswerType[];
}

const RelatedAnswers: React.FC<RelatedAnswersProps> = ({ relatedAnswers }) => {
  const [showMore, setShowMore] = useState(false);
  
  if (!relatedAnswers || relatedAnswers.length === 0) {
    return null;
  }

  // Initially show only the first answer
  const displayedAnswers = showMore ? relatedAnswers : relatedAnswers.slice(0, 1);

  return (
    <div className="card">
      <h3>Related Information</h3>
      {displayedAnswers.map((answer, idx) => (
        <div key={idx} className="related-answer">
          <p>{answer.answer}</p>
          <small>Relevance: {(1 - answer.distance).toFixed(2)}</small>
        </div>
      ))}
      {relatedAnswers.length > 1 && (
        <button 
          onClick={() => setShowMore(!showMore)}
          style={{ marginTop: '1rem' }}
        >
          {showMore ? 'Show Less' : `Show ${relatedAnswers.length - 1} More`}
        </button>
      )}
    </div>
  );
};

export default RelatedAnswers; 