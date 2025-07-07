// src/components/Header.jsx

/**
 * The top navigation bar for ig2spotify.
 * Renders a dark background, app title on the left,
 * and can hold nav items on the right.
 */

import React from 'react';

export default function Header() {
  return (
    <header className="bg-[#191414] text-white py-4 px-6 shadow-md">
      <div className="max-w-4xl mx-auto flex items-center justify-between">
        {/* App title / logo */}
        <h1 className="text-2xl font-bold">ig2spotify</h1>
        {/* Placeholder for nav items */}
        <nav className="space-x-4">
          {/* Example future links: */}
          {/* <a href="/history" className="hover:underline">History</a> */}
          {/* <a href="/help" className="hover:underline">Help</a> */}
        </nav>
      </div>
    </header>
  );
}
