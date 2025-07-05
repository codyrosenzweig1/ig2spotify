// This react component provides a form UI for the user to enter their target instagram handle and 
// start a new run of the pipeline. It manages its own loading, success (run IDF), and error states 
// and shows feedback on screen.

import React, { useState } from 'react';
import { startRun } from '../api';

export default function RunLauncher({ onRunStarted}) {
    const [username, setUsername] = useState(''); // form input state
    const [limit, setLimit] = useState(50); // limit for number of posts to process
    const [loading, setLoading] = useState(false); // spinner state
    const [error, setError] = useState(null); // stores any error messages

    // Handles form submission, starts a new run with the provided username
    const handleSubmit = async (e) => {
        e.preventDefault(); // stops the browesers deaukt oage refresh
        setLoading(true);
        setError(null);

        try {
            const data = await startRun(username.trim(), limit);
            onRunStarted(data.runId);
        } catch (err) {
            setError(err.response?.data?.detail || err.message || 'Failed to start run. Please try again.');
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
                className="mt-1 block w-full border rounded p-2"
                placeholder="e.g. nasa"
                required
              />
            </label>

            <label className="block text-sm font-medium">  
                Number of Reels  
                <select  
                    value={limit}  
                    onChange={(e) => setLimit(Number(e.target.value))}  
                    className="mt-1 block w-full border rounded p-2"  
                >  
                    {[2, 50, 100, 250, 500].map(n => (  
                    <option key={n} value={n}>{n}</option>  
                    ))}  
                </select>  
            </label>  
    
            <button
              type="submit"
              disabled={loading}
              className="bg-blue-600 text-white px-4 py-2 rounded"
            >
              {loading ? 'Starting…' : 'Start Run'}
            </button>
          </form>
    
          {error && (
            <div className="mt-6 p-4 bg-red-100 rounded">
              <p className="font-semibold">❌ Error</p>
              <p>{error}</p>
            </div>
          )}
        </div>
      );
}