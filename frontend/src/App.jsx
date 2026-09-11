import React, { useState, useEffect } from 'react';
import { Sparkles, Home, Search, Compass, BookOpen, Layers, UploadCloud, RefreshCw, MessageSquare, Trash2, Plus, FileText } from 'lucide-react';
import DocumentUpload from './components/DocumentUpload';
import DocumentList from './components/DocumentList';
import ChatInterface from './components/ChatInterface';
import SearchDrawer from './components/SearchDrawer';
import ChunkViewerModal from './components/ChunkViewerModal';

export default function App() {
  const [health, setHealth] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [isLoadingSamples, setIsLoadingSamples] = useState(false);
  const [activeCitations, setActiveCitations] = useState([]);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [activeNav, setActiveNav] = useState('search');

  // Conversations & Search state
  const [conversations, setConversations] = useState([]);
  const [currentConvId, setCurrentConvId] = useState(null);
  const [currentConvDetails, setCurrentConvDetails] = useState(null);
  const [searchOpen, setSearchOpen] = useState(false);
  const [selectedChunkModal, setSelectedChunkModal] = useState(null);

  const fetchHealthAndDocs = async () => {
    try {
      const [healthRes, docsRes, convsRes] = await Promise.all([
        fetch('/api/health'),
        fetch('/api/documents'),
        fetch('/api/conversations')
      ]);

      if (healthRes.ok) {
        setHealth(await healthRes.json());
      }
      if (docsRes.ok) {
        setDocuments(await docsRes.json());
      }
      if (convsRes.ok) {
        setConversations(await convsRes.json());
      }
    } catch (err) {
      console.error("Error fetching initial metrics & conversations:", err);
    }
  };

  useEffect(() => {
    fetchHealthAndDocs();
  }, []);

  const loadConversationDetails = async (convId) => {
    try {
      const res = await fetch(`/api/conversations/${convId}`);
      if (res.ok) {
        const data = await res.json();
        setCurrentConvId(convId);
        setCurrentConvDetails(data);
        if (data.messages && data.messages.length > 0) {
          const lastAssistant = [...data.messages].reverse().find(m => m.sender === 'assistant');
          if (lastAssistant && lastAssistant.citations) {
            setActiveCitations(lastAssistant.citations);
          }
        }
      }
    } catch (err) {
      console.error("Failed to load conversation thread:", err);
    }
  };

  const handleNavClick = (navKey) => {
    setActiveNav(navKey);
    if (navKey === 'search') {
      setSearchOpen(true);
    } else if (navKey === 'home') {
      setCurrentConvId(null);
      setCurrentConvDetails(null);
      setActiveCitations([]);
    }
  };

  const handleLoadSamples = async () => {
    setIsLoadingSamples(true);
    try {
      const res = await fetch('/api/load-samples', { method: 'POST' });
      if (res.ok) {
        await fetchHealthAndDocs();
      } else {
        alert("Failed to load sample documents.");
      }
    } catch (err) {
      alert("Network error loading sample documents.");
    } finally {
      setIsLoadingSamples(false);
    }
  };

  const handleResetVectorStore = async () => {
    if (!window.confirm("Are you sure you want to reset the vector store and clear all indexed legal documents?")) {
      return;
    }
    try {
      const res = await fetch('/api/reset', { method: 'POST' });
      if (res.ok) {
        setDocuments([]);
        setActiveCitations([]);
        await fetchHealthAndDocs();
      }
    } catch (err) {
      console.error("Failed to reset vector store:", err);
    }
  };

  const handleDeleteConversation = async (convId, e) => {
    e.stopPropagation();
    if (!window.confirm("Delete this conversation thread?")) return;

    try {
      const res = await fetch(`/api/conversations/${convId}`, { method: 'DELETE' });
      if (res.ok) {
        if (currentConvId === convId) {
          setCurrentConvId(null);
          setCurrentConvDetails(null);
          setActiveCitations([]);
        }
        await fetchHealthAndDocs();
      }
    } catch (err) {
      console.error("Error deleting conversation:", err);
    }
  };

  return (
    <div className="app-shell">
      {/* Chunk Viewer Modal */}
      {selectedChunkModal && (
        <ChunkViewerModal
          citation={selectedChunkModal}
          onClose={() => setSelectedChunkModal(null)}
        />
      )}

      {/* Search Drawer Modal */}
      <SearchDrawer
        isOpen={searchOpen}
        onClose={() => {
          setSearchOpen(false);
          if (activeNav === 'search') setActiveNav('home');
        }}
        onSelectConversation={(convId) => {
          loadConversationDetails(convId);
          setActiveNav('home');
        }}
      />

      {/* Zone 1: Slim 64px Icon Nav Rail with Reactive Active State */}
      <aside className="left-rail">
        <div className="rail-top">
          <div className="rail-logo" title="GroundLex AI Engine" onClick={() => handleNavClick('home')}>
            <Sparkles size={20} />
          </div>

          <button
            className={`rail-icon-btn ${activeNav === 'home' ? 'active' : ''}`}
            onClick={() => handleNavClick('home')}
            title="Home / New Query"
          >
            <Home size={19} />
          </button>

          <button
            className={`rail-icon-btn ${activeNav === 'search' ? 'active' : ''}`}
            onClick={() => handleNavClick('search')}
            title="Search Past Conversations"
          >
            <Search size={19} />
          </button>

          <button
            className={`rail-icon-btn ${activeNav === 'discover' ? 'active' : ''}`}
            onClick={() => handleNavClick('discover')}
            title="Discover Legal Insights"
          >
            <Compass size={19} />
          </button>

          <button
            className={`rail-icon-btn ${activeNav === 'library' ? 'active' : ''}`}
            onClick={() => handleNavClick('library')}
            title="Library / Saved Threads"
          >
            <BookOpen size={19} />
          </button>

          <button
            className={`rail-icon-btn ${activeNav === 'spaces' ? 'active' : ''}`}
            onClick={() => handleNavClick('spaces')}
            title="Spaces / Active Index Registry"
          >
            <Layers size={19} />
          </button>
        </div>

        <div className="rail-bottom">
          <button
            className="rail-icon-btn"
            onClick={() => setShowUploadModal(!showUploadModal)}
            title="Upload Legal PDF Document"
          >
            <UploadCloud size={18} />
          </button>

          <button
            className="rail-icon-btn"
            onClick={handleResetVectorStore}
            title="Reset Vector DB"
          >
            <RefreshCw size={16} />
          </button>

          <div className="user-avatar-pill" title="User Profile">
            GX
          </div>
        </div>
      </aside>

      {/* Zone 2: Centered Max-760px Answer Column / View Panel */}
      <main className="center-zone">
        <div className="answer-column">
          {showUploadModal && (
            <div className="surface-card" style={{ padding: '20px', marginBottom: '24px', background: '#fff', border: '1px solid var(--border-hairline)', borderRadius: '16px' }}>
              <DocumentUpload
                onUploadSuccess={() => {
                  fetchHealthAndDocs();
                  setShowUploadModal(false);
                }}
                onLoadSamples={() => {
                  handleLoadSamples();
                  setShowUploadModal(false);
                }}
                isLoadingSamples={isLoadingSamples}
              />
            </div>
          )}

          {activeNav === 'library' ? (
            <div style={{ padding: '8px 0' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
                <div>
                  <h2 style={{ fontSize: '1.4rem', fontWeight: 700, fontFamily: 'var(--font-heading)', color: 'var(--text-ink)' }}>
                    Saved Conversation History
                  </h2>
                  <p style={{ fontSize: '0.84rem', color: 'var(--text-meta)' }}>
                    Manage and reopen past grounded legal query threads.
                  </p>
                </div>
                <button
                  onClick={() => handleNavClick('home')}
                  style={{
                    background: 'var(--brand-rose)',
                    color: '#fff',
                    border: 'none',
                    padding: '8px 16px',
                    borderRadius: 'var(--radius-chip)',
                    fontSize: '0.84rem',
                    fontWeight: 600,
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px'
                  }}
                >
                  <Plus size={16} /> New Query
                </button>
              </div>

              {conversations.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '40px', background: '#fff', borderRadius: '16px', border: '1px solid var(--border-hairline)' }}>
                  <MessageSquare size={32} style={{ color: 'var(--text-meta)', opacity: 0.4, marginBottom: '10px' }} />
                  <p style={{ fontWeight: 600, color: 'var(--text-ink)' }}>No saved conversations yet.</p>
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                  {conversations.map((conv) => (
                    <div
                      key={conv.id}
                      onClick={() => {
                        loadConversationDetails(conv.id);
                        setActiveNav('home');
                      }}
                      className="related-card"
                      style={{ padding: '16px', borderRadius: '16px', background: '#fff', border: '1px solid var(--border-hairline)' }}
                    >
                      <div style={{ flex: 1, overflow: 'hidden' }}>
                        <div style={{ fontWeight: 600, fontSize: '0.95rem', color: 'var(--text-ink)', marginBottom: '4px' }}>
                          {conv.title}
                        </div>
                        {conv.last_message && (
                          <div style={{ fontSize: '0.82rem', color: 'var(--text-meta)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                            {conv.last_message}
                          </div>
                        )}
                        <div style={{ fontSize: '0.72rem', color: 'var(--text-meta)', fontFamily: 'var(--font-mono)', marginTop: '6px' }}>
                          {conv.message_count} messages • Updated {conv.updated_at ? conv.updated_at.split('T')[0] : 'Today'}
                        </div>
                      </div>

                      <button
                        onClick={(e) => handleDeleteConversation(conv.id, e)}
                        title="Delete conversation"
                        style={{ background: 'none', border: 'none', color: 'var(--text-meta)', cursor: 'pointer', padding: '6px' }}
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ) : activeNav === 'spaces' ? (
            <div style={{ padding: '8px 0' }}>
              <div style={{ marginBottom: '20px' }}>
                <h2 style={{ fontSize: '1.4rem', fontWeight: 700, fontFamily: 'var(--font-heading)', color: 'var(--text-ink)' }}>
                  Active Index Registry
                </h2>
                <p style={{ fontSize: '0.84rem', color: 'var(--text-meta)' }}>
                  Legal contracts and statutory PDF documents currently indexed in ChromaDB vector store.
                </p>
              </div>
              <DocumentList documents={documents} />
            </div>
          ) : (
            <ChatInterface
              hasDocuments={documents.length > 0}
              documents={documents}
              onSampleClick={handleLoadSamples}
              onCitationsUpdate={setActiveCitations}
              health={health}
              onUploadSuccess={fetchHealthAndDocs}
              conversationId={currentConvId}
              conversationTitle={currentConvDetails?.title}
              initialMessages={currentConvDetails?.messages}
              onTitleUpdate={fetchHealthAndDocs}
              onConversationChange={(newId) => {
                fetchHealthAndDocs();
                loadConversationDetails(newId);
              }}
            />
          )}
        </div>
      </main>

      {/* Zone 3: Right Sources Rail (320px) with Distinct PDF & Web Citations */}
      <aside className="sources-rail">
        <div className="sources-rail-title">
          <BookOpen size={15} style={{ color: 'var(--text-meta)' }} />
          <span>Sources ({activeCitations.length > 0 ? activeCitations.length : documents.length})</span>
        </div>

        {activeCitations.length > 0 ? (
          <div style={{ display: 'flex', flexDirection: 'column', flex: 1 }}>
            {activeCitations.map((cit, idx) => {
              const isPdf = cit.doc_name.toLowerCase().endsWith('.pdf');
              const cleanDomain = isPdf ? cit.doc_name : cit.doc_name.toUpperCase().replace('.PDF', '.COM');
              const badgeText = isPdf ? 'PDF' : cit.doc_name.charAt(0).toUpperCase();

              return (
                <div
                  key={idx}
                  className={`source-card ${idx === 0 ? 'active' : ''}`}
                  onClick={() => setSelectedChunkModal(cit)}
                  title="Click to expand full cited clause"
                >
                  <div className="source-card-meta">
                    <div className="source-domain-wrapper">
                      <div
                        className="source-icon-badge"
                        style={{
                          background: isPdf ? 'var(--brand-rose-tint)' : '#f1f5f9',
                          color: isPdf ? 'var(--brand-rose)' : 'var(--text-ink)',
                          fontSize: '0.62rem'
                        }}
                      >
                        {badgeText}
                      </div>
                      <span className="source-domain-tag">{cleanDomain}</span>
                    </div>
                    <div className="source-num-circle">{idx + 1}</div>
                  </div>

                  <div className="source-card-title">
                    {cit.doc_name} {isPdf ? `— Clause (Page ${cit.page_number})` : ''}
                  </div>

                  <div className="source-card-snippet">
                    {cit.snippet}
                  </div>
                </div>
              );
            })}

            <button className="btn-show-all-sources" onClick={() => handleNavClick('spaces')}>
              Show all {documents.length} indexed files
            </button>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', flex: 1 }}>
            {documents.length > 0 ? (
              <div>
                <div style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-meta)', marginBottom: '12px' }}>
                  INDEXED DOCUMENTS ({documents.length})
                </div>
                <DocumentList documents={documents} />
              </div>
            ) : (
              <div style={{ padding: '24px 16px', textAlign: 'center', background: '#fff', borderRadius: '16px', border: '1px solid var(--border-hairline)' }}>
                <UploadCloud size={24} style={{ color: 'var(--brand-rose)', marginBottom: '8px' }} />
                <p style={{ fontSize: '0.88rem', fontWeight: 600, color: 'var(--text-ink)' }}>No Documents Indexed</p>
                <p style={{ fontSize: '0.8rem', color: 'var(--text-meta)', marginTop: '4px', marginBottom: '12px' }}>
                  Upload a legal PDF or load sample contracts to enable grounded retrieval.
                </p>
                <button
                  onClick={handleLoadSamples}
                  disabled={isLoadingSamples}
                  style={{
                    background: 'var(--brand-rose)',
                    color: '#fff',
                    border: 'none',
                    padding: '8px 14px',
                    borderRadius: 'var(--radius-chip)',
                    fontSize: '0.78rem',
                    fontWeight: 600,
                    cursor: 'pointer'
                  }}
                >
                  Load Sample PDFs
                </button>
              </div>
            )}
          </div>
        )}
      </aside>
    </div>
  );
}
