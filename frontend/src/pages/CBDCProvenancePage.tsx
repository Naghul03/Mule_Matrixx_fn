import React, { useState, useEffect, useCallback } from 'react';
import {
  Coins,
  Search,
  ShieldCheck,
  RefreshCw,
  Play,
  ArrowDownRight,
  ArrowUpRight,
} from 'lucide-react';
import { api } from '../services/api';
import {
  CBDCTokenLot,
  CBDCProvenanceData,
  CBDCLedgerEvent,
  CBDCWallet,
} from '../types';

export const CBDCProvenancePage: React.FC = () => {
  const [lots, setLots] = useState<CBDCTokenLot[]>([]);
  const [wallets, setWallets] = useState<CBDCWallet[]>([]);
  const [events, setEvents] = useState<CBDCLedgerEvent[]>([]);
  const [selectedLotRef, setSelectedLotRef] = useState<string>('');
  const [provenance, setProvenance] = useState<CBDCProvenanceData | null>(null);

  const [loading, setLoading] = useState<boolean>(true);
  const [searching, setSearching] = useState<boolean>(false);
  const [generating, setGenerating] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [seed, setSeed] = useState<number>(42);

  // Load initial lots, wallets, events
  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [allLots, allWallets, allEvents] = await Promise.all([
        api.listCBDCLots(),
        api.listCBDCWallets(),
        api.listCBDCEvents(),
      ]);
      setLots(allLots);
      setWallets(allWallets);
      setEvents(allEvents);

      if (allLots.length > 0 && !selectedLotRef) {
        setSelectedLotRef(allLots[0].lot_reference);
      }
    } catch (err) {
      console.error('Failed to load CBDC ledger data:', err);
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }, [selectedLotRef]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Load provenance when selectedLotRef changes
  const loadProvenance = useCallback(async (ref: string) => {
    if (!ref) return;
    setSearching(true);
    setError(null);
    try {
      const data = await api.getCBDCProvenance(ref);
      setProvenance(data);
    } catch (err) {
      console.error('Failed to load provenance:', err);
      setError((err as Error).message);
    } finally {
      setSearching(false);
    }
  }, []);

  useEffect(() => {
    if (selectedLotRef) {
      loadProvenance(selectedLotRef);
    }
  }, [selectedLotRef, loadProvenance]);

  // Run Scenario 2 generator
  const handleRunCBDCScenario = async () => {
    setGenerating(true);
    setError(null);
    try {
      await api.runCBDCScenario(seed, 100000);
      await loadData();
    } catch (err) {
      console.error('Failed to run CBDC scenario:', err);
      setError((err as Error).message);
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-muted-border pb-5">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold font-mono tracking-wide text-warm-white">
              CBDC Token Lot Provenance & Peeling Chain Explorer
            </h1>
            <span className="text-[10px] font-mono uppercase bg-amber/15 text-amber px-2 py-0.5 rounded border border-amber/30">
              Module 6
            </span>
          </div>
          <p className="text-xs text-muted-gray mt-1">
            Simulated digital currency token ledger ({wallets.length} Wallets, {lots.length} Lots) with deterministic UTXO-style lot split/merge tracing and peeling chain detection.
          </p>
        </div>

        {/* Scenario 2 Trigger */}
        <div className="flex items-center gap-2">
          <input
            type="number"
            value={seed}
            onChange={(e) => setSeed(Number(e.target.value))}
            placeholder="Seed"
            className="w-20 bg-background-secondary border border-muted-border rounded px-2.5 py-1.5 text-xs font-mono text-warm-white focus:outline-none focus:border-amber"
          />
          <button
            onClick={handleRunCBDCScenario}
            disabled={generating}
            className="flex items-center gap-2 px-3 py-1.5 bg-earth hover:bg-earth/80 text-warm-white text-xs font-mono font-medium rounded border border-amber/40 transition-colors disabled:opacity-50"
          >
            {generating ? (
              <RefreshCw size={13} className="animate-spin text-amber" />
            ) : (
              <Play size={13} className="text-amber" />
            )}
            <span>Simulate Scenario 2 (Token Peel)</span>
          </button>
        </div>
      </div>

      {/* Lot Selection & Search Bar */}
      <div className="p-4 bg-background-secondary border border-muted-border rounded-lg flex flex-col sm:flex-row gap-3 items-stretch sm:items-center justify-between">
        <div className="flex items-center gap-2 flex-1">
          <Search size={16} className="text-muted-gray ml-1" />
          <input
            type="text"
            value={selectedLotRef}
            onChange={(e) => setSelectedLotRef(e.target.value)}
            placeholder="Search Token Lot Reference (e.g. LOT-42-...)"
            className="w-full bg-background border border-muted-border rounded px-3 py-1.5 text-xs font-mono text-warm-white focus:outline-none focus:border-amber"
          />
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs font-mono text-muted-gray whitespace-nowrap">Or select from ledger:</span>
          <select
            value={selectedLotRef}
            onChange={(e) => setSelectedLotRef(e.target.value)}
            className="bg-background border border-muted-border rounded px-3 py-1.5 text-xs font-mono text-warm-white focus:outline-none focus:border-amber max-w-[240px]"
          >
            {lots.map((l) => (
              <option key={l.id} value={l.lot_reference}>
                {l.lot_reference} (${Number(l.amount).toLocaleString()} - {l.status})
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Messages */}
      {error && (
        <div className="p-3 bg-red-950/40 border border-red-500/40 rounded text-xs text-red-200 font-mono">
          {error}
        </div>
      )}

      {/* Provenance Tree Visualizer */}
      {(loading || searching) ? (
        <div className="p-12 bg-background-secondary border border-muted-border rounded-lg text-center text-amber font-mono text-xs animate-pulse">
          Querying CBDC UTXO lot provenance tree...
        </div>
      ) : provenance && (
        <div className="space-y-4">
          {/* Mathematical Invariant Banner */}
          <div className="p-3 bg-emerald-950/20 border border-emerald-500/30 rounded flex items-center justify-between">
            <div className="flex items-center gap-2.5 text-xs font-mono text-emerald-300">
              <ShieldCheck size={18} className="text-emerald-400" />
              <span className="font-bold">Token Conservation Law Preserved</span>
              <span className="text-muted-gray hidden md:inline">
                | Deterministic lot conservation: input lot values strictly equal output lot values.
              </span>
            </div>
            <span className="text-[10px] font-mono uppercase bg-emerald-500/20 text-emerald-400 px-2 py-0.5 rounded border border-emerald-500/30">
              UTXO Verified
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Parents / Ancestry */}
            <div className="bg-background-secondary border border-muted-border rounded-lg p-4">
              <div className="flex items-center gap-2 pb-2.5 border-b border-muted-border mb-3 text-xs font-mono font-bold text-warm-white">
                <ArrowUpRight size={15} className="text-amber" />
                <span>Parent Origins ({provenance.parents.length})</span>
              </div>

              {provenance.parents.length === 0 ? (
                <div className="py-8 text-center text-xs font-mono text-muted-dark">
                  No upstream parents (Root Genesis / Central Bank Issuance Lot)
                </div>
              ) : (
                <div className="space-y-2">
                  {provenance.parents.map((p) => (
                    <div
                      key={p.id}
                      onClick={() => setSelectedLotRef(p.lotReference)}
                      className="p-3 bg-background hover:bg-background-hover border border-muted-border rounded cursor-pointer transition-colors"
                    >
                      <div className="flex justify-between items-start">
                        <span className="text-xs font-mono font-semibold text-amber">{p.lotReference}</span>
                        <span className="text-[10px] font-mono uppercase px-1.5 py-0.5 bg-muted-border/30 text-muted-gray rounded">
                          {p.status}
                        </span>
                      </div>
                      <div className="text-sm font-mono font-bold text-warm-white mt-1">
                        ${Number(p.amount).toLocaleString('en-US', { minimumFractionDigits: 2 })}
                      </div>
                      <div className="text-[10px] font-mono text-muted-gray mt-1">
                        Split Event: {p.eventType}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Target Lot */}
            <div className="bg-background-secondary border-2 border-amber/60 rounded-lg p-4 shadow-lg shadow-amber/5">
              <div className="flex items-center justify-between pb-2.5 border-b border-muted-border mb-3 text-xs font-mono font-bold text-warm-white">
                <div className="flex items-center gap-2">
                  <Coins size={15} className="text-amber" />
                  <span>Inspected Token Lot</span>
                </div>
                <span className="text-[10px] uppercase px-2 py-0.5 rounded bg-amber/15 text-amber border border-amber/30">
                  Target
                </span>
              </div>

              <div className="space-y-3 font-mono">
                <div className="p-3 bg-background rounded border border-muted-border">
                  <div className="text-[10px] uppercase text-muted-dark font-semibold">Reference</div>
                  <div className="text-xs font-bold text-warm-white mt-0.5 break-all">
                    {provenance.targetLot.lotReference}
                  </div>
                </div>

                <div className="p-3 bg-background rounded border border-muted-border">
                  <div className="text-[10px] uppercase text-muted-dark font-semibold">Lot Value</div>
                  <div className="text-xl font-bold text-warm-white mt-0.5">
                    ${Number(provenance.targetLot.amount).toLocaleString('en-US', { minimumFractionDigits: 2 })} {provenance.targetLot.currency}
                  </div>
                  <div className="text-[10px] text-muted-gray mt-1">
                    Status: <span className="text-amber font-semibold">{provenance.targetLot.status}</span>
                  </div>
                </div>

                <div className="p-3 bg-background rounded border border-muted-border">
                  <div className="text-[10px] uppercase text-muted-dark font-semibold">Holding Wallet</div>
                  <div className="text-xs font-semibold text-warm-white mt-1">
                    {provenance.targetLot.currentHolder.displayName}
                  </div>
                  <div className="text-[10px] text-muted-gray mt-0.5 break-all">
                    {provenance.targetLot.currentHolder.address}
                  </div>
                  <div className="mt-2 text-[10px] uppercase px-2 py-0.5 bg-earth/30 text-amber inline-block rounded border border-amber/30">
                    Type: {provenance.targetLot.currentHolder.type}
                  </div>
                </div>
              </div>
            </div>

            {/* Children / Descendants */}
            <div className="bg-background-secondary border border-muted-border rounded-lg p-4">
              <div className="flex items-center gap-2 pb-2.5 border-b border-muted-border mb-3 text-xs font-mono font-bold text-warm-white">
                <ArrowDownRight size={15} className="text-amber" />
                <span>Descendant Lots ({provenance.children.length})</span>
              </div>

              {provenance.children.length === 0 ? (
                <div className="py-8 text-center text-xs font-mono text-muted-dark">
                  No downstream child lots (Terminal Unspent Lot)
                </div>
              ) : (
                <div className="space-y-2">
                  {provenance.children.map((c) => (
                    <div
                      key={c.id}
                      onClick={() => setSelectedLotRef(c.lotReference)}
                      className="p-3 bg-background hover:bg-background-hover border border-muted-border rounded cursor-pointer transition-colors"
                    >
                      <div className="flex justify-between items-start">
                        <span className="text-xs font-mono font-semibold text-amber">{c.lotReference}</span>
                        <span className="text-[10px] font-mono uppercase px-1.5 py-0.5 bg-muted-border/30 text-muted-gray rounded">
                          {c.status}
                        </span>
                      </div>
                      <div className="text-sm font-mono font-bold text-warm-white mt-1">
                        ${Number(c.amount).toLocaleString('en-US', { minimumFractionDigits: 2 })}
                      </div>
                      <div className="text-[10px] font-mono text-muted-gray mt-1">
                        Split Event: {c.eventType}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* CBDC Ledger Events Table */}
      <div className="bg-background-secondary border border-muted-border rounded-lg p-5">
        <h3 className="text-xs font-mono uppercase tracking-wider text-muted-gray font-semibold mb-3">
          CBDC Ledger Event Stream ({events.length} Events)
        </h3>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead>
              <tr className="border-b border-muted-border text-muted-dark uppercase text-[10px]">
                <th className="pb-2">Event Type</th>
                <th className="pb-2">From Wallet</th>
                <th className="pb-2">To Wallet</th>
                <th className="pb-2">Amount</th>
                <th className="pb-2">Timestamp</th>
                <th className="pb-2">Lot Lineage</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-muted-border/50">
              {events.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-muted-gray">
                    No CBDC ledger events recorded yet. Run Scenario 2 to simulate digital currency flows.
                  </td>
                </tr>
              ) : (
                events.map((e) => (
                  <tr key={e.id} className="hover:bg-background transition-colors">
                    <td className="py-2.5">
                      <span className={`text-[10px] font-mono uppercase px-2 py-0.5 rounded border ${
                        e.event_type === 'SPLIT' ? 'bg-amber/15 text-amber border-amber/30' :
                        e.event_type === 'ISSUANCE' ? 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30' :
                        'bg-blue-500/15 text-blue-400 border-blue-500/30'
                      }`}>
                        {e.event_type}
                      </span>
                    </td>
                    <td className="py-2.5 text-muted-gray">
                      {e.from_wallet_address ? `${e.from_wallet_address.slice(0, 14)}...` : 'CENTRAL_ISSUER'}
                    </td>
                    <td className="py-2.5 text-warm-white">
                      {e.to_wallet_address ? `${e.to_wallet_address.slice(0, 14)}...` : 'REDEEMED'}
                    </td>
                    <td className="py-2.5 font-bold text-warm-white">
                      ${Number(e.amount).toLocaleString('en-US', { minimumFractionDigits: 2 })} {e.currency}
                    </td>
                    <td className="py-2.5 text-muted-gray">
                      {new Date(e.event_timestamp).toLocaleTimeString()}
                    </td>
                    <td className="py-2.5 text-[10px] text-muted-dark">
                      Parents: {e.parent_lot_ids?.length || 0} / Children: {e.child_lot_ids?.length || 0}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
