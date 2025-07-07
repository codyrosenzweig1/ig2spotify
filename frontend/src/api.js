// Here we wrap http calls to our backend FastAPI
// It centralises API url configuration and exposes functions like startRun so components
// do'nt need to know endpoints or headers

import axios from 'axios';

// Base url for the FASTAPI backend
const API_BASE = process.env.REACT_APP_API_BASE;

console.log("API_BASE:", process.env.REACT_APP_API_BASE);


/**
 * Kick off a new ig2spotify pipieline run for the given username 
 * @param {string} username - The Spotify username to process
 * @param {number} limit - The maximum number of posts to process
 * @returns {Promise<{ message: string, runId: string }>} - A promise that resolves to the response from the API
 */

export function startRun(instagramUsername, limit) {
    return axios
    .post(
        `${API_BASE}/api/run`,
    { instagram_username: instagramUsername, limit }
).then(res => res.data);
}


/**
 * Poll the backend for the status of a run
 * @param {string} runId - The ID of the run to check
 * @returns {Promise<{ runId: string, processed: number, total: number, records: object[]}>}
 */

export function getStatus(runId) {
    return axios
        .get(`${API_BASE}/api/runs/${runId}/status`)
        .then(res => {
            const d = res.data;
            // If backend didnt send steps build a single step object
            const steps = d.steps ?? {
                recognise: { done: d.processed, total: d.total },
            }
            return {...d, steps };
        });
}


