// Root component of the react app
// Shows the run launcher or the status dashboard
import React, { useState } from 'react';
import RunLauncher from './components/RunLauncher';
import StatusDashboard from './components/StatusDashboard';

function App() {
  const [runId, setrunId] = useState(null);

  return (
    <div className="App">
      {!runId 
        ?<RunLauncher onRunStarted={setrunId} />
        : <StatusDashboard runId={runId} />
      }
    </div>
  );
}

export default App;
