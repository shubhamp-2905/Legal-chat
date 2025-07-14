import React, { useState } from 'react';
import { Send, Scale, AlertCircle, CheckCircle } from 'lucide-react';
import './LegalAIChatbot.css';

const LegalAIChatbot = () => {
  const [question, setQuestion] = useState('');
  const [response, setResponse] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  const API_URL = "http://127.0.0.1:8000/ask";

  const handleSubmit = async () => {
    if (!question.trim()) {
      setError('Please enter a question');
      return;
    }

    setLoading(true);
    setError('');
    setSuccess(false);
    setResponse('');

    try {
      const res = await fetch(API_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ question: question.trim() }),
      });

      if (res.ok) {
        const data = await res.json();
        setResponse(data.response);
        setSuccess(true);
      } else {
        setError('Error from backend. Please check server logs.');
      }
    } catch (err) {
      setError('Connection error. Is the backend running?');
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="app-container">
      {/* Header */}
      <header className="header">
        <div className="header-content">
          <div className="header-title">
            <Scale className="scale-icon" />
            <div>
              <h1 className="main-title">Legal AI Chatbot</h1>
              <p className="subtitle">for Indian Law</p>
            </div>
          </div>
          <p className="description">
            Ask any question related to Indian law and get a legal answer backed by real law data.
          </p>
        </div>
      </header>

      {/* Main Content */}
      <main className="main-content">
        {/* Input Section */}
        <div className="input-section">
          <div className="form-group">
            <label htmlFor="question" className="label">
              Your Legal Question:
            </label>
            <textarea
              id="question"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="e.g., What does Section 2 define in the Income Tax Act?"
              className="textarea"
              rows="3"
              disabled={loading}
            />
          </div>
          
          <button
            onClick={handleSubmit}
            disabled={loading || !question.trim()}
            className={`submit-button ${loading || !question.trim() ? 'disabled' : ''}`}
          >
            {loading ? (
              <>
                <div className="spinner"></div>
                Getting Answer...
              </>
            ) : (
              <>
                <Send className="send-icon" />
                Get Answer
              </>
            )}
          </button>
        </div>

        {/* Error Display */}
        {error && (
          <div className="error-container">
            <div className="error-header">
              <AlertCircle className="error-icon" />
              <p className="error-title">Error</p>
            </div>
            <p className="error-message">{error}</p>
          </div>
        )}

        {/* Success Response */}
        {success && response && (
          <div className="success-container">
            <div className="success-header">
              <CheckCircle className="success-icon" />
              <h3 className="success-title">Answer:</h3>
            </div>
            <div className="response-text">
              {response}
            </div>
          </div>
        )}

        {/* Loading State */}
        {loading && (
          <div className="loading-container">
            <div className="loading-content">
              <div className="loading-spinner"></div>
              <p className="loading-text">Getting answer from Legal Bot...</p>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="footer">
        <div className="footer-content">
          <p className="footer-text">
            Made with ❤️ using React and Gemini
          </p>
        </div>
      </footer>
    </div>
  );
};

export default LegalAIChatbot;