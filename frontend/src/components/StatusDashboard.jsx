// Displays per-step prgress bars, overall percentage and clip records for a run
import React, { useState, useEffect } from 'react';
import { getStatus } from '../api';
import PipelineSteps from './PipelineSteps';

export default function StatusDashboard({ runId }) {  
  const [status, setStatus] = useState({ steps: {}, records: [] });  
  const [loading, setLoading] = useState(true);  
  const [error, setError] = useState(null);  

  useEffect(() => {  
    let interval;  
    const fetchStatus = async () => {  
      try {  
        const data = await getStatus(runId);  
        setStatus(data);  
        setLoading(false);  
        // Continue polling if any step incomplete  
        const incomplete = Object.values(data.steps).some(s => s.done < s.total);  
        if (incomplete) {  
          interval = setTimeout(fetchStatus, 2000);  
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

    return (  
        <div className="p-4 max-w-lg mx-auto">  
        <h2 className="text-lg font-semibold mb-2">Pipeline Progress</h2>  
        {/* Per-step bars */}  
        <PipelineSteps steps={status.steps} />  

        {/* Detailed records */}  
        {/* <h3 className="font-semibold mb-2">Clip Records</h3> */}  
        <ul className="list-disc list-inside">  
            {status.records.map((rec, idx) => (  
            <li key={idx}>  
                {rec.file_name}: {rec.source} {rec.title && `– ${rec.title}`}  
            </li>  
            ))}  
        </ul>  
        </div>  
    );  
    }  