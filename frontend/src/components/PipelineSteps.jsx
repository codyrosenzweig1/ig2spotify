// Renders each pipeline stage with its own progress bar.
// Greyed out until start. Highlights current stage, bolds when complete

import React from 'react';

const STEPS = [
    { key: 'download', label: 'Download Reels'},
    { key: 'convert', label: 'Trim & Convert'},
    { key: 'recognise', label: 'Recognise Audio' },  
    { key: 'search',    label: 'Search Spotify' },  
    { key: 'add',       label: 'Add to Playlist' },  
];

export function PipelineSteps({ steps }) {
    return (  
        <div className="space-y-6 mb-6">  
          {STEPS.map(({ key, label }) => {  
            const { done = 0, total = 0 } = steps[key] || {};  
            const pct = total > 0 ? Math.round((done / total) * 100) : 0;  
            const isDone = done >= total && total > 0;  
            const isActive = done > 0 && done < total;  
            const className = isDone  
              ? 'font-bold text-black'  
              : isActive  
                ? 'font-semibold text-blue-600'  
                : 'text-gray-400';  
            return (  
              <div key={key}>  
                <p className={className}>{label}</p>  
                <div className="w-full bg-gray-200 rounded-full h-2 mt-1">  
                  <div  
                    className={`h-2 rounded-full ${isDone ? 'bg-green-600' : isActive ? 'bg-blue-500' : 'bg-gray-300'}`}  
                    style={{ width: `${pct}%` }}  
                  />  
                </div>  
              </div>  
            );  
          })}  
        </div>  
    );  
}