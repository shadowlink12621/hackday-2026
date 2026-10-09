import React, { useState } from 'react';
import { chatCase } from '../api';

const SUGGESTED_QUESTIONS = [
  'What is the cataract waiting period?',
  'What does the policy say about room rent?',
  'Are refractive error treatments excluded?',
];

export default function CaseChat({ caseId }) {
  const [q, setQ] = useState('');
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);

  const askQuestion = async (question) => {
    const cleanQuestion = question.trim();
    if (!cleanQuestion || loading) return;

    setLoading(true);
    setQ('');
    setHistory((items) => [...items, { role: 'user', text: cleanQuestion }]);
    try {
      const res = await chatCase(caseId, cleanQuestion);
      setHistory((items) => [...items, {
        role: 'ai',
        text: res.answer,
        citations: res.citations || [],
        isFallback: res.is_fallback || res.model_used === 'offline_mock' || res.model_used === 'retrieval_only',
      }]);
    } catch (err) {
      setHistory((items) => [...items, {
        role: 'ai',
        text: err.message || 'Could not reach the policy assistant. Please try again.',
        error: true,
      }]);
    } finally {
      setLoading(false);
    }
  };

  const handleAsk = (event) => {
    event.preventDefault();
    askQuestion(q);
  };

  return (
    <section className="card policy-chat-card" aria-labelledby="policy-chat-title">
      <div className="policy-chat-heading">
        <div>
          <div className="eyebrow">SOURCE-BASED Q&amp;A</div>
          <h3 id="policy-chat-title">Ask this policy</h3>
          <p>Get answers from indexed policy wording, with page references.</p>
        </div>
        <span className="policy-guide-tag">POLICY ASSISTANT</span>
      </div>

      {history.length === 0 ? (
        <div className="policy-chat-empty">
          <strong>What would you like to check?</strong>
          <div className="policy-question-chips">
            {SUGGESTED_QUESTIONS.map((suggestion) => (
              <button key={suggestion} type="button" onClick={() => askQuestion(suggestion)} disabled={loading}>
                {suggestion}
              </button>
            ))}
          </div>
        </div>
      ) : (
        <div className="chat-messages policy-chat-messages" aria-live="polite">
          {history.map((msg, index) => (
            <article className={`chat-bubble ${msg.role === 'user' ? 'chat-user' : 'chat-ai'}${msg.error ? ' policy-chat-error' : ''}`} key={`${msg.role}-${index}`}>
              <strong>{msg.role === 'user' ? 'You' : 'Policy guide'}</strong>
              <p>{msg.text}</p>
              {msg.citations?.length > 0 && (
                <div className="policy-chat-citations">
                  {msg.citations.map((citation, citationIndex) => (
                    <details className="policy-chat-citation" key={`${citation.page}-${citationIndex}`}>
                      <summary>Source · page {citation.page}</summary>
                      {citation.quote && <p>{citation.quote}</p>}
                    </details>
                  ))}
                </div>
              )}
              {msg.isFallback && <small className="policy-chat-source">Retrieved from indexed policy text</small>}
            </article>
          ))}
          {loading && <div className="policy-chat-thinking" role="status">Checking relevant policy pages…</div>}
        </div>
      )}

      <form onSubmit={handleAsk} className="chat-input-form policy-chat-form">
        <input
          type="text"
          value={q}
          onChange={(event) => setQ(event.target.value)}
          placeholder="Ask about a limit, exclusion, or waiting period…"
          aria-label="Ask a question about this policy"
          disabled={loading}
        />
        <button type="submit" disabled={loading || !q.trim()}>{loading ? 'Checking…' : 'Ask'}</button>
      </form>
      <small className="policy-chat-disclaimer">Guidance only. Confirm coverage and limits against your active policy schedule.</small>
    </section>
  );
}
