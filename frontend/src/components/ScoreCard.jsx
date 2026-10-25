import React from 'react';
import { TrendingDown, TrendingUp, Minus, AlertCircle } from 'lucide-react';

const ScoreCard = ({ title, score, maxScore = 1, interpretation, color = 'indigo' }) => {
  const percentage = Math.min(Math.abs(score) / Math.abs(maxScore) * 100, 100);
  
  const getColor = () => {
    if (score < -0.5) return 'red';
    if (score < -0.2) return 'orange';
    if (score < 0.2) return 'yellow';
    if (score < 0.5) return 'blue';
    return 'green';
  };

  const getIcon = () => {
    if (score < -0.5) return <TrendingDown className="w-5 h-5 text-red-500" />;
    if (score < 0.2) return <Minus className="w-5 h-5 text-yellow-500" />;
    return <TrendingUp className="w-5 h-5 text-green-500" />;
  };

  const colorMap = {
    red: 'border-red-500 bg-red-50',
    orange: 'border-orange-500 bg-orange-50',
    yellow: 'border-yellow-500 bg-yellow-50',
    blue: 'border-blue-500 bg-blue-50',
    green: 'border-green-500 bg-green-50',
  };

  const textColorMap = {
    red: 'text-red-700',
    orange: 'text-orange-700',
    yellow: 'text-yellow-700',
    blue: 'text-blue-700',
    green: 'text-green-700',
  };

  const currentColor = getColor();

  return (
    <div className={`border-l-4 ${colorMap[currentColor]} bg-white rounded-lg shadow-sm p-4`}>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <div className="flex items-center space-x-2 mt-1">
            {getIcon()}
            <span className={`text-2xl font-bold ${textColorMap[currentColor]}`}>
              {score.toFixed(3)}
            </span>
          </div>
          {interpretation && (
            <p className="text-sm text-gray-500 mt-1">{interpretation}</p>
          )}
        </div>
        <div className="w-16 h-16 relative">
          <svg className="w-16 h-16 transform -rotate-90">
            <circle
              className="text-gray-200"
              strokeWidth="4"
              stroke="currentColor"
              fill="transparent"
              r="28"
              cx="32"
              cy="32"
            />
            <circle
              className={`${currentColor === 'red' ? 'text-red-500' : 
                          currentColor === 'orange' ? 'text-orange-500' :
                          currentColor === 'yellow' ? 'text-yellow-500' :
                          currentColor === 'blue' ? 'text-blue-500' : 
                          'text-green-500'}`}
              strokeWidth="4"
              strokeDasharray={175.93}
              strokeDashoffset={175.93 * (1 - percentage / 100)}
              strokeLinecap="round"
              stroke="currentColor"
              fill="transparent"
              r="28"
              cx="32"
              cy="32"
            />
          </svg>
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="text-xs font-bold">{Math.round(percentage)}%</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ScoreCard;