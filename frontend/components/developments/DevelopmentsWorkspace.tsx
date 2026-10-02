'use client'

import React, { useState, useEffect, useCallback, useMemo } from 'react'
import Link from 'next/link'
import type { DevelopmentSummary } from '@/types/api'
import { fetchDevelopments } from '@/lib/api'
import { formatError, FormattedError } from '@/lib/errors'
import { SectionTitle, Card, Badge } from '@/components/metaradar'
import { ErrorState } from '../common/ErrorState'
import {
  FlaskConical,
  RefreshCw,
  ChevronRight,
  Zap,
  Search,
  Dna,
  ShieldCheck,
  Building,
  Layers,
  ArrowUpRight,
  Activity,
  Filter,
} from 'lucide-react'

export function DevelopmentsWorkspace() {
  const [developments, setDevelopments] = useState<DevelopmentSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<FormattedError | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedModality, setSelectedModality] = useState<string>('ALL')
  const [selectedStage, setSelectedStage] = useState<string>('ALL')

  const loadDevelopments = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await fetchDevelopments(50)
      setDevelopments(data)
    } catch (err) {
      setError(formatError(err, 'Failed to fetch clinical developments registry.'))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadDevelopments()
  }, [loadDevelopments])

  // Aggregate metrics
  const totalSignals = developments.reduce((acc, d) => acc + (d.signal_count || 0), 0)
  const modalitiesCount = useMemo(() => {
    const s = new Set<string>()
    developments.forEach((d) => {
      if (d.modality) s.add(d.modality)
    })
    return s.size || 3
  }, [developments])

  // Unique modalities & stages for filtering
  const availableModalities = useMemo(() => {
    const mods = new Set<string>()
    developments.forEach((d) => {
      if (d.modality) mods.add(d.modality)
    })
    return Array.from(mods)
  }, [developments])

  // Filtered developments
  const filteredDevelopments = useMemo(() => {
    return developments.filter((d) => {
      const q = searchQuery.toLowerCase().trim()
      const matchesSearch =
        !q ||
        (d.title && d.title.toLowerCase().includes(q)) ||
        (d.asset_name && d.asset_name.toLowerCase().includes(q)) ||
        (d.generic_name && d.generic_name.toLowerCase().includes(q)) ||
        (d.company_name && d.company_name.toLowerCase().includes(q)) ||
        (d.mechanism && d.mechanism.toLowerCase().includes(q)) ||
        (d.indication && d.indication.toLowerCase().includes(q)) ||
        (d.current_stage && d.current_stage.toLowerCase().includes(q))

      const matchesModality =
        selectedModality === 'ALL' ||
        (d.modality && d.modality.toLowerCase().includes(selectedModality.toLowerCase()))

      const matchesStage =
        selectedStage === 'ALL' ||
        (selectedStage === 'APPROVED' &&
          (d.current_stage.toLowerCase().includes('approved') ||
            d.current_stage.toLowerCase().includes('market authorization'))) ||
        (selectedStage === 'PHASE3' && d.current_stage.toLowerCase().includes('phase iii')) ||
        (selectedStage === 'REGULATORY' &&
          (d.current_stage.toLowerCase().includes('regulatory') ||
            d.current_stage.toLowerCase().includes('bla') ||
            d.current_stage.toLowerCase().includes('review')))

      return matchesSearch && matchesModality && matchesStage
    })
  }, [developments, searchQuery, selectedModality, selectedStage])

  return (
    <>
      <SectionTitle
        eyebrow="Asset Tracking & Competitor Pipeline"
        title="Competitive Developments Registry"
        detail="Canonical disease-area development tracks linking clinical trials, regulatory filings, and competitor milestones."
      />

      <div className="kpi-grid">
        <div className="panel kpi">
          <p className="eyebrow">Tracked developments</p>
          <div className="kpi-value">
            <strong style={{ color: 'var(--signal)' }}>{developments.length}</strong>
            <span>Active programs</span>
          </div>
        </div>
        <div className="panel kpi">
          <p className="eyebrow">Indexed evidence</p>
          <div className="kpi-value">
            <strong>{totalSignals}</strong>
            <span>Verified signals</span>
          </div>
        </div>
        <div className="panel kpi">
          <p className="eyebrow">Therapeutic modalities</p>
          <div className="kpi-value">
            <strong style={{ fontSize: '24px' }}>{modalitiesCount} Classes</strong>
            <span>Gene Tx · mAb · RNAi</span>
          </div>
        </div>
        <div className="panel kpi">
          <p className="eyebrow">Pipeline engine</p>
          <div className="kpi-value">
            <strong style={{ color: 'var(--success)' }}>Active</strong>
            <span>FSM v5.1</span>
          </div>
        </div>
      </div>

      {/* Search and Filter Toolbar */}
      <div className="mb-4 flex flex-col gap-3 rounded-lg border border-[var(--border)] bg-[var(--surface-secondary)] p-3.5">
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
          <div className="relative flex-1">
            <Search
              size={15}
              className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--muted-foreground)]"
            />
            <input
              type="text"
              placeholder="Search by asset, sponsor, mechanism, or indication..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full rounded-md border border-[var(--border)] bg-[var(--surface)] py-1.5 pl-9 pr-3 text-xs text-[var(--foreground)] placeholder-[var(--muted-foreground)] outline-none focus:border-[var(--signal)]"
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery('')}
                className="absolute right-2.5 top-1/2 -translate-y-1/2 text-xs text-[var(--muted-foreground)] hover:text-[var(--foreground)]"
              >
                ✕
              </button>
            )}
          </div>

          <div className="flex items-center justify-between sm:justify-end gap-2">
            <span className="text-[11px] text-[var(--muted-foreground)] font-mono">
              {filteredDevelopments.length} / {developments.length} Assets
            </span>
            <button
              onClick={loadDevelopments}
              className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded text-xs border border-[var(--border)] bg-[var(--surface)] text-[var(--foreground)] hover:border-[var(--signal)] shrink-0 transition-colors"
              title="Refresh Registry from Database"
            >
              <RefreshCw size={12} className={loading ? 'animate-spin' : ''} />
              <span className="hidden sm:inline">Refresh</span>
            </button>
          </div>
        </div>

        {/* Modality & Stage Filter Chips */}
        <div className="flex items-center gap-1.5 flex-wrap pt-2 border-t border-[var(--border)] text-[11px]">
          <span className="text-[10px] uppercase font-bold text-[var(--muted-foreground)] mr-1 tracking-wider">
            Modality:
          </span>
          {['ALL', 'Gene Therapy', 'Bispecific', 'RNAi', 'Anti-TFPI'].map((mod) => (
            <button
              key={mod}
              onClick={() => setSelectedModality(mod)}
              className={`px-2.5 py-1 rounded-full text-[10px] font-semibold transition-all border ${
                selectedModality === mod
                  ? 'bg-[var(--signal)] text-[var(--background)] border-[var(--signal)] font-bold shadow-xs'
                  : 'bg-[var(--surface)] text-[var(--muted-foreground)] border-[var(--border)] hover:border-[var(--signal)] hover:text-[var(--foreground)]'
              }`}
            >
              {mod === 'ALL' ? 'All Modalities' : mod}
            </button>
          ))}

          <span className="text-[10px] uppercase font-bold text-[var(--muted-foreground)] ml-2 mr-1 tracking-wider hidden md:inline">
            Stage:
          </span>
          {[
            { id: 'ALL', label: 'All Stages' },
            { id: 'APPROVED', label: 'Approved' },
            { id: 'PHASE3', label: 'Phase III' },
            { id: 'REGULATORY', label: 'In Review' },
          ].map((st) => (
            <button
              key={st.id}
              onClick={() => setSelectedStage(st.id)}
              className={`px-2.5 py-1 rounded-full text-[10px] font-semibold transition-all border ${
                selectedStage === st.id
                  ? 'bg-[var(--foreground)] text-[var(--background)] border-[var(--foreground)] font-bold'
                  : 'bg-[var(--surface)] text-[var(--muted-foreground)] border-[var(--border)] hover:border-[var(--foreground)] hover:text-[var(--foreground)]'
              }`}
            >
              {st.label}
            </button>
          ))}
        </div>
      </div>

      {error && (
        <ErrorState
          title={error.title}
          message={error.message}
          requestId={error.requestId}
          endpoint={error.endpoint}
          statusCode={error.statusCode}
          onRetry={loadDevelopments}
        />
      )}

      {loading && developments.length === 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <Card key={i} className="animate-pulse h-48" />
          ))}
        </div>
      )}

      {!loading && !error && filteredDevelopments.length === 0 && (
        <Card className="empty-state py-12">
          <FlaskConical size={32} className="text-[var(--muted-foreground)] mx-auto mb-2 opacity-60" />
          <p>No matching developments found</p>
          <span>
            {searchQuery || selectedModality !== 'ALL' || selectedStage !== 'ALL'
              ? 'Try adjusting your search criteria or resetting filters.'
              : 'Competitive developments are synthesized automatically when new clinical trials or regulatory filings are ingested.'}
          </span>
          {(searchQuery || selectedModality !== 'ALL' || selectedStage !== 'ALL') && (
            <button
              onClick={() => {
                setSearchQuery('')
                setSelectedModality('ALL')
                setSelectedStage('ALL')
              }}
              className="mt-3 text-xs text-[var(--signal)] underline font-medium"
            >
              Clear all filters
            </button>
          )}
        </Card>
      )}

      {!loading && !error && filteredDevelopments.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filteredDevelopments.map((d) => {
            const isApproved =
              d.current_stage.toLowerCase().includes('approved') ||
              d.current_stage.toLowerCase().includes('authorized')
            const isPhase3 = d.current_stage.toLowerCase().includes('phase iii')

            return (
              <Card
                key={d.development_id}
                className="flex flex-col justify-between hover:border-[var(--signal)] transition-all duration-200 group bg-[var(--surface)] p-4 rounded-xl shadow-xs"
              >
                <div>
                  {/* Top Bar: Asset Badge, Stage, and Signal Count */}
                  <div className="flex items-start justify-between gap-2 mb-2.5">
                    <div className="flex items-center gap-1.5 flex-wrap">
                      <span
                        className={`text-[10px] px-2 py-0.5 rounded-full font-bold uppercase tracking-wider border ${
                          isApproved
                            ? 'bg-[var(--success)]/10 text-[var(--success)] border-[var(--success)]/30'
                            : isPhase3
                            ? 'bg-[var(--primary)]/10 text-[var(--primary)] border-[var(--primary)]/30'
                            : 'bg-[var(--warning)]/10 text-[var(--warning)] border-[var(--warning)]/30'
                        }`}
                      >
                        {d.current_stage}
                      </span>
                      {d.modality && (
                        <span className="text-[10px] px-2 py-0.5 rounded-full font-medium bg-[var(--surface-secondary)] text-[var(--muted-foreground)] border border-[var(--border)]">
                          {d.modality}
                        </span>
                      )}
                    </div>
                    <Link
                      href={`/signals?query=${encodeURIComponent(d.asset_name || d.title)}`}
                      className="inline-flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded-md bg-[var(--surface-secondary)] hover:bg-[var(--surface-hover)] border border-[var(--border)] text-[var(--foreground)] transition-colors shrink-0"
                      title="View all evidence signals for this asset"
                    >
                      <Layers size={11} className="text-[var(--signal)]" />
                      <span>{d.signal_count} signals</span>
                    </Link>
                  </div>

                  {/* Asset Title & Generic Name */}
                  <div className="mb-2.5">
                    <h3 className="text-base font-bold text-[var(--foreground)] m-0 group-hover:text-[var(--signal)] transition-colors flex items-center justify-between">
                      <span>{d.asset_name || d.title}</span>
                      {d.asset_name && d.asset_name !== d.title && (
                        <span className="text-[11px] font-normal text-[var(--muted-foreground)] truncate max-w-[200px]">
                          {d.title}
                        </span>
                      )}
                    </h3>
                    {d.generic_name && (
                      <p className="text-xs text-[var(--muted-foreground)] italic mt-0.5 mb-0">
                        {d.generic_name}
                      </p>
                    )}
                  </div>

                  {/* Mechanism & Indication Details */}
                  <div className="space-y-1.5 my-3 text-xs bg-[var(--surface-secondary)] p-2.5 rounded-md border border-[var(--border)]">
                    {d.mechanism && (
                      <div className="flex items-start gap-1.5">
                        <span className="text-[10px] uppercase font-bold text-[var(--muted-foreground)] shrink-0 mt-0.5">
                          MoA:
                        </span>
                        <span className="text-[var(--foreground)] leading-tight">{d.mechanism}</span>
                      </div>
                    )}
                    {d.indication && (
                      <div className="flex items-start gap-1.5">
                        <span className="text-[10px] uppercase font-bold text-[var(--muted-foreground)] shrink-0 mt-0.5">
                          Indication:
                        </span>
                        <span className="text-[var(--foreground)] leading-tight">{d.indication}</span>
                      </div>
                    )}
                  </div>
                </div>

                {/* Footer: Sponsor, Jurisdiction, and Quick Links */}
                <div className="pt-2.5 border-t border-[var(--border)] mt-1">
                  <div className="flex items-center justify-between text-xs text-[var(--muted-foreground)] mb-2">
                    <div className="flex items-center gap-1 truncate">
                      <Building size={12} className="shrink-0" />
                      <span className="truncate">
                        Sponsor: <strong className="text-[var(--foreground)]">{d.company_name || 'Competitor'}</strong>
                      </span>
                    </div>
                    {d.jurisdiction && (
                      <div className="flex items-center gap-1 shrink-0 text-[11px]">
                        <ShieldCheck size={12} className="text-[var(--success)]" />
                        <span>{d.jurisdiction}</span>
                      </div>
                    )}
                  </div>

                  <div className="flex items-center justify-between gap-2 pt-2 border-t border-[var(--border)] border-dashed text-[11px]">
                    <Link
                      href={`/confluence`}
                      className="inline-flex items-center gap-1 text-[var(--signal)] hover:underline font-medium"
                    >
                      <Zap size={12} />
                      <span>Confluence Stream</span>
                    </Link>
                    <Link
                      href={`/lifecycles`}
                      className="inline-flex items-center gap-1 text-[var(--muted-foreground)] hover:text-[var(--foreground)] transition-colors"
                    >
                      <span>Lifecycle Milestones</span>
                      <ChevronRight size={12} />
                    </Link>
                  </div>
                </div>
              </Card>
            )
          })}
        </div>
      )}
    </>
  )
}
