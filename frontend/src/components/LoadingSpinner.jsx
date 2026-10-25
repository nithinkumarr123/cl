import React from 'react';

const LoadingSpinner = () => {
  return (
    <div className="flex flex-col items-center justify-center py-12">
      <div className="relative">
        <div className="w-16 h-16 border-4 border-indigo-200 rounded-full animate-spin border-t-indigo-600"></div>
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="w-8 h-8 border-4 border-purple-200 rounded-full animate-spin border-t-purple-600" style={{ animationDuration: '0.8s' }}></div>
        </div>
      </div>
      <p className="mt-4 text-gray-600 font-medium">Analyzing variant with AI models...</p>
      <p className="text-sm text-gray-400">This may take a few seconds</p>
    </div>
  );
};

export default LoadingSpinner;