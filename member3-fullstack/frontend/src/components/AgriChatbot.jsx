import React, { useState, useRef, useEffect } from 'react';

const INITIAL_MESSAGES = [
  {
    sender: 'bot',
    text: "Hello! I am your **Agri-AI Geospatial Assistant** 🌾.\n\nI can analyze cadastral parcels across **Ambasamudram & Cheranmahadevi (293 parcels • 171.65 ha)**, compare seasonal Sentinel-2 trajectories, or suggest interventions for your next cultivation cycle.\n\nHow can I help you today?"
  }
];

const PROMPT_SUGGESTIONS = [
  "⏱️ Compare Kuruvai vs Samba season",
  "🌾 How to improve paddy yield in Ambasamudram?",
  "🍌 Banana fertilizer & Sigatoka advice",
  "💧 Thamirabarani canal water management",
  "📄 How do I download the PDF report?"
];

export default function AgriChatbot({ isOpen, onToggle, onClose }) {
  const [messages, setMessages] = useState(INITIAL_MESSAGES);
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    if (isOpen) {
      scrollToBottom();
    }
  }, [messages, isOpen]);

  const handleSendMessage = async (textToSend) => {
    const text = textToSend || inputValue;
    if (!text.trim()) return;

    const userMsg = { sender: 'user', text };
    setMessages((prev) => [...prev, userMsg]);
    if (!textToSend) setInputValue('');
    setLoading(true);

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text })
      });

      if (!response.ok) throw new Error('API communication error');
      const data = await response.json();

      setMessages((prev) => [...prev, { sender: 'bot', text: data.reply }]);
    } catch (err) {
      console.error('Chat error:', err);
      setMessages((prev) => [
        ...prev,
        {
          sender: 'bot',
          text: "⚠️ Sorry, I couldn't reach the Agri-AI service. Please check your backend connection."
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  // Helper to format basic markdown (bold, lists, newlines)
  const renderFormattedText = (raw) => {
    const lines = raw.split('\n');
    return lines.map((line, idx) => {
      let content = line;

      // Header h3
      if (content.startsWith('### ')) {
        return (
          <div key={idx} style={{ fontWeight: 800, fontSize: '0.9rem', color: '#0f172a', margin: '6px 0 3px' }}>
            {content.replace('### ', '')}
          </div>
        );
      }

      // Unordered list
      const isBullet = content.startsWith('- ') || content.startsWith('* ');
      if (isBullet) {
        content = content.replace(/^[-*]\s+/, '');
      }

      // Numbered list
      const isNumbered = /^\d+\.\s+/.test(content);
      if (isNumbered) {
        content = content.replace(/^\d+\.\s+/, '');
      }

      // Bold formatting
      const parts = content.split(/(\*\*.*?\*\*)/g);
      const renderedParts = parts.map((part, pIdx) => {
        if (part.startsWith('**') && part.endsWith('**')) {
          return <strong key={pIdx}>{part.slice(2, -2)}</strong>;
        }
        return part;
      });

      if (isBullet) {
        return (
          <div key={idx} style={{ paddingLeft: '1rem', position: 'relative', margin: '2px 0' }}>
            <span style={{ position: 'absolute', left: 4 }}>•</span>
            {renderedParts}
          </div>
        );
      }

      if (isNumbered) {
        return (
          <div key={idx} style={{ paddingLeft: '1rem', position: 'relative', margin: '2px 0' }}>
            <span style={{ position: 'absolute', left: 2, fontWeight: 700 }}>›</span>
            {renderedParts}
          </div>
        );
      }

      return (
        <p key={idx} style={{ margin: line ? '3px 0' : '6px 0' }}>
          {renderedParts}
        </p>
      );
    });
  };

  return (
    <>
      {/* Floating Toggle Bubble (when closed) */}
      {!isOpen && (
        <button
          className="chatbot-floating-btn"
          onClick={onToggle}
          title="Open Agri-AI Geospatial Assistant"
        >
          <span style={{ fontSize: '1.25rem' }}>🤖</span>
          <span className="chatbot-btn-label">Agri-AI Assistant</span>
          <span className="chatbot-pulse-dot" />
        </button>
      )}

      {/* Chat Window (when open) */}
      {isOpen && (
        <div className="chatbot-window">
          {/* Header */}
          <div className="chatbot-header">
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <div className="chatbot-avatar">🌱</div>
              <div>
                <div className="chatbot-title">Agri-AI Assistant</div>
                <div className="chatbot-subtitle">
                  <span className="status-dot" style={{ background: '#16a34a', display: 'inline-block', width: 6, height: 6 }} />
                  <span>Thamirabarani Basin • Live Context</span>
                </div>
              </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <button
                className="chatbot-ctrl-btn"
                onClick={onClose}
                title="Minimize Chat"
              >
                ✕
              </button>
            </div>
          </div>

          {/* Quick Prompt Pills Bar */}
          <div className="chatbot-suggestions-bar">
            {PROMPT_SUGGESTIONS.map((prompt, idx) => (
              <button
                key={idx}
                className="chatbot-pill"
                onClick={() => handleSendMessage(prompt.replace(/^[^\s]+\s/, ''))}
              >
                {prompt}
              </button>
            ))}
          </div>

          {/* Message History */}
          <div className="chatbot-messages-area">
            {messages.map((m, idx) => (
              <div
                key={idx}
                className={`chat-bubble ${m.sender === 'user' ? 'bubble-user' : 'bubble-bot'}`}
              >
                {m.sender === 'bot' && (
                  <div className="bot-label">
                    <span>🤖 GeoAI</span>
                  </div>
                )}
                <div className="bubble-text">{renderFormattedText(m.text)}</div>
              </div>
            ))}

            {loading && (
              <div className="chat-bubble bubble-bot">
                <div className="bot-label">
                  <span>🤖 GeoAI</span>
                </div>
                <div style={{ display: 'flex', gap: '4px', padding: '6px 0', alignItems: 'center' }}>
                  <span className="chat-typing-dot" />
                  <span className="chat-typing-dot" style={{ animationDelay: '0.2s' }} />
                  <span className="chat-typing-dot" style={{ animationDelay: '0.4s' }} />
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input Box */}
          <div className="chatbot-input-bar">
            <input
              type="text"
              placeholder="Ask about paddy yield, temporal NDVI, fertilizers..."
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              className="chatbot-input"
              disabled={loading}
            />
            <button
              onClick={() => handleSendMessage()}
              disabled={loading || !inputValue.trim()}
              className="chatbot-send-btn"
              title="Send Message"
            >
              ➤
            </button>
          </div>
        </div>
      )}
    </>
  );
}
