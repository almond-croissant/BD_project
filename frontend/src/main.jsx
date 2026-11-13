import React, { useState } from 'react';
import { createRoot } from 'react-dom/client';
import './styles.css';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

function App() {
  const [query, setQuery] = useState('');
  const [data, setData] = useState(null);
  const [document, setDocument] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  async function search(event) {
    event?.preventDefault();
    if (!query.trim()) return;
    setLoading(true); setError(''); setDocument(null);
    try {
      const response = await fetch(`${API_URL}/search?q=${encodeURIComponent(query)}`);
      if (!response.ok) throw new Error((await response.json()).detail || 'Search failed');
      setData(await response.json());
    } catch (caught) { setError(caught.message); }
    finally { setLoading(false); }
  }

  async function openDocument(id) {
    try { const response = await fetch(`${API_URL}/documents/${encodeURIComponent(id)}`); setDocument(await response.json()); }
    catch { setError('Unable to load this document.'); }
  }

  return <main className="shell">
    <header><div className="mark">A</div><div><p className="eyebrow">UNIVERSITY KNOWLEDGE SEARCH</p><h1>AtlasSearch</h1></div></header>
    <section className="hero"><p className="kicker">Explore the atlas</p><h2>Find the signal in your archive.</h2><p className="subhead">Search across the distributed university collection with transparent, relevance-ranked results.</p>
      <form onSubmit={search} className="searchbar"><input value={query} onChange={e => setQuery(e.target.value)} placeholder="Try “distributed systems”" aria-label="Search"/><button disabled={loading}>{loading ? 'Searching…' : 'Search'}</button></form>
      {error && <div className="error">{error}</div>}
    </section>
    {data && <section className="results"><div className="result-meta"><span>{data.total} result{data.total === 1 ? '' : 's'}</span><span>Index {data.version}</span></div>{data.results.map(result => <article className="card" key={result.id}><p className="result-score">{result.score.toFixed(3)} relevance</p><h3>{result.title}</h3><p>{result.snippet}</p><button className="read" onClick={() => openDocument(result.id)}>Read document →</button></article>)}</section>}
    {document && <div className="modal" onClick={() => setDocument(null)}><article onClick={e => e.stopPropagation()}><button className="close" onClick={() => setDocument(null)}>×</button><p className="eyebrow">DOCUMENT {document.id}</p><h2>{document.title}</h2><p>{document.content}</p></article></div>}
  </main>;
}

createRoot(document.getElementById('root')).render(<App />);
