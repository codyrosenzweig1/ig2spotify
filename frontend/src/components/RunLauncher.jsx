import React, { useState } from 'react';
import { startRun } from '../api';  // Your API function

export default function RunLauncher({ onRunStarted }) {
  const [username, setUsername] = useState('');
  const [limit, setLimit] = useState(10);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const data = await startRun(username.trim(), limit);
      console.log("Pipeline started:", data);

      const runId = data.run_id;
      if (runId) {
        onRunStarted(runId, limit);
      } else {
        console.error("No runId returned from backend!");
        setError("Unexpected response from server.");
      }
    } catch (err) {
      console.error("Error starting pipeline:", err);
      setError(err.response?.data?.detail || err.message || 'Failed to start run.');
    } finally {
      setLoading(false);
    }
  };



  return (
    <div className="p-4 max-w-md mx-auto">
      <h1 className="text-xl font-bold mb-4">Start New IG2Spotify Run</h1>
      <form onSubmit={handleSubmit} className="space-y-4">
        <label className="block text-sm font-medium">
          Instagram Username
          <input
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            className="bg-[#121212] text-white border border-gray-500 rounded px-3 py-2 mt-1 w-full"
            placeholder="e.g. nasa"
            required
          />
        </label>

        <label className="block text-sm font-medium">
          Number of Reels
          <select
            value={limit}
            onChange={(e) => setLimit(Number(e.target.value))}
            className="bg-[#121212] text-white border border-gray-500 rounded px-3 py-2 mt-1 w-full"
          >
            {[10, 50, 100, 250, 500].map(n => (
              <option key={n} value={n}>{n}</option>
            ))}
          </select>
        </label>

        <button
          type="submit"
          disabled={loading}
          className="bg-blue-600 text-white px-4 py-2 rounded w-full"
        >
          {loading ? 'Starting…' : 'Start Run'}
        </button>
      </form>

      {error && (
        <div className="mt-6 p-4 bg-red-100 text-red-800 rounded">
          <p className="font-semibold">❌ Error</p>
          <p>{error}</p>
        </div>
      )}
    </div>
  );
}
