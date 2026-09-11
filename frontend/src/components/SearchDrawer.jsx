import React, { useState, useEffect } from 'react';
import { Search, X, MessageSquare, Clock, ChevronRight } from 'lucide-react';

export default function SearchDrawer({ isOpen, onClose, onSelectConversation }) {
  const [searchQuery, setSearchQuery] = useState('');
  const [results, setResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);

  useEffect(() => {
    if (!isOpen) return;

    const performSearch = async () => {
      setIsSearching(true);
      try {
        const res = await fetch(`/api/conversations/search?q=${encodeURIComponent(searchQuery)}`);
        if (res.ok) {
          const data = await res.json();
          setResults(data);
        }
      } catch (err) {
        console.error("Error searching conversations:", err);
      } finally {
        setIsSearching(false);
      }
    };

    const timer = setTimeout(() => {
      performSearch();
    }, 200);

    return () => clearTimeout(timer);
  }, [searchQuery, isOpen]);

  if (!isOpen) return null;

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      background: 'rgba(20, 22, 27, 0.4)',
      backdropFilter: 'blur(4px)',
      display: 'flex',
      alignItems: 'flex-start',
      justifyContent: 'center',
      paddingTop: '80px',
      zIndex: 1000
    }} onClick={onClose}>
      <div style={{
        background: '#ffffff',
        border: '1px solid var(--border-hairline)',
        borderRadius: '20px',
        maxWidth: '640px',
        width: '100%',
        boxShadow: '0 20px 40px rgba(0,0,0,0.12)',
        overflow: 'hidden',
        display: 'flex',
        flexDirection: 'column',
        maxHeight: '70vh'
      }} onClick={(e) => e.stopPropagation()}>
        {/* Search Header Input */}
        <div style={{
          padding: '16px 20px',
          borderBottom: '1px solid var(--border-hairline)',
          display: 'flex',
          alignItems: 'center',
          gap: '12px'
        }}>
          <Search size={18} style={{ color: 'var(--brand-rose)' }} />
          <input
            type="text"
            placeholder="Search past conversations by title or legal content..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            autoFocus
            style={{
              flex: 1,
              border: 'none',
              outline: 'none',
              fontFamily: 'var(--font-body)',
              fontSize: '0.95rem',
              color: 'var(--text-ink)',
              background: 'transparent'
            }}
          />
          <button
            onClick={onClose}
            style={{
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              color: 'var(--text-meta)'
            }}
          >
            <X size={18} />
          </button>
        </div>

        {/* Results List */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '12px 16px' }}>
          {isSearching ? (
            <div style={{ padding: '24px', textAlign: 'center', color: 'var(--text-meta)', fontSize: '0.85rem' }}>
              Searching conversation archives...
            </div>
          ) : results.length === 0 ? (
            <div style={{ padding: '32px 16px', textAlign: 'center', color: 'var(--text-meta)', fontSize: '0.85rem' }}>
              <MessageSquare size={24} style={{ opacity: 0.3, marginBottom: '8px' }} />
              <p>No matching conversations found.</p>
              <p style={{ fontSize: '0.75rem', marginTop: '4px' }}>Try searching for keywords like "lease", "NDA", "penalty", or "deposit".</p>
            </div>
          ) : (
            results.map((item) => (
              <div
                key={item.id}
                onClick={() => {
                  onSelectConversation(item.id);
                  onClose();
                }}
                style={{
                  padding: '12px 16px',
                  borderRadius: '12px',
                  border: '1px solid var(--border-hairline)',
                  marginBottom: '8px',
                  cursor: 'pointer',
                  background: '#ffffff',
                  transition: 'var(--transition-fast)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between'
                }}
                className="related-card"
              >
                <div>
                  <div style={{ fontWeight: 600, fontSize: '0.88rem', color: 'var(--text-ink)', marginBottom: '4px' }}>
                    {item.title}
                  </div>
                  {item.snippet && (
                    <div style={{ fontSize: '0.78rem', color: 'var(--text-meta)', lineHeight: 1.4 }}>
                      {item.snippet}
                    </div>
                  )}
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-meta)', fontFamily: 'var(--font-mono)', marginTop: '4px' }}>
                    {item.message_count} messages • Match: {item.match_type || 'title'}
                  </div>
                </div>
                <ChevronRight size={16} style={{ color: 'var(--text-meta)' }} />
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
