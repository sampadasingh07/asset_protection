/* ═══════════════════════════════════════════════════════════════════════
   Header — Top bar with search, alerts, and user avatar
   ═══════════════════════════════════════════════════════════════════════ */

import { Search, Bell, Settings, Moon } from 'lucide-react';
import { useState, useRef, useEffect } from 'react';
import { searchAssets, getApiBaseUrl } from '../lib/api';

export default function Header({ unreadCount, criticalCount, onAlertClick, onNavigate }) {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const [showResults, setShowResults] = useState(false);
  const [theme, setTheme] = useState(() => localStorage.getItem('verilens_theme') || 'dark');
  const [showSettingsMenu, setShowSettingsMenu] = useState(false);
  const [showProfileMenu, setShowProfileMenu] = useState(false);
  const searchRef = useRef(null);
  const settingsRef = useRef(null);
  const profileRef = useRef(null);

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('verilens_theme', theme);
  }, [theme]);

  // Handle search
  const handleSearch = async (e) => {
    const query = e.target.value;
    setSearchQuery(query);

    if (query.trim().length < 2) {
      setSearchResults([]);
      setShowResults(false);
      return;
    }

    setIsSearching(true);
    try {
      const results = await searchAssets(query, 10);
      setSearchResults(Array.isArray(results) ? results : []);
      setShowResults(true);
    } catch (error) {
      console.error('Search failed:', error);
      setSearchResults([]);
    } finally {
      setIsSearching(false);
    }
  };

  // Close search results when clicking outside
  useEffect(() => {
    function handleClickOutside(event) {
      if (searchRef.current && !searchRef.current.contains(event.target)) {
        setShowResults(false);
      }
      if (settingsRef.current && !settingsRef.current.contains(event.target)) {
        setShowSettingsMenu(false);
      }
      if (profileRef.current && !profileRef.current.contains(event.target)) {
        setShowProfileMenu(false);
      }
    }

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const toggleTheme = () => {
    setTheme((prev) => (prev === 'dark' ? 'light' : 'dark'));
  };

  const handleCopyApiUrl = async () => {
    try {
      await navigator.clipboard.writeText(getApiBaseUrl());
      setShowSettingsMenu(false);
    } catch (error) {
      console.error('Failed to copy API URL:', error);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('verilens_access_token');
    localStorage.removeItem('access_token');
    window.location.reload();
  };

  return (
    <header className="header">
      <div className="header-left">
        <div className="header-search" ref={searchRef} style={{ position: 'relative' }}>
          <Search size={15} style={{ opacity: 0.4, flexShrink: 0 }} />
          <input
            type="text"
            placeholder="Search assets, accounts, URLs..."
            id="global-search"
            value={searchQuery}
            onChange={handleSearch}
            onFocus={() => searchQuery.trim().length >= 2 && setShowResults(true)}
          />
          <kbd style={{
            fontSize: '0.6rem',
            padding: '2px 6px',
            borderRadius: '4px',
            background: 'var(--bg-surface)',
            border: '1px solid var(--border-subtle)',
            color: 'var(--text-muted)',
            whiteSpace: 'nowrap'
          }}>⌘ K</kbd>

          {/* Search Results Dropdown */}
          {showResults && searchResults.length > 0 && (
            <div style={{
              position: 'absolute',
              top: '100%',
              left: 0,
              right: 0,
              marginTop: '8px',
              background: 'var(--bg-surface)',
              border: '1px solid var(--border-subtle)',
              borderRadius: '8px',
              boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
              maxHeight: '400px',
              overflowY: 'auto',
              zIndex: 100,
            }}>
              {searchResults.slice(0, 10).map((result, idx) => (
                <div
                  key={result.asset_id || result.id || idx}
                  style={{
                    padding: '12px 16px',
                    borderBottom: idx < searchResults.length - 1 ? '1px solid var(--border-subtle)' : 'none',
                    cursor: 'pointer',
                    transition: 'background 0.2s',
                  }}
                  onMouseOver={(e) => e.currentTarget.style.background = 'var(--bg-hover)'}
                  onMouseOut={(e) => e.currentTarget.style.background = 'transparent'}
                >
                  <div style={{ fontSize: '0.9rem', fontWeight: '500' }}>
                    {result.title || result.source_url || 'Unknown Asset'}
                  </div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                    {result.score ? `Score: ${(result.score * 100).toFixed(1)}%` : 'Asset'}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="header-right">
        <button className="header-btn" title="Toggle theme" onClick={toggleTheme}>
          <Moon size={16} />
        </button>

        <div ref={settingsRef} style={{ position: 'relative' }}>
          <button className="header-btn" title="Settings" onClick={() => setShowSettingsMenu((prev) => !prev)}>
            <Settings size={16} />
          </button>

          {showSettingsMenu && (
            <div style={{
              position: 'absolute',
              right: 0,
              top: 'calc(100% + 8px)',
              minWidth: '220px',
              background: 'var(--bg-surface)',
              border: '1px solid var(--border-subtle)',
              borderRadius: '8px',
              boxShadow: '0 8px 24px rgba(0,0,0,0.25)',
              padding: '8px',
              zIndex: 110,
            }}>
              <button className="btn btn-ghost btn-sm" style={{ width: '100%', justifyContent: 'flex-start' }} onClick={handleCopyApiUrl}>
                Copy API Base URL
              </button>
              <button
                className="btn btn-ghost btn-sm"
                style={{ width: '100%', justifyContent: 'flex-start' }}
                onClick={() => {
                  onNavigate?.('health');
                  setShowSettingsMenu(false);
                }}
              >
                Open System Health
              </button>
              <button
                className="btn btn-ghost btn-sm"
                style={{ width: '100%', justifyContent: 'flex-start' }}
                onClick={toggleTheme}
              >
                Switch to {theme === 'dark' ? 'Light' : 'Dark'} Theme
              </button>
            </div>
          )}
        </div>

        <button
          className="header-btn"
          onClick={onAlertClick}
          title={`${unreadCount} unread alerts`}
          id="alert-bell-btn"
        >
          <Bell size={16} />
          {unreadCount > 0 && (
            <span className="header-btn-badge">
              {unreadCount > 99 ? '99+' : unreadCount}
            </span>
          )}
        </button>

        <div ref={profileRef} style={{ position: 'relative' }}>
          <button
            className="header-avatar"
            title="Admin User"
            onClick={() => setShowProfileMenu((prev) => !prev)}
            style={{ border: 'none', cursor: 'pointer' }}
          >
            AD
          </button>

          {showProfileMenu && (
            <div style={{
              position: 'absolute',
              right: 0,
              top: 'calc(100% + 8px)',
              minWidth: '220px',
              background: 'var(--bg-surface)',
              border: '1px solid var(--border-subtle)',
              borderRadius: '8px',
              boxShadow: '0 8px 24px rgba(0,0,0,0.25)',
              padding: '8px',
              zIndex: 110,
            }}>
              <div style={{ padding: '8px 10px', fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                Signed in as
              </div>
              <div style={{ padding: '0 10px 8px', fontSize: '0.88rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                admin@demo.org
              </div>
              <button className="btn btn-ghost btn-sm" style={{ width: '100%', justifyContent: 'flex-start' }} onClick={handleLogout}>
                Log out
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}

