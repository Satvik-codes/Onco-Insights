import React from 'react';
import { Link } from 'react-router-dom';
import TopBar from './TopBar';
import Sidebar from './Sidebar';

const AppShell = ({ children }) => {
  return (
    <div className="app-shell">
      <TopBar />
      <div className="app-body">
        <Sidebar />
        <main className="app-main-content">
          {children}
        </main>
      </div>
    </div>
  );
};

export default AppShell;
