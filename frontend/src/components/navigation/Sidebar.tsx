import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import {
  Activity,
  Layers,
  BellRing,
  Briefcase,
  GitGraph,
  BarChart3,
  Coins,
  Shield,
  CircleDollarSign,
  Lock,
} from 'lucide-react';
import { AppSection } from '../../types';

interface SidebarProps {
  currentSection: AppSection;
  onSectionChange: (section: AppSection) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentSection,
  onSectionChange,
}) => {
  const location = useLocation();

  const currentMoneyNav = [
    { name: 'Overview', path: '/current-money/overview', icon: Activity, module: 1, active: true },
    { name: 'Scenarios', path: '/current-money/scenarios', icon: Layers, module: 2, active: true },
    { name: 'Monitoring & Alerts', path: '/current-money/alerts', icon: BellRing, module: 3, active: true },
    { name: 'Cases', path: '/current-money/cases', icon: Briefcase, module: 4, active: true },
    { name: 'Investigation Graph', path: '/current-money/investigation', icon: GitGraph, module: 5, active: true },
    { name: 'Evaluation', path: '/current-money/evaluation', icon: BarChart3, module: 7, active: true },
  ];

  const cbdcNav = [
    { name: 'Overview', path: '/cbdc/overview', icon: Activity, module: 6, active: true },
    { name: 'Scenarios', path: '/cbdc/scenarios', icon: Layers, module: 6, active: true },
    { name: 'Monitoring & Alerts', path: '/cbdc/alerts', icon: BellRing, module: 6, active: true },
    { name: 'Cases', path: '/cbdc/cases', icon: Briefcase, module: 6, active: true },
    { name: 'Investigation Graph', path: '/cbdc/investigation', icon: GitGraph, module: 6, active: true },
    { name: 'Token Provenance', path: '/cbdc/provenance', icon: Coins, module: 6, active: true },
    { name: 'Evaluation', path: '/cbdc/evaluation', icon: BarChart3, module: 7, active: true },
  ];

  const navItems = currentSection === 'current_money' ? currentMoneyNav : cbdcNav;

  return (
    <aside className="w-64 bg-background-secondary border-r border-muted-border flex flex-col flex-shrink-0 select-none">
      {/* Brand Identity */}
      <div className="p-5 border-b border-muted-border">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded bg-earth flex items-center justify-center text-warm-white font-mono font-bold text-sm tracking-wider border border-amber/40 shadow-sm">
            MM
          </div>
          <div>
            <h1 className="font-mono text-sm font-bold tracking-wider text-warm-white uppercase">
              Mule Matrix
            </h1>
            <p className="text-[10px] text-amber tracking-tight font-medium">
              Financial Network Intelligence
            </p>
          </div>
        </div>
        <p className="text-[11px] text-muted-gray mt-3 font-mono italic">
          Follow the Money. Uncover the Network.
        </p>
      </div>

      {/* Dual Section Switcher */}
      <div className="p-3 border-b border-muted-border">
        <div className="text-[10px] uppercase font-mono text-muted-dark font-semibold mb-2 px-1">
          Investigation Domain
        </div>
        <div className="grid grid-cols-2 gap-1 bg-background p-1 rounded border border-muted-border">
          <button
            onClick={() => onSectionChange('current_money')}
            className={`flex items-center justify-center gap-1.5 py-1.5 px-2 rounded text-xs font-mono transition-all ${
              currentSection === 'current_money'
                ? 'bg-earth text-warm-white font-semibold shadow-sm'
                : 'text-muted-gray hover:text-warm-white'
            }`}
          >
            <CircleDollarSign size={13} />
            <span>Current Money</span>
          </button>
          <button
            onClick={() => onSectionChange('cbdc')}
            className={`flex items-center justify-center gap-1.5 py-1.5 px-2 rounded text-xs font-mono transition-all ${
              currentSection === 'cbdc'
                ? 'bg-earth text-warm-white font-semibold shadow-sm'
                : 'text-muted-gray hover:text-warm-white'
            }`}
          >
            <Coins size={13} />
            <span>CBDC</span>
          </button>
        </div>
      </div>

      {/* Section Navigation Links */}
      <nav className="flex-1 overflow-y-auto p-3 space-y-1">
        <div className="text-[10px] uppercase font-mono text-muted-dark font-semibold mb-2 px-2">
          {currentSection === 'current_money' ? 'Bank Transfer Modules' : 'Token Ledger Modules'}
        </div>
        {navItems.map((item) => {
          const Icon = item.icon;
          const isCurrent = location.pathname === item.path;

          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={`flex items-center justify-between px-3 py-2 rounded text-xs font-medium transition-colors ${
                isCurrent
                  ? 'bg-earth/25 text-amber border-l-2 border-amber font-semibold'
                  : 'text-muted-gray hover:text-warm-white hover:bg-background-hover'
              }`}
            >
              <div className="flex items-center gap-2.5">
                <Icon size={15} className={isCurrent ? 'text-amber' : 'text-muted-gray'} />
                <span>{item.name}</span>
              </div>
              {item.active ? (
                <span className="text-[10px] font-mono uppercase bg-amber/15 text-amber px-1.5 py-0.5 rounded border border-amber/30">
                  Ready
                </span>
              ) : (
                <span className="flex items-center gap-1 text-[10px] font-mono text-muted-dark">
                  <Lock size={10} />
                  M{item.module}
                </span>
              )}
            </NavLink>
          );
        })}
      </nav>

      {/* System Baseline Footer */}
      <div className="p-3 border-t border-muted-border bg-background/50">
        <div className="flex items-center gap-2 text-[11px] text-muted-gray font-mono">
          <Shield size={13} className="text-amber" />
          <span>Simulation & Research v0.1.0</span>
        </div>
        <p className="text-[10px] text-muted-dark mt-1 font-mono">
          Modules 1–7 Unified Monolith
        </p>
      </div>
    </aside>
  );
};

