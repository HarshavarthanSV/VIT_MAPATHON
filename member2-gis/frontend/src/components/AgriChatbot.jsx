import React, { useState, useRef, useEffect } from 'react';

const getInitialMessage = (stats, isGemini) => {
  const parcels = stats?.study_area_summary?.total_parcels || 293;
  const area = stats?.study_area_summary?.total_parcels_area_hectares || 171.65;
  const engineText = isGemini ? "Google Gemini 2.5 Flash" : "GeoAI & Google Gemini";
  return [
    {
      sender: 'bot',
      source: isGemini ? 'gemini' : 'local',
      model: isGemini ? 'gemini-2.5-flash' : 'Domain-Rules-Engine',
      text: `Hello! I am your **Agri-AI Geospatial Assistant** 🌾 (powered by **${engineText}**).\n\nI can answer **everything** — from cadastral parcel data, crop acreages, and Sentinel-2 trajectories across **Ambasamudram & Cheranmahadevi (${parcels} parcels • ${Number(area).toFixed(2)} ha)** to crop diseases, fertilizers, canal water management, satellite formulas, Python code, and general knowledge!\n\nHow can I help you today?`
    }
  ];
};

const PROMPT_SUGGESTIONS = [
  "📍 Crop count in PARCEL_0128",
  "🌱 How many crops can be planted in PARCEL_0126?",
  "⚠️ If hazard occurs, what is loss rate for PARCEL_0128?",
  "🌾 Paddy planting capacity & flood loss rate",
  "⏱️ Compare baseline vs peak observation",
  "🍌 Banana fertilizer & Sigatoka advice",
  "💧 Thamirabarani canal water management",
  "📄 How do I download the PDF report?"
];

export default function AgriChatbot({ isOpen, onToggle, onClose, statistics }) {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(false);
  const [geminiActive, setGeminiActive] = useState(false);
  const [showConfigModal, setShowConfigModal] = useState(false);
  const [apiKeyInput, setApiKeyInput] = useState('');
  const [savingKey, setSavingKey] = useState(false);
  const [configMessage, setConfigMessage] = useState(null);
  const messagesEndRef = useRef(null);

  // Check Gemini status on mount
  useEffect(() => {
    const checkStatus = async () => {
      try {
        const storedKey = localStorage.getItem('gemini_api_key');
        if (storedKey) {
          setApiKeyInput(storedKey);
        }
        const res = await fetch('/api/chat/status');
        if (res.ok) {
          const data = await res.json();
          const active = data.gemini_active || !!storedKey;
          setGeminiActive(active);
          setMessages(getInitialMessage(statistics, active));
        } else {
          setMessages(getInitialMessage(statistics, !!storedKey));
        }
      } catch (e) {
        setMessages(getInitialMessage(statistics, false));
      }
    };
    checkStatus();
  }, [statistics]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    if (isOpen) {
      scrollToBottom();
    }
  }, [messages, isOpen]);

  const handleSaveApiKey = async (e) => {
    if (e) e.preventDefault();
    const key = apiKeyInput.trim();
    if (!key) {
      localStorage.removeItem('gemini_api_key');
      setGeminiActive(false);
      setConfigMessage({ type: 'info', text: 'API key cleared. Reverting to local GIS engine.' });
      return;
    }

    setSavingKey(true);
    setConfigMessage(null);
    try {
      localStorage.setItem('gemini_api_key', key);
      const res = await fetch('/api/chat/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ api_key: key, persist: true })
      });
      const data = await res.json();
      if (data.success) {
        setGeminiActive(true);
        setConfigMessage({ type: 'success', text: '✨ Google Gemini 2.5 Flash connected successfully!' });
        setTimeout(() => setShowConfigModal(false), 1400);
      } else {
        setConfigMessage({ type: 'error', text: data.message || 'Failed to save key.' });
      }
    } catch (err) {
      localStorage.setItem('gemini_api_key', key);
      setGeminiActive(true);
      setConfigMessage({ type: 'success', text: 'Key saved locally in browser!' });
      setTimeout(() => setShowConfigModal(false), 1400);
    } finally {
      setSavingKey(false);
    }
  };

  const handleSendMessage = async (textToSend) => {
    const text = textToSend || inputValue;
    if (!text.trim()) return;

    const userMsg = { sender: 'user', text };
    setMessages((prev) => [...prev, userMsg]);
    if (!textToSend) setInputValue('');
    setLoading(true);

    try {
      // Check if user pasted an API key in the chat message
      const keyMatch = text.match(/\b(AIzaSy[A-Za-z0-9_-]{28,45})\b/);
      if (keyMatch) {
        localStorage.setItem('gemini_api_key', keyMatch[1]);
        setGeminiActive(true);
      }

      const storedKey = (keyMatch ? keyMatch[1] : null) || localStorage.getItem('gemini_api_key') || undefined;

      // Extract recent conversation history for multi-turn context
      const history = messages.slice(-6).map((m) => ({
        sender: m.sender,
        text: m.text
      }));

      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: text,
          history: history,
          api_key: storedKey,
          model: 'gemini-2.5-flash'
        })
      });

      if (!response.ok) throw new Error('API communication error');
      const data = await response.json();

      if (data.source === 'gemini' || data.gemini_active) {
        setGeminiActive(true);
      }

      setMessages((prev) => [
        ...prev,
        {
          sender: 'bot',
          text: data.reply,
          source: data.source || 'local',
          model: data.model || 'gemini-2.5-flash'
        }
      ]);
    } catch (err) {
      console.error('Chat error:', err);
      setMessages((prev) => [
        ...prev,
        {
          sender: 'bot',
          source: 'local',
          text: "⚠️ Sorry, I couldn't reach the AI service. Please verify your backend server connection."
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

  // Helper to format markdown nicely (bold, lists, headers, code blocks, dividers)
  const renderFormattedText = (raw) => {
    const lines = (raw || '').split('\n');
    return lines.map((line, idx) => {
      let content = line;

      // Divider
      if (content.trim() === '---') {
        return <hr key={idx} style={{ border: 'none', borderTop: '1px solid #e2e8f0', margin: '8px 0' }} />;
      }

      // Header h3
      if (content.startsWith('### ')) {
        return (
          <div key={idx} style={{ fontWeight: 800, fontSize: '0.92rem', color: '#0f172a', margin: '8px 0 4px' }}>
            {content.replace('### ', '')}
          </div>
        );
      }

      // Header h2
      if (content.startsWith('## ')) {
        return (
          <div key={idx} style={{ fontWeight: 800, fontSize: '0.98rem', color: '#0f172a', margin: '10px 0 4px' }}>
            {content.replace('## ', '')}
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

      // Bold and inline code formatting
      const parts = content.split(/(\*\*.*?\*\*|`.*?`)/g);
      const renderedParts = parts.map((part, pIdx) => {
        if (part.startsWith('**') && part.endsWith('**')) {
          return <strong key={pIdx}>{part.slice(2, -2)}</strong>;
        }
        if (part.startsWith('`') && part.endsWith('`')) {
          return (
            <code
              key={pIdx}
              style={{
                background: '#f1f5f9',
                padding: '1px 5px',
                borderRadius: '4px',
                fontFamily: 'monospace',
                fontSize: '0.85em',
                color: '#0f172a'
              }}
            >
              {part.slice(1, -1)}
            </code>
          );
        }
        return part;
      });

      if (isBullet) {
        return (
          <div key={idx} style={{ paddingLeft: '1rem', position: 'relative', margin: '3px 0' }}>
            <span style={{ position: 'absolute', left: 4, color: '#16a34a' }}>•</span>
            {renderedParts}
          </div>
        );
      }

      if (isNumbered) {
        return (
          <div key={idx} style={{ paddingLeft: '1rem', position: 'relative', margin: '3px 0' }}>
            <span style={{ position: 'absolute', left: 2, fontWeight: 700, color: '#2563eb' }}>›</span>
            {renderedParts}
          </div>
        );
      }

      return (
        <p key={idx} style={{ margin: line ? '4px 0' : '6px 0' }}>
          {renderedParts}
        </p>
      );
    });
  };

  return (
    <>

      {/* Chat Window (when open) */}
      {isOpen && (
        <div className="chatbot-window">
          {/* Header */}
          <div className="chatbot-header">
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <div
                className="chatbot-avatar"
                style={{
                  background: geminiActive ? '#eff6ff' : '#f0fdf4',
                  borderColor: geminiActive ? '#bfdbfe' : '#bbf7d0'
                }}
              >
                {geminiActive ? '✨' : '🌱'}
              </div>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <span className="chatbot-title">Agri-AI Assistant</span>
                  <span
                    className={`chatbot-gemini-pill ${geminiActive ? 'active' : 'idle'}`}
                    onClick={() => setShowConfigModal(true)}
                    title="Click to configure Google Gemini API Key"
                  >
                    {geminiActive ? '✨ Gemini 2.5' : '⚙️ Add Key'}
                  </span>
                </div>
                <div className="chatbot-subtitle">
                  <span
                    className="status-dot"
                    style={{
                      background: geminiActive ? '#2563eb' : '#16a34a',
                      display: 'inline-block',
                      width: 6,
                      height: 6
                    }}
                  />
                  <span>
                    {geminiActive ? 'Gemini Live • Answers Everything' : 'Thamirabarani Basin • Local AI'}
                  </span>
                </div>
              </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <button
                className="chatbot-ctrl-btn"
                onClick={() => setShowConfigModal(true)}
                title="Configure Gemini API Key"
              >
                ⚙️
              </button>
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
                    {m.source === 'gemini' ? (
                      <span style={{ color: '#2563eb', fontWeight: 800 }}>
                        ✨ Gemini 2.5 Flash
                      </span>
                    ) : (
                      <span>🌱 Local GeoAI</span>
                    )}
                  </div>
                )}
                <div className="bubble-text">{renderFormattedText(m.text)}</div>
              </div>
            ))}

            {loading && (
              <div className="chat-bubble bubble-bot">
                <div className="bot-label">
                  <span style={{ color: geminiActive ? '#2563eb' : '#16a34a' }}>
                    {geminiActive ? '✨ Gemini Thinking...' : '🌱 Processing...'}
                  </span>
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
              placeholder={
                geminiActive
                  ? "Ask anything (paddy, weather, code, math, crops)..."
                  : "Ask about paddy yield, temporal NDVI, fertilizers..."
              }
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

      {/* Gemini API Key Configuration Modal */}
      {showConfigModal && (
        <div className="gemini-modal-overlay" onClick={() => setShowConfigModal(false)}>
          <div className="gemini-modal-card" onClick={(e) => e.stopPropagation()}>
            <div className="gemini-modal-header">
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: '1.3rem' }}>✨</span>
                <div>
                  <h3 style={{ margin: 0, fontSize: '1rem', fontWeight: 800, color: '#0f172a' }}>
                    Google Gemini API Settings
                  </h3>
                  <p style={{ margin: 0, fontSize: '0.72rem', color: '#64748b' }}>
                    Real-time AI answering for anything and everything
                  </p>
                </div>
              </div>
              <button
                className="chatbot-ctrl-btn"
                onClick={() => setShowConfigModal(false)}
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleSaveApiKey} style={{ padding: '1rem' }}>
              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: '#334155', marginBottom: '6px' }}>
                  Gemini API Key:
                </label>
                <input
                  type="password"
                  placeholder="AIzaSy..."
                  value={apiKeyInput}
                  onChange={(e) => setApiKeyInput(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '8px 10px',
                    borderRadius: '6px',
                    border: '1px solid #cbd5e1',
                    fontSize: '0.85rem',
                    fontFamily: 'monospace'
                  }}
                />
                <p style={{ fontSize: '0.7rem', color: '#64748b', margin: '6px 0 0' }}>
                  Get your free Gemini API key from{' '}
                  <a
                    href="https://aistudio.google.com/app/apikey"
                    target="_blank"
                    rel="noreferrer"
                    style={{ color: '#2563eb', fontWeight: 600, textDecoration: 'underline' }}
                  >
                    Google AI Studio ↗
                  </a>
                </p>
              </div>

              {configMessage && (
                <div
                  style={{
                    padding: '8px 10px',
                    borderRadius: '6px',
                    fontSize: '0.75rem',
                    marginBottom: '1rem',
                    background: configMessage.type === 'error' ? '#fef2f2' : (configMessage.type === 'success' ? '#f0fdf4' : '#eff6ff'),
                    color: configMessage.type === 'error' ? '#991b1b' : (configMessage.type === 'success' ? '#166534' : '#1e40af'),
                    border: `1px solid ${configMessage.type === 'error' ? '#fecaca' : (configMessage.type === 'success' ? '#bbf7d0' : '#bfdbfe')}`
                  }}
                >
                  {configMessage.text}
                </div>
              )}

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
                <button
                  type="button"
                  onClick={() => {
                    setApiKeyInput('');
                    localStorage.removeItem('gemini_api_key');
                    setGeminiActive(false);
                    setConfigMessage({ type: 'info', text: 'Key cleared.' });
                  }}
                  style={{
                    padding: '6px 12px',
                    fontSize: '0.75rem',
                    background: '#f1f5f9',
                    border: '1px solid #cbd5e1',
                    borderRadius: '6px',
                    color: '#475569',
                    cursor: 'pointer'
                  }}
                >
                  Clear Key
                </button>
                <button
                  type="submit"
                  disabled={savingKey}
                  style={{
                    padding: '6px 14px',
                    fontSize: '0.75rem',
                    fontWeight: 700,
                    background: '#2563eb',
                    border: 'none',
                    borderRadius: '6px',
                    color: '#ffffff',
                    cursor: 'pointer'
                  }}
                >
                  {savingKey ? 'Connecting...' : 'Save & Connect'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
}
