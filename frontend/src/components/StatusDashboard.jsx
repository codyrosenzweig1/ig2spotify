import React, { useState, useEffect } from 'react';
import { getStatus } from '../api';

export default function StatusDashboard({ runId }) {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let interval;

    const fetchStatus = async () => {
      try {
        const data = await getStatus(runId);
        setStatus(data);
        setLoading(false);

        if (!data.playlist_done) {
          interval = setTimeout(fetchStatus, 10000);
        }
      } catch (err) {
        setError(err.message || 'Failed to fetch status');
        setLoading(false);
      }
    };

    fetchStatus();

    return () => clearTimeout(interval);
  }, [runId]);

  if (loading) return <p>Loading status...</p>;
  if (error) return <p className="text-red-600">{error}</p>;

  const {
    reels_downloaded,
    audio_converted,
    track_recognition_processed,
    tracks_matched,
    playlist_done,
    limit,
    instagram_username,
    playlist_name,
  } = status;

  return (
    <div className="p-4 max-w-lg mx-auto">
      <h2 className="text-lg font-semibold mb-4">Pipeline Progress</h2>

      <p><strong>Instagram User:</strong> {instagram_username}</p>
      <p><strong>Playlist:</strong> {playlist_name}</p>
      <p><strong>Limit:</strong> {limit}</p>

      {/* Progress bars */}
      <ProgressBar label="Reels Downloaded" current={reels_downloaded} total={limit} />
      <ProgressBar label="Tracks Recognised" current={track_recognition_processed} total={limit} />

      <p className="mt-4">
        {playlist_done ? '🎉 Playlist update complete!' : '⏳ Processing...'}
      </p>
      {status.playlist_url && (
      <div className="mt-4">
        <a href={status.playlist_url} target="_blank" rel="noopener noreferrer" className="text-blue-400 underline">
          🎧 View Spotify Playlist
        </a>
      </div>
      )}
      <p>
        {playlist_done ? "✅ Successfully matched " + tracks_matched + " tracks." : ""}
      </p>
    </div>
  );
}

function ProgressBar({ label, current, total }) {
  const percentage = Math.min((current / total) * 100, 100);

  return (
    <div className="mb-4">
      <p className="font-medium mb-1">{label}: {current} / {total}</p>
      <div className="w-full bg-gray-700 rounded-full h-2">
        <div
          className="bg-green-500 h-2 rounded-full"
          style={{ width: `${percentage}%` }}
        ></div>
      </div>
    </div>
  );
}
