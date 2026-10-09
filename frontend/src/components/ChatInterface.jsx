import React, { useState } from 'react';
import { sendChat } from '../api';

export default function ChatInterface({ claimId }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim() || !claimId) return;

    const question = input.trim();
    setInput('');
    setMessages(prev => [...prev, { role: 'user', text: question }]);
    setLoading(true);

    try {
      const response = await sendChat(claimId, question);
      setMessages(prev => [...prev, { role: 'ai', text: response.answer }]);
    } catch (err) {
      setMessages(prev => [...prev, { role: 'ai', text: `Could not reach AI: ${err.message}. (GEMINI_API_KEY needed for AI answers.)` }]);
    } finally {
      setLoading(false);
    }
  };

  if (!claimId) return null;

  return (
    <div className="chat-container">
      <div className="rules-heading subheading">
        <h3>CHAT WITH CLAIM AI</h3>
      </div>
      
      <div className="chat-messages">
        {messages.length === 0 && (
          <div className="chat-empty">Ask about this claim — e.g. "Are these room rent charges normal?" or "What's covered under this policy?"</div>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`chat-bubble ${m.role === 'ai' ? 'chat-ai' : 'chat-user'}`}>
            <strong>{m.role === 'ai' ? '🤖 Gemma AI' : '👤 You'}</strong>
            <p>{m.text}</p>
          </div>
        ))}
        {loading && (
          <div className="chat-bubble chat-ai">
            <strong>🤖 Gemma AI</strong>
            <p>Thinking<span style={{ animation: 'none' }}>…</span></p>
          </div>
        )}
      </div>

      <form onSubmit={handleSend} className="chat-input-form">
        <input 
          type="text" 
          id="chat-input"
          placeholder="Ask about this claim..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={loading}
        />
        <button type="submit" id="chat-send-btn" disabled={loading || !input.trim()}>Send</button>
      </form>
    </div>
  );
}
