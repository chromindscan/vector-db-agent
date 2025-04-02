import React, { useState } from 'react';
import { addText } from '../api';

interface AddTextFormProps {
  onSuccess?: () => void;
}

const AddTextForm: React.FC<AddTextFormProps> = ({ onSuccess }) => {
  const [text, setText] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [wordCount, setWordCount] = useState(0);

  const MAX_WORDS = 100;

  const handleTextChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const newText = e.target.value;
    const words = newText.trim().split(/\s+/);
    const count = newText.trim() === '' ? 0 : words.length;
    
    setWordCount(count);
    setText(newText);
    setSuccess(false);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!text.trim()) {
      setError('Please enter some text.');
      return;
    }
    
    if (wordCount > MAX_WORDS) {
      setError(`Text exceeds ${MAX_WORDS} words limit.`);
      return;
    }
    
    setIsSubmitting(true);
    setError(null);

    try {
      const response = await addText(text);
      
      if (response.success) {
        setSuccess(true);
        setText('');
        setWordCount(0);
        if (onSuccess) onSuccess();
      } else {
        setError(response.error || 'Failed to add text.');
      }
    } catch (err) {
      setError('Error connecting to server. Please try again.');
      console.error(err);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="card">
      
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="embedText">
            Enter text ({wordCount}/{MAX_WORDS} words):
          </label>
          <textarea
            id="embedText"
            rows={5}
            value={text}
            onChange={handleTextChange}
            placeholder="Enter cryptocurrency knowledge to store in the database..."
            disabled={isSubmitting}
            className={wordCount > MAX_WORDS ? 'text-error' : ''}
          />
          {wordCount > MAX_WORDS && (
            <div className="word-limit-error">
              Exceeds {MAX_WORDS} word limit by {wordCount - MAX_WORDS} words
            </div>
          )}
        </div>
        
        <button 
          type="submit" 
          disabled={isSubmitting || !text.trim() || wordCount > MAX_WORDS}
        >
          {isSubmitting ? 'Adding...' : 'Add to Database'}
        </button>
      </form>
      
      {error && <div className="error-message">{error}</div>}
      {success && <div className="success-message">Text successfully added to the database!</div>}
    </div>
  );
};

export default AddTextForm; 