import React from 'react';
import { Scale, ShieldCheck, Database, RefreshCw } from 'lucide-react';

export default function Navbar({ health, onReset }) {
  const docCount = health?.indexed_documents_count || 0;
  const llmProvider = health?.llm_provider || 'OpenAI';
  const modelName = health?.model_name || 'gpt-4o-mini';

  return (
    <header className="navbar">
      <div className="brand-section">
        <div className="brand-logo">
          <Scale size={22} />
        </div>
        <div>
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <h1 className="brand-title">LexiQuery RAG</h1>
            <span className="brand-badge">Legal Assistant MVP</span>
          </div>
          <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            Grounded Retrieval & Clause Citation Engine
          </p>
        </div>
      </div>

      <div className="nav-stats">
        <div className="stat-pill">
          <Database size={14} style={{ color: 'var(--accent-gold)' }} />
          <span>{docCount} {docCount === 1 ? 'Doc Indexed' : 'Docs Indexed'}</span>
        </div>

        <div className="stat-pill">
          <ShieldCheck size={14} style={{ color: 'var(--accent-emerald)' }} />
          <span style={{ textTransform: 'capitalize' }}>
            {llmProvider}: {modelName}
          </span>
        </div>

        <div className="stat-pill" style={{ background: 'rgba(16, 185, 129, 0.1)' }}>
          <div className="stat-indicator" />
          <span style={{ color: 'var(--accent-emerald)', fontWeight: 600 }}>System Ready</span>
        </div>

        {onReset && (
          <button 
            onClick={onReset}
            title="Reset Vector Store Collection"
            style={{
              background: 'transparent',
              border: '1px solid var(--border-subtle)',
              color: 'var(--text-muted)',
              padding: '6px 10px',
              borderRadius: 'var(--radius-full)',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              fontSize: '0.78rem'
            }}
          >
            <RefreshCw size={12} /> Reset DB
          </button>
        )}
      </div>
    </header>
  );
}
