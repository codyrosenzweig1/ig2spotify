// src/components/PipelineSteps.jsx
import React from 'react';

const steps = [
  "Downloading Reels",
  "Recognising Audio",
  "Logging into Spotify",
  "Adding Tracks to Playlist",
];

export default function PipelineSteps({ currentStep }) {
  return (
    <div className="mt-8 space-y-4">
      {steps.map((step, index) => (
        <div key={index} className="flex items-center space-x-4">
          <div
            className={`h-3 w-3 rounded-full ${
              index <= currentStep ? 'bg-green-500' : 'bg-gray-300'
            }`}
          ></div>
          <div
            className={`text-lg ${
              index === currentStep
                ? 'font-bold text-black'
                : index < currentStep
                ? 'text-gray-600'
                : 'text-gray-400'
            }`}
          >
            {step}
          </div>
        </div>
      ))}
    </div>
  );
}
