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
      setMessages(prev => [...prev, { role: 'ai', text: 'Sorry, failed to connect to Gemma.' }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="chat-container">
      <div className="rules-heading subheading">
        <h3>CHAT WITH CLAIM (GEMMA 4)</h3>
      </div>
      
      <div className="chat-messages">
        {messages.length === 0 && (
          <div className="chat-empty">Ask Gemma a question about this claim.</div>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`chat-bubble ${m.role === 'ai' ? 'chat-ai' : 'chat-user'}`}>
            <strong>{m.role === 'ai' ? 'Gemma AI' : 'You'}</strong>
            <p>{m.text}</p>
          </div>
        ))}
        {loading && <div className="chat-bubble chat-ai"><strong>Gemma AI</strong><p>Thinking...</p></div>}
      </div>

      <form onSubmit={handleSend} className="chat-input-form">
        <input 
          type="text" 
          placeholder="e.g., Are these room rent charges normal?" 
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={loading || !claimId}
        />
        <button type="submit" disabled={loading || !claimId || !input.trim()}>Send</button>
      </form>
    </div>
  );
}
