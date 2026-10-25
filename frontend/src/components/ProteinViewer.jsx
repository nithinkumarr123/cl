import React from 'react';

const ProteinViewer = ({ refProtein, altProtein, refAA, altAA, position }) => {
  if (!refProtein && !altProtein) {
    return (
      <div className="text-center py-8 text-gray-400">
        <p>No protein sequence available</p>
      </div>
    );
  }

  const highlightMutation = (sequence, aa, pos) => {
    if (!sequence || !aa || pos === undefined) return sequence;
    
    const parts = sequence.split('');
    const idx = Math.min(pos - 1, parts.length - 1);
    
    if (idx >= 0 && idx < parts.length) {
      parts[idx] = `[${aa}]`;
    }
    
    return parts.join('');
  };

  const refDisplay = refProtein ? highlightMutation(refProtein, refAA, position) : 'N/A';
  const altDisplay = altProtein ? highlightMutation(altProtein, altAA, position) : 'N/A';

  return (
    <div className="bg-white rounded-lg shadow-sm p-4">
      <h4 className="text-sm font-medium text-gray-700 mb-3">Protein Sequences</h4>
      <div className="space-y-3">
        <div>
          <p className="text-xs text-gray-500 mb-1">Reference</p>
          <div className="bg-gray-50 rounded-lg p-3 font-mono text-sm break-all">
            {refDisplay}
          </div>
        </div>
        <div>
          <p className="text-xs text-gray-500 mb-1">Altered</p>
          <div className="bg-yellow-50 rounded-lg p-3 font-mono text-sm break-all border border-yellow-200">
            {altDisplay}
          </div>
        </div>
        {refAA && altAA && position && (
          <div className="flex items-center space-x-2 text-sm bg-indigo-50 p-2 rounded-lg">
            <span className="font-medium text-indigo-700">AA Change:</span>
            <span className="font-mono">{refAA}</span>
            <span className="text-gray-400">→</span>
            <span className="font-mono font-bold text-red-600">{altAA}</span>
            <span className="text-gray-500">at position</span>
            <span className="font-mono font-bold">{position}</span>
          </div>
        )}
      </div>
    </div>
  );
};

export default ProteinViewer;