import React from 'react';
import { Link } from 'react-router-dom';
import { AlertTriangle, ArrowLeft } from 'lucide-react';
import { Button } from '../components/common/Button';

export const NotFoundPage: React.FC = () => {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] text-center p-6">
      <div className="w-14 h-14 rounded-full bg-earth/20 flex items-center justify-center text-amber mb-4 border border-earth/40">
        <AlertTriangle size={24} />
      </div>
      <h1 className="text-xl font-bold font-mono text-warm-white uppercase tracking-wider mb-2">
        404 — Endpoint Not Found
      </h1>
      <p className="text-xs text-muted-gray max-w-sm mb-6">
        The requested financial intelligence route does not exist in the registered navigation structure.
      </p>
      <Link to="/current-money/overview">
        <Button variant="secondary" size="sm" className="font-mono text-xs">
          <ArrowLeft size={14} />
          <span>Return to Overview</span>
        </Button>
      </Link>
    </div>
  );
};

