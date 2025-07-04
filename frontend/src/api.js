// Here we wrap http calls to our backend FastAPI
// It centralises API url configuration and exposes functions like startRun so components
// do'nt need to know endpoints or headers

import axios from 'axios';

// Base url for the FASTAPI backend
const API_BASE = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';

/**
 * Kick off a new ig2spotify pipieline run for the given username 
 * @param {string} username - The Spotify username to process
 * @returns {Promise<{ message: string, run_id: string }>} - A promise that resolves to the response from the API
 */

export function startRun(instagramUsername) {
    return axios
    .post(
        `${API_BASE}/api/run`,
    { instagram_username: instagramUsername }
).then(res => res.data);
}


/**
 * Poll the backend for the status of a run
 * @param {string} runId - The ID of the run to check
 * @returns {Promise<{ run_id: string, processed: number, total: number, records: object[]}>}
 */

export function getStatus(runID) {
    return axios
        .get(`${API_BASE}/api/runs/${run_id}/status`)
        .then(res => res.data);
}


