import React from 'react';
import { Link } from 'react-router-dom';
import config from '../../config';

const TopBar = () => {
  return (
    <header className="top-bar">
      <div className="top-bar-brand">
        <h1 className="monospace">Cancer Gene Validation Copilot</h1>
        <span className="version-badge">v1.0</span>
      </div>
      <nav className="top-bar-nav">
        <Link to="/" className="nav-link">Dashboard</Link>
        {config.showAboutPage && <Link to="/about" className="nav-link">About</Link>}
      </nav>
    </header>
  );
};

export default TopBar;
