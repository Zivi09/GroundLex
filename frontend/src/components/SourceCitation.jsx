import React, { useState } from 'react';
import { BookOpen, ChevronDown, ChevronRight, FileText, ExternalLink } from 'lucide-react';

export default function SourceCitation({ citations }) {
  const [isOpen, setIsOpen] = useState(true);

  if (!citations || citations.length === 0) return null;

  return (
    <div className="citations-section">
      <div className="citations-header" onClick={() => setIsOpen(!isOpen)}>
        <BookOpen size={14} />
        <span>Source Citations & Verifiable Context ({citations.length})</span>
        {isOpen ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
      </div>

      {isOpen && (
        <div className="citation-grid">
          {citations.map((cit, idx) => (
            <div key={idx} className="citation-card">
              <div className="citation-meta">
                <div className="citation-source">
                  <FileText size={12} />
                  <span>{cit.doc_name}</span>
                  <span style={{
                    background: 'var(--accent-gold-light)',
                    color: 'var(--accent-gold)',
                    padding: '1px 6px',
                    borderRadius: '4px',
                    fontSize: '0.72rem'
                  }}>
                    Page {cit.page_number}
                  </span>
                </div>
                <span className="citation-score" title="Vector L2 similarity score (lower = closer match)">
                  Score: {cit.score}
                </span>
              </div>
              <p className="citation-text">"{cit.snippet}"</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
