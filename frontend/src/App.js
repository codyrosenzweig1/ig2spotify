// Root component of the react app
// Shows the run launcher or the status dashboard
import React, { useState } from 'react';
import RunLauncher from './components/RunLauncher';
import Header from './components/Header';
import StatusDashboard from './components/StatusDashboard';
import PipelineSteps from './components/PipelineSteps';
import axios from 'axios';


function App() {
  const [runId, setRunId] = useState(null);
  const [currentStep, setCurrentStep] = useState(-1);  // -1 means hidden


  const pollPipelineStatus = (runId, limit) => {
    const interval = setInterval(async () => {
      try {
        const response = await axios.get(`${process.env.REACT_APP_API_BASE}/api/runs/${runId}/status`, {
          params: {
            limit: limit // Pass the limit to the backend
          }
        });

        const status = response.data; // Response from backend

        console.log('Pipeline status:', status);

        // Here we assume the backend sends processed as current completed
        setCurrentStep(status.processed);

        // Stop polling if the run is complete
        if (status.processed >= limit) {
          clearInterval(interval);
        }  
      } catch (error) {
        console.error('Error fetching pipeline status:', error);
        clearInterval(interval);
      }
    }, 2000); // Poll every 2 seconds
  }

  const handleRunStarted = (newRunId, limit) => {
    setRunId(newRunId);
    pollPipelineStatus(newRunId, limit);  // Start simulating steps when a new run starts
  };


  return (
    <div className="min-h-screen bg-[#121212] text-white flex flex-col">
      <Header />

      <main className="flex-1 max-w-4xl mx-auto w-full px-4 py-8 space-y-12">
        {/* Launch form */}
        <div className="bg-[#282828] rounded-lg p-8 shadow-lg">
          <RunLauncher onRunStarted={handleRunStarted} disabled={!!runId} />
        </div>

        {/* Pipeline status (appears once runId is set) */}
        {runId && (
          <div className="bg-[#282828] rounded-lg p-6 shadow-lg">
            <StatusDashboard runId={runId} />
          </div>
        )}

        {/* ✅ Pipeline Steps */}
        <div
          className={`transition-opacity duration-500 ${
            currentStep === -1 ? 'opacity-0' : 'opacity-100'
          }`}
        >
          <PipelineSteps currentStep={currentStep} />
        </div>


      </main>
    </div>
  );
}

export default App;
