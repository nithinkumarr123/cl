import React from 'react';
import { Activity, Dna, Shield } from 'lucide-react';

const Header = () => {
  return (
    <header className="bg-gradient-to-r from-indigo-700 via-purple-700 to-pink-600 text-white shadow-lg">
      <div className="container mx-auto px-4 py-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="bg-white/20 p-2 rounded-lg">
              <Dna className="w-8 h-8" />
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight">ClinX Clinical</h1>
              <p className="text-sm text-white/80">Variant Effect Research System</p>
            </div>
          </div>
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2 bg-white/10 px-3 py-1.5 rounded-full text-sm">
              <Activity className="w-4 h-4" />
              <span className="hidden sm:inline">v4.0.0</span>
            </div>
            <div className="flex items-center space-x-2 bg-white/10 px-3 py-1.5 rounded-full text-sm">
              <Shield className="w-4 h-4" />
              <span className="hidden sm:inline">Research use</span>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;
