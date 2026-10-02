'use client'

import { useEffect, useMemo, useState, useRef } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { AnimatePresence, motion } from 'framer-motion'
import {
  Activity,
  AlertTriangle,
  Bell,
  BookOpen,
  BrainCircuit,
  CheckCircle2,
  ChevronRight,
  CircleHelp,
  Clock,
  Compass,
  Database,
  ExternalLink,
  Eye,
  FileText,
  Filter,
  FlaskConical,
  Gauge,
  HelpCircle,
  Layers,
  LayoutDashboard,
  ListFilter,
  Menu,
  Moon,
  Network,
  PanelLeft,
  PanelLeftClose,
  RefreshCw,
  RotateCcw,
  Search,
  Settings,
  ShieldAlert,
  ShieldCheck,
  Sliders,
  Sparkles,
  Star,
  Sun,
  Target,
  Trash2,
  User,
  X,
  Zap,
} from 'lucide-react'

import { SpecularButton } from '@/components/ui/SpecularButton'
import { MetaRadarLogo } from '@/components/common/MetaRadarLogo'
import { DemoOperatorSelector } from '@/components/common/DemoOperatorSelector'
import { useTheme } from '@/components/theme/ThemeProvider'
import { useAuth } from '@/context/AuthContext'
import ProfileCard from '@/components/auth/ProfileCard'
import { SignalCard } from '@/components/signals/SignalCard'
import Counter from '@/components/ui/Counter'
import AnimatedCounter from '@/components/ui/AnimatedCounter'
import { GlowingThinkingButton } from '@/components/ui/GlowingThinkingButton'
import Stepper, { Step } from '@/components/ui/Stepper'
import { Area, AreaChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import {
  askAthena,
  getAthenaSuggestedQuestions,
  clearCache,
  confirmWatchItem,
  getCalibrationWeights,
  getConfluences,
  getDevelopments,
  getFeedbackSummary,
  getHealthModels,
  getHealthReady,
  getLifecycles,
  getMissingSignals,
  getOverview,
  getPendingApprovals,
  getRedTeamContradictions,
  getSignals,
  getSources,
  mapSearchResult,
  mapSignal,
  recalibrateRole,
  searchSignals,
  submitFeedback,
  triggerIngestAndPipelineSync,
} from '@/lib/api'
import { useLiveData } from '@/lib/hooks'
import type {
  ApprovalRequest,
  AthenaResponse,
  BeforeAfterComparison,
  CacheClearResponse,
  ConfluenceAlertItem,
  ContradictionItem,
  DashboardOverview,
  DevelopmentSummary,
  FeedbackSummaryResponse,
  HealthModelsResponse,
  HealthReadyResponse,
  LifecycleTimelineItem,
  MissingSignalWatchItem,
  RecalibrateResponse,
  Signal,
  SignalFilterParams,
  SignalSearchResult,
  SourceRegistryItem,
  WatchRuleSuggestion,
} from '@/types/api'

const primaryNav = [
  { href: '/dashboard', label: 'Overview', icon: LayoutDashboard },
  { href: '/signals', label: 'Signals', icon: Activity },
  { href: '/intelligence', label: 'Search & Athena', icon: BrainCircuit },
]

const deepNav = [
  { href: '/confluence', label: 'Confluence', icon: Zap },
  { href: '/lifecycles', label: 'Lifecycles', icon: Clock },
  { href: '/red-team', label: 'Red Team', icon: ShieldAlert },
  { href: '/missing-signals', label: 'Missing Signals', icon: Eye },
  { href: '/developments', label: 'Developments', icon: FlaskConical },
]

const adminNav = [
  { href: '/sources', label: 'Sources & Connectors', icon: BookOpen },
  { href: '/observability', label: 'Observability & Logs', icon: Database },
  { href: '/settings', label: 'Settings', icon: Settings },
]

const nav = [...primaryNav, ...deepNav, ...adminNav]
const secondary = adminNav

export function Badge({
  children,
  tone = 'neutral',
}: {
  children: React.ReactNode
  tone?: 'critical' | 'high' | 'medium' | 'low' | 'neutral'
}) {
  return <span className={`badge badge-${tone}`}>{children}</span>
}

export function Card({
  children,
  className = '',
  style,
  role,
  'aria-live': ariaLive,
}: {
  children?: React.ReactNode
  className?: string
  style?: React.CSSProperties
  role?: string
  'aria-live'?: 'off' | 'assertive' | 'polite'
}) {
  return (
    <section className={`panel ${className}`} style={style} role={role} aria-live={ariaLive}>
      {children}
    </section>
  )
}

export function SectionTitle({
  eyebrow,
  title,
  detail,
}: {
  eyebrow: string
  title: string
  detail?: string
}) {
  return (
    <div className="section-title">
      <div>
        <p className="eyebrow">{eyebrow}</p>
        <h1>{title}</h1>
      </div>
      {detail && <p className="muted max-w-xs text-right text-sm">{detail}</p>}
    </div>
  )
}

const ROLE_PERSONAS: Record<string, { name: string; title: string; handle: string; initials: string; email: string }> = {
  DEVELOPER: {
    name: 'test-developer',
    title: 'Platform Engineer / Developer',
    handle: 'test.developer',
    email: 'test-developer@metaradar.demo',
    initials: 'TD',
  },
  LEADERSHIP: {
    name: 'test-leader',
    title: 'Executive Leadership',
    handle: 'test.leader',
    email: 'test-leader@metaradar.demo',
    initials: 'TL',
  },
  MEDICAL_AFFAIRS: {
    name: 'test-medical',
    title: 'Medical Affairs Lead',
    handle: 'test.medical',
    email: 'test-medical@metaradar.demo',
    initials: 'TM',
  },
  REGULATORY: {
    name: 'test-regulatory',
    title: 'Regulatory Affairs Director',
    handle: 'test.regulatory',
    email: 'test-regulatory@metaradar.demo',
    initials: 'TR',
  },
  SAFETY: {
    name: 'test-safety',
    title: 'Pharmacovigilance & Safety Lead',
    handle: 'test.safety',
    email: 'test-safety@metaradar.demo',
    initials: 'TS',
  },
  MARKET_ACCESS: {
    name: 'test-access',
    title: 'Market Access & HEOR Lead',
    handle: 'test.access',
    email: 'test-access@metaradar.demo',
    initials: 'TA',
  },
  COMMUNICATIONS: {
    name: 'test-comms',
    title: 'Medical Communications Lead',
    handle: 'test.comms',
    email: 'test-comms@metaradar.demo',
    initials: 'TC',
  },
  ADMIN: {
    name: 'test-admin',
    title: 'System Administrator',
    handle: 'test.admin',
    email: 'admin@metaradar.internal',
    initials: 'TA',
  },
}

export function Shell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()
  const [open, setOpen] = useState(false)
  const [isCollapsed, setIsCollapsed] = useState(false)
  const [profileModalOpen, setProfileModalOpen] = useState(false)
  const { isDark, toggleTheme } = useTheme()
  const { user, role, logout } = useAuth()
  const [searchOpen, setSearchOpen] = useState(false)
  const [selectedSignal, setSelectedSignal] = useState<Signal | null>(null)
  const [notificationsOpen, setNotificationsOpen] = useState(false)

  const currentPersona = ROLE_PERSONAS[role] || ROLE_PERSONAS['MEDICAL_AFFAIRS']

  useEffect(() => {
    if (window.innerWidth < 900) setIsCollapsed(false)
  }, [open])

  // Live health status polling (60s cadence)
  const { data: healthReady } = useLiveData<HealthReadyResponse>(getHealthReady, 60000)
  const { data: healthModels } = useLiveData<HealthModelsResponse>(getHealthModels, 60000)

  // Global ⌘K / Ctrl+K keyboard shortcut
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault()
        setSearchOpen((prev) => !prev)
      } else if (e.key === 'Escape') {
        setSearchOpen(false)
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [])

  const [ingesting, setIngesting] = useState(false)
  const [ingestNotice, setIngestNotice] = useState<string | null>(null)

  const handleManualIngest = async () => {
    setIngesting(true)
    setIngestNotice(null)
    try {
      const res = await triggerIngestAndPipelineSync(undefined, 50)
      const fetched = res.ingestion?.total_fetched ?? 0
      const processed = res.pipeline?.signals_processed ?? 0
      setIngestNotice(`Ingestion completed: ${fetched} fetched, ${processed} processed`)
      setTimeout(() => setIngestNotice(null), 6000)
    } catch (err) {
      setIngestNotice('Ingestion encountered an error. Check sources telemetry.')
      setTimeout(() => setIngestNotice(null), 6000)
    } finally {
      setIngesting(false)
    }
  }

  const isDegraded = healthReady?.status === 'degraded'
  const currentSectionLabel =
    nav.find((item) => item.href === pathname)?.label ??
    secondary.find((item) => item.href === pathname)?.label ??
    'Overview'

  return (
    <div className="app-shell">
      {/* Sidebar Dock */}
      <aside className={`sidebar ${isCollapsed ? 'collapsed' : ''} ${open ? 'sidebar-open' : ''}`}>
        
        {/* User Profile & Dock Controls at TOP of Dock */}
        <div className="sidebar-top-profile">
          <button
            type="button"
            onClick={() => setProfileModalOpen(true)}
            className="user-profile-dock-btn group"
            title={isCollapsed ? `Profile: ${user?.display_name || currentPersona.name} (${currentPersona.title})` : 'Click to view holographic Profile Card'}
            aria-label="View Profile Card"
          >
            <div className="user-profile-avatar-wrap">
              <div className="avatar-dot-ring">
                <span className="avatar-initials">{currentPersona.initials}</span>
              </div>
              <span className="online-indicator-dot" />
            </div>
            <div className="user-profile-text text-left">
              <div className="flex items-center gap-1">
                <strong className="user-name truncate">{user?.display_name || currentPersona.name}</strong>
                <Sparkles size={11} className="text-[var(--signal)] shrink-0" />
              </div>
              <span className="user-role truncate">{currentPersona.title}</span>
            </div>
            <div className="profile-open-arrow">
              <ChevronRight size={14} />
            </div>
          </button>
          
          {/* Dock Collapse / Expand Toggle Button */}
          <button
            type="button"
            onClick={() => setIsCollapsed(!isCollapsed)}
            className="dock-toggle-btn hidden md:grid"
            aria-label={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            title={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            {isCollapsed ? <PanelLeft size={16} /> : <PanelLeftClose size={16} />}
          </button>

          {/* Mobile close */}
          <button
            className="icon-button sidebar-close md:hidden"
            onClick={() => {
              setOpen(false)
              setIsCollapsed(false)
            }}
            aria-label="Close navigation"
          >
            <X size={18} />
          </button>
        </div>

        {/* Navigation List */}
        <nav className="nav-list" aria-label="Primary navigation">
          <div className="nav-section-title text-[10px] uppercase font-bold tracking-wider text-[var(--muted-foreground)] px-3 py-1 opacity-80">
            Decision Workspace
          </div>
          {primaryNav.map(({ href, label, icon: Icon }) => (
            <Link
              key={href}
              href={href}
              onClick={() => setOpen(false)}
              className={`nav-item ${pathname === href ? 'active' : ''}`}
              title={isCollapsed ? label : undefined}
            >
              <Icon size={17} className="shrink-0" />
              <span className="nav-item-text">{label}</span>
            </Link>
          ))}

          <div className="nav-section-title text-[10px] uppercase font-bold tracking-wider text-[var(--muted-foreground)] px-3 pt-3 pb-1 opacity-80 border-t border-[var(--border)] mt-2">
            Deep Investigation
          </div>
          <div className="nav-divider" />
          {deepNav.map(({ href, label, icon: Icon }) => (
            <Link
              key={href}
              href={href}
              onClick={() => setOpen(false)}
              className={`nav-item ${pathname === href ? 'active' : ''}`}
              title={isCollapsed ? label : undefined}
            >
              <Icon size={16} className="shrink-0" />
              <span className="nav-item-text text-xs">{label}</span>
            </Link>
          ))}

          <div className="nav-section-title text-[10px] uppercase font-bold tracking-wider text-[var(--muted-foreground)] px-3 pt-3 pb-1 opacity-80 border-t border-[var(--border)] mt-2">
            System & Admin
          </div>
          <div className="nav-divider" />
          {adminNav.map(({ href, label, icon: Icon }) => (
            <Link
              key={href}
              href={href}
              onClick={() => setOpen(false)}
              className={`nav-item ${pathname === href ? 'active' : ''}`}
              title={isCollapsed ? label : undefined}
            >
              <Icon size={16} className="shrink-0" />
              <span className="nav-item-text text-xs">{label}</span>
            </Link>
          ))}
        </nav>

        {/* Live Intelligence Footer */}
        <div
          className="sidebar-note group cursor-default"
          title={`Live Intelligence: ${healthModels ? `${healthModels.llm_provider.toUpperCase()} · ${healthModels.embedding_model}` : 'Connecting to pipeline...'}`}
        >
          <div className="relative shrink-0 flex items-center justify-center">
            <Sparkles size={17} />
            <span className="live-pulse-dot" />
          </div>
          <div className="sidebar-note-content">
            <strong>Live Intelligence</strong>
            <span>
              {healthModels
                ? `${healthModels.llm_provider.toUpperCase()} · ${healthModels.embedding_model}`
                : 'Connecting to pipeline...'}
            </span>
          </div>
        </div>
      </aside>

      <div className="main-column">
        {isDegraded && (
          <div className="degraded-banner" role="alert">
            <AlertTriangle size={15} />
            <span>
              System Notice: Running in degraded mode ({healthReady?.redis_warning || 'Cache unavailable'}). Core intelligence and reasoning remain operational.
            </span>
          </div>
        )}
        {ingestNotice && (
          <div className="px-4 py-2 bg-[var(--surface-hover)] border-b border-[var(--border)] text-xs text-[var(--foreground)] flex items-center justify-between animate-fadeIn">
            <span className="flex items-center gap-2">
              <CheckCircle2 size={14} style={{ color: 'var(--success)' }} />
              {ingestNotice}
            </span>
            <button onClick={() => setIngestNotice(null)} className="text-[var(--muted-foreground)] hover:text-[var(--foreground)] text-sm px-1">✕</button>
          </div>
        )}

        {/* Top Header Bar */}
        <header className="topbar">
          <div className="flex items-center gap-3">
            <button
              className="icon-button menu-button flex items-center justify-center"
              onClick={() => {
                if (typeof window !== 'undefined' && window.innerWidth < 900) {
                  setOpen(!open)
                  setIsCollapsed(false)
                } else {
                  setIsCollapsed(!isCollapsed)
                }
              }}
              aria-label="Toggle navigation dock"
              title="Toggle navigation dock"
            >
              <Menu size={20} />
            </button>
            <div className="flex items-center gap-2.5">
              <div className="p-1 rounded-lg bg-[var(--surface-secondary)] border border-[var(--border)] shadow-sm">
                <MetaRadarLogo size={26} />
              </div>
              <span className="topbar-brand-title">
                MetaRadar
              </span>
              <span className="badge badge-critical text-[9px] py-0.5 px-2 font-mono font-bold hidden sm:inline-flex">
                HAEMOPHILIA
              </span>
            </div>
            <div className="h-4 w-[1px] bg-[var(--border)] hidden lg:block mx-1" />
            <div className="hidden lg:flex items-center gap-1.5 text-xs text-[var(--muted-foreground)]">
              <span className="font-semibold text-[var(--foreground)]">
                {currentSectionLabel}
              </span>
            </div>
          </div>

          <div className="top-actions">
            <SpecularButton
              size="default"
              radius={8}
              intensity={1.2}
              shineSize={14}
              shineFade={45}
              thickness={1}
              speed={0.4}
              followMouse
              proximity={220}
              loading={ingesting}
              autoAnimate={ingesting}
              onClick={handleManualIngest}
              disabled={ingesting}
              title="Manually trigger live public data ingestion and pipeline run"
              aria-label="Ingest data now"
              className="h-8 shadow-sm cursor-pointer"
            >
              {ingesting ? (
                <>
                  <RefreshCw size={13} className="animate-spin text-[var(--primary)]" />
                  <span className="hidden sm:inline font-semibold">Ingesting...</span>
                </>
              ) : (
                <>
                  <Zap size={13} className="text-amber-400" />
                  <span className="hidden sm:inline font-semibold">Ingest Data</span>
                </>
              )}
            </SpecularButton>
            <button
              className="search-button"
              onClick={() => setSearchOpen(true)}
              aria-label="Search signals"
            >
              <Search size={16} />
              <span>Search signals</span>
              <kbd>⌘ K</kbd>
            </button>
            <button
              className="icon-button notification"
              aria-label="Notifications"
              aria-expanded={notificationsOpen}
              onClick={() => setNotificationsOpen((open) => !open)}
            >
              <Bell size={17} />
              <i />
            </button>
            {notificationsOpen && (
              <div className="absolute right-12 top-12 z-50 w-72 rounded-md border border-[var(--border)] bg-[var(--surface)] p-3 shadow-lg">
                <div className="flex items-center justify-between">
                  <strong className="text-xs">Notifications</strong>
                  <button
                    className="text-xs text-[var(--muted-foreground)]"
                    onClick={() => setNotificationsOpen(false)}
                    aria-label="Close notifications"
                  >
                    Close
                  </button>
                </div>
                <p className="m-0 mt-3 text-xs text-[var(--muted-foreground)]">No new operational notifications.</p>
              </div>
            )}
            <button
              className="theme-toggle"
              onClick={toggleTheme}
              aria-label={`Switch to ${isDark ? 'light' : 'dark'} mode`}
            >
              {isDark ? <Moon size={16} /> : <Sun size={16} />}
            </button>
          </div>
        </header>

        <main className="content">{children}</main>

        <footer className="health-footer">
          <span>
            <Activity size={13} /> {healthReady?.database ? 'Database: Operational' : 'Database: Connecting...'}
          </span>
          <span>
            <ShieldCheck size={13} /> PII/PHI Scrubber: Active
          </span>
          <span className="footer-source">
            <BrainCircuit size={13} /> {healthModels?.llm_provider.toUpperCase() || 'Local Gemma'} Reasoning Engine
          </span>
        </footer>
      </div>

      {/* 3D Holographic Animated Profile Card Modal */}
      {profileModalOpen && (
        <div 
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-md animate-fadeIn select-none"
          onClick={() => setProfileModalOpen(false)}
        >
          <div 
            className="relative flex flex-col items-center justify-center animate-scaleUp"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              type="button"
              onClick={() => setProfileModalOpen(false)}
              className="absolute -top-11 right-0 sm:-right-8 text-white/80 hover:text-white p-1.5 rounded-full bg-white/10 hover:bg-white/20 backdrop-blur-md transition-all cursor-pointer z-30"
              aria-label="Close profile modal"
            >
              <X size={20} />
            </button>

            <ProfileCard
              name={user?.display_name || currentPersona.name}
              title={currentPersona.title}
              handle={currentPersona.handle}
              email={user?.email || currentPersona.email || `${currentPersona.handle}@metaradar.demo`}
              roleId={role}
              status="Online & Verified"
              contactText="Sign Out"
              onContactClick={() => {
                setProfileModalOpen(false)
                logout()
              }}
            />
            
            <p className="text-white/60 text-xs mt-3 font-mono text-center">
              Move cursor over card for 3D holographic tilt • Click outside to close
            </p>
          </div>
        </div>
      )}

      {searchOpen && (
        <SearchModal
          onClose={() => setSearchOpen(false)}
          onSelectSignal={(sig) => {
            setSearchOpen(false)
            setSelectedSignal(sig)
          }}
        />
      )}

      {selectedSignal && (
        <SignalDrawer
          signal={selectedSignal}
          onClose={() => setSelectedSignal(null)}
        />
      )}
    </div>
  )
}

export function SearchModal({
  onClose,
  onSelectSignal,
}: {
  onClose: () => void
  onSelectSignal: (signal: Signal) => void
}) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<SignalSearchResult[]>([])
  const [loading, setLoading] = useState(false)
  const [searchError, setSearchError] = useState<string | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    inputRef.current?.focus()
  }, [])

  useEffect(() => {
    if (!query.trim()) {
      setResults([])
      setLoading(false)
      return
    }

    const timer = setTimeout(async () => {
      setLoading(true)
      setSearchError(null)
      try {
        const res = await searchSignals(query, 8)
        setResults(res.results)
      } catch (err) {
        setSearchError(err instanceof Error ? err.message : 'Search failed')
        setResults([])
      } finally {
        setLoading(false)
      }
    }, 200)

    return () => clearTimeout(timer)
  }, [query])

  return (
    <div className="search-modal-backdrop" onClick={onClose}>
      <div className="search-modal" onClick={(e) => e.stopPropagation()}>
        <div className="search-header">
          <Search size={18} />
          <input
            ref={inputRef}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search signals by ID, drug, mechanism, or concepts (e.g. EMA-CHMP-2026-04, NCT04869267, Mim8)..."
          />
          <kbd>ESC</kbd>
        </div>
        <div className="search-results">
          {loading && (
            <div className="search-empty">
              <Activity size={18} className="animate-spin text-signal" />
              <p>Searching 384-dim semantic index & identifiers...</p>
            </div>
          )}
          {searchError && (
            <div className="search-empty text-warning">
              <p>Search unavailable: {searchError}</p>
            </div>
          )}
          {!loading && !searchError && results.length > 0 && (
            results.map((r) => {
              const scorePct = Math.round(r.similarity_score * 100)
              return (
                <button
                  key={r.signal_id}
                  className="search-item text-left w-full"
                  onClick={() => onSelectSignal(mapSearchResult(r))}
                >
                  <div className="search-item-top flex items-start justify-between gap-2">
                    <strong className="text-sm text-[var(--foreground)]">{r.title}</strong>
                    <Badge tone={scorePct >= 80 ? 'high' : 'neutral'}>
                      {scorePct >= 99 ? 'Exact Match' : `${scorePct}% match`}
                    </Badge>
                  </div>
                  <p className="text-xs text-[var(--muted-foreground)] line-clamp-2 my-1">{r.content}</p>
                  <div className="search-item-meta text-[11px] font-mono text-[var(--muted-foreground)] flex items-center gap-2">
                    <span className="text-[var(--signal)] font-semibold">{r.signal_id.slice(0, 8)}...</span>
                    <span>·</span>
                    <span>{r.disease}</span>
                    <span>·</span>
                    <span>{r.signal_type}</span>
                  </div>
                </button>
              )
            })
          )}
          {!loading && !searchError && query.trim() && results.length === 0 && (
            <div className="search-empty">
              <p>No matching signals found for &ldquo;{query}&rdquo;</p>
            </div>
          )}
          {!query.trim() && (
            <div className="search-empty">
              <p>Type keywords or signal IDs (e.g. EMA-CHMP-2026-04, 38291023, NCT04869267, Mim8) to search.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function KPI({
  label,
  value,
  change,
  accent,
}: {
  label: string
  value: string | number
  change: string
  accent?: string
}) {
  const isNumeric = typeof value === 'number'

  return (
    <Card className="kpi">
      <p className="eyebrow">{label}</p>
      <div className="kpi-value">
        <strong className="kpi-number">
          {isNumeric ? <AnimatedCounter value={value} duration={850} /> : value}
        </strong>
        <span className={`kpi-change ${accent ?? 'positive'}`}>{change}</span>
      </div>
      <div className="micro-bars">
        <i />
        <i />
        <i />
        <i />
        <i />
      </div>
    </Card>
  )
}

function Radar({ score }: { score: number }) {
  return (
    <div className="radar">
      <div className="radar-ring ring-one" />
      <div className="radar-ring ring-two" />
      <div className="radar-ring ring-three" />
      <div className="radar-sweep" />
      <div className="radar-core">
        <strong>{Math.round(score)}</strong>
        <span>confluence</span>
      </div>
    </div>
  )
}

export function SignalRow({
  signal,
  onSelect,
}: {
  signal: Signal
  onSelect: (signal: Signal) => void
}) {
  return (
    <button className="signal-row" onClick={() => onSelect(signal)}>
      <span className={`severity-dot ${signal.severity}`} />
      <div className="signal-copy">
        <div>
          <strong>{signal.title}</strong>
          <Badge tone={signal.severity}>{signal.severity}</Badge>
        </div>
        <span>{signal.summary}</span>
        <small>
          {signal.detectedAt} · {signal.sources.length} sources
        </small>
      </div>
      <div className="signal-score">
        <strong>{signal.score}</strong>
        <span>priority score</span>
      </div>
      <ChevronRight size={17} className="muted" />
    </button>
  )
}

function TrendChart({ data }: { data: DashboardOverview['trends'] }) {
  return (
    <div className="chart-wrap">
      <ResponsiveContainer width="100%" height={220}>
        <AreaChart
          data={data}
          margin={{ left: -22, right: 8, top: 10, bottom: 0 }}
        >
          <defs>
            <linearGradient id="trend" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="var(--signal)" stopOpacity={0.35} />
              <stop offset="100%" stopColor="var(--signal)" stopOpacity={0} />
            </linearGradient>
          </defs>
          <XAxis
            dataKey="label"
            axisLine={false}
            tickLine={false}
            tick={{ fill: 'var(--muted-foreground)', fontSize: 11 }}
          />
          <YAxis hide domain={[0, 100]} />
          <Tooltip
            contentStyle={{
              background: 'var(--panel)',
              border: '1px solid var(--border)',
              borderRadius: 10,
              color: 'var(--foreground)',
            }}
          />
          <Area
            type="monotone"
            dataKey="baseline"
            stroke="var(--muted-foreground)"
            strokeDasharray="4 4"
            fill="none"
            strokeWidth={1.5}
          />
          <Area
            type="monotone"
            dataKey="value"
            stroke="var(--signal)"
            fill="url(#trend)"
            strokeWidth={2.5}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}

export function FilterBar({
  onApply,
  onClear,
}: {
  onApply: (params: SignalFilterParams) => void
  onClear: () => void
}) {
  const [expanded, setExpanded] = useState(false)
  const [severity, setSeverity] = useState('')
  const [entity, setEntity] = useState('')
  const [signalType, setSignalType] = useState('')
  const [source, setSource] = useState('')
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')

  const handleApply = () => {
    onApply({
      severity: severity || undefined,
      entity: entity || undefined,
      signal_type: signalType || undefined,
      source: source || undefined,
      date_from: dateFrom || undefined,
      date_to: dateTo || undefined,
    })
  }

  const handleClear = () => {
    setSeverity('')
    setEntity('')
    setSignalType('')
    setSource('')
    setDateFrom('')
    setDateTo('')
    onClear()
  }

  return (
    <div className="mb-4">
      <div className="flex items-center justify-between gap-3 mb-2">
        <button
          className={`filter-btn inline-flex items-center gap-2 px-3 py-1.5 rounded text-xs border border-[var(--border)] ${expanded ? 'bg-[var(--surface-secondary)] font-semibold' : 'bg-transparent text-[var(--muted-foreground)]'}`}
          onClick={() => setExpanded(!expanded)}
        >
          <ListFilter size={14} />
          <span>{expanded ? 'Hide Filters' : 'Apply Filters'}</span>
          {(severity || entity || signalType || source || dateFrom) && (
            <span className="w-2 h-2 rounded-full bg-[var(--signal)]" />
          )}
        </button>
      </div>

      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="filter-drawer-panel"
          >
            <div className="filter-grid">
              <div className="filter-group">
                <label>Priority / Severity</label>
                <select
                  className="filter-select"
                  value={severity}
                  onChange={(e) => setSeverity(e.target.value)}
                >
                  <option value="">All Priorities</option>
                  <option value="CRITICAL">Critical</option>
                  <option value="HIGH">High</option>
                  <option value="MEDIUM">Medium</option>
                  <option value="LOW">Low</option>
                </select>
              </div>

              <div className="filter-group">
                <label>Entity / Drug / Term</label>
                <input
                  type="text"
                  placeholder="e.g. Hemgenix, concizumab..."
                  className="filter-input"
                  value={entity}
                  onChange={(e) => setEntity(e.target.value)}
                />
              </div>

              <div className="filter-group">
                <label>Signal Type</label>
                <select
                  className="filter-select"
                  value={signalType}
                  onChange={(e) => setSignalType(e.target.value)}
                >
                  <option value="">All Types</option>
                  <option value="congress">Congress Abstract</option>
                  <option value="trial">Clinical Trial</option>
                  <option value="regulatory">Regulatory</option>
                  <option value="safety">Safety / PV</option>
                  <option value="access">Market Access</option>
                  <option value="comms">Communications</option>
                </select>
              </div>

              <div className="filter-group">
                <label>Source</label>
                <select
                  className="filter-select"
                  value={source}
                  onChange={(e) => setSource(e.target.value)}
                >
                  <option value="">All Sources</option>
                  <option value="pubmed">PubMed</option>
                  <option value="clinicaltrials">ClinicalTrials.gov</option>
                  <option value="openfda">OpenFDA</option>
                  <option value="newsapi">NewsAPI</option>
                  <option value="ema_rss">EMA RSS</option>
                </select>
              </div>

              <div className="filter-group">
                <label>Published After</label>
                <input
                  type="date"
                  className="filter-input"
                  value={dateFrom}
                  onChange={(e) => setDateFrom(e.target.value)}
                />
              </div>

              <div className="filter-group">
                <label>Published Before</label>
                <input
                  type="date"
                  className="filter-input"
                  value={dateTo}
                  onChange={(e) => setDateTo(e.target.value)}
                />
              </div>
            </div>

            <div className="filter-actions">
              <button className="clear-filter-btn" onClick={handleClear}>
                Reset
              </button>
              <button className="apply-filter-btn" onClick={handleApply}>
                <Filter size={13} /> Apply Filters
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

export function CacheClearModal({
  isOpen,
  onClose,
  onSuccess,
}: {
  isOpen: boolean
  onClose: () => void
  onSuccess: (status?: string) => void
}) {
  const [clearing, setClearing] = useState(false)

  if (!isOpen) return null

  const handleConfirm = async () => {
    setClearing(true)
    try {
      const res = await clearCache()
      onSuccess(res?.status)
      onClose()
    } catch (err) {
      console.error('Failed to clear cache:', err)
      onClose()
    } finally {
      setClearing(false)
    }
  }

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-card" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center gap-2 mb-3 text-[var(--danger)] font-bold text-sm">
          <Trash2 size={18} />
          <span>Clear Server Cache</span>
        </div>
        <p className="text-xs text-[var(--muted-foreground)] leading-relaxed mb-5">
          This will flush the Redis cache layer and invalidate all cached intelligence aggregations. Active pipeline processing will repopulate the cache on demand.
        </p>
        <div className="flex justify-end gap-3">
          <button className="modal-cancel-btn" onClick={onClose} disabled={clearing}>
            Cancel
          </button>
          <button
            className="modal-danger-btn inline-flex items-center gap-2"
            onClick={handleConfirm}
            disabled={clearing}
          >
            {clearing ? <RefreshCw size={13} className="spin" /> : <Trash2 size={13} />}
            <span>Clear Cache</span>
          </button>
        </div>
      </div>
    </div>
  )
}

export function DashboardPage() {
  const { role } = useAuth()
  const { data, loading, error, isRefreshing, refetch } = useLiveData<DashboardOverview>(getOverview)
  const [selected, setSelected] = useState<Signal | null>(null)
  const [overviewTab, setOverviewTab] = useState<'all' | 'critical' | 'review' | 'leadership'>('all')
  const [pendingApprovals, setPendingApprovals] = useState<ApprovalRequest[]>([])

  useEffect(() => {
    if (role === 'LEADERSHIP' || role === 'ADMIN') {
      getPendingApprovals()
        .then((items) => setPendingApprovals(items))
        .catch(() => setPendingApprovals([]))
    }
  }, [role])

  if (loading && !data) return <Loading />

  if (error && !data) {
    return (
      <div className="error-card">
        <h3>Workspace Connection Failure</h3>
        <p>Could not connect to backend service at {process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'}</p>
        <button className="retry-button" onClick={() => refetch()}>
          <RefreshCw size={14} /> Retry Connection
        </button>
      </div>
    )
  }

  const overviewData: DashboardOverview = data || {
    active_signals: 0,
    monitored_assets: 0,
    confluences_detected: 0,
    contradictions_flagged: 0,
    weekly_change: '+0%',
    signals: [],
    confluence: { score: 0, label: 'Calculating...', drivers: [], updatedAt: 'Just now' },
    lifecycle: [],
    trends: [],
    health: { api: 'healthy', lastSync: 'Live', latencyMs: 12, sourceCount: 8 },
  }

  const totalSignals = overviewData.signals.length
  const criticalSignalsCount = overviewData.signals.filter((s) => {
    const p = (s.priority || s.severity || '').toUpperCase()
    return p === 'CRITICAL' || p === 'HIGH' || (s.score && s.score >= 70)
  }).length

  const reviewSignalsCount = overviewData.signals.filter((s) => {
    const st = (s.review_status || s.status || '').toLowerCase()
    return st.includes('unreviewed') || st.includes('pending') || st.includes('in_review') || st.includes('review')
  }).length

  const leadershipSignalsCount = overviewData.signals.filter((s) => {
    return Boolean(s.is_escalated || (s as any).escalate_to_leadership || s.route_destination?.toLowerCase().includes('leadership'))
  }).length

  const prioritySignals = overviewData.signals.filter((s) => {
    if (overviewTab === 'critical') {
      const p = (s.priority || s.severity || '').toUpperCase()
      return p === 'CRITICAL' || p === 'HIGH' || (s.score && s.score >= 70)
    }
    if (overviewTab === 'review') {
      const st = (s.review_status || s.status || '').toLowerCase()
      return st.includes('unreviewed') || st.includes('pending') || st.includes('in_review') || st.includes('review')
    }
    if (overviewTab === 'leadership') {
      return Boolean(s.is_escalated || (s as any).escalate_to_leadership || s.route_destination?.toLowerCase().includes('leadership'))
    }
    return true
  })

  return (
    <>
      <SectionTitle
        eyebrow="Decision Intelligence Briefing"
        title="Executive Overview"
        detail={isRefreshing ? 'Syncing live telemetry...' : 'Evidence-grounded critical signals and decision alerts across the haemophilia landscape.'}
      />

      {/* Leadership Cross-Functional Pending Approvals Alert Banner */}
      {(role === 'LEADERSHIP' || role === 'ADMIN') && pendingApprovals.length > 0 && (
        <div className="mb-6 rounded-xl border border-amber-500/40 bg-amber-500/10 p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 animate-in fade-in">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-lg bg-amber-500/20 text-amber-400 border border-amber-500/30 shrink-0">
              <ShieldAlert className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-sm font-bold text-slate-100 m-0">
                  {pendingApprovals.length} Cross-Functional Escalation{pendingApprovals.length > 1 ? 's' : ''} Awaiting Executive Steer
                </h3>
                <span className="px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-300 text-[10px] font-bold font-mono border border-amber-500/30">
                  ACTION REQUIRED
                </span>
              </div>
              <p className="text-xs text-slate-300 m-0 mt-0.5">
                Teams require executive review and approval for prioritized signal actions.
              </p>
            </div>
          </div>
          <Link
            href="/functions"
            className="shrink-0 px-4 py-2 rounded-lg bg-amber-500 hover:bg-amber-400 text-slate-950 text-xs font-bold transition-all shadow-md flex items-center gap-1.5"
          >
            <span>Review Approvals Queue</span>
            <ChevronRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      )}

      {/* Daily Executive Intelligence Briefing Hero Card (REQ-P10-09) */}
      <div className="mb-3.5 rounded-xl border border-[var(--primary)]/25 bg-[var(--primary)]/5 p-3.5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="flex h-2 w-2 rounded-full bg-[var(--primary)] animate-pulse" />
              <span className="text-[10px] font-bold uppercase tracking-wider text-[var(--primary)]">
                Today's Executive Intelligence Summary
              </span>
            </div>
            <p className="text-xs text-[var(--foreground)] m-0 leading-relaxed">
              MetaRadar continuously monitors <strong>8 authoritative & discovery sources</strong>, validated <strong>{overviewData.confluences_detected ?? 0} multi-source confluences</strong>, and flagged <strong>{criticalSignalsCount} high-urgency signals</strong> requiring functional attention.
            </p>
          </div>

          <div className="flex items-center gap-2 flex-wrap">
            <div className="rounded-lg border border-[var(--border)] bg-[var(--surface)] px-3 py-1 text-center">
              <div className="text-sm font-bold font-mono text-[var(--foreground)]">{totalSignals}</div>
              <div className="text-[9px] uppercase tracking-wider text-[var(--muted-foreground)]">Total Signals</div>
            </div>
            <div className="rounded-lg border border-[var(--border)] bg-[var(--surface)] px-3 py-1 text-center">
              <div className="text-sm font-bold font-mono text-[var(--priority-critical)]">{criticalSignalsCount}</div>
              <div className="text-[9px] uppercase tracking-wider text-[var(--muted-foreground)]">High Priority</div>
            </div>
            <div className="rounded-lg border border-[var(--border)] bg-[var(--surface)] px-3 py-1 text-center">
              <div className="text-sm font-bold font-mono text-[var(--warning)]">{reviewSignalsCount}</div>
              <div className="text-[9px] uppercase tracking-wider text-[var(--muted-foreground)]">Needs Review</div>
            </div>
            <div className="rounded-lg border border-[var(--border)] bg-[var(--surface)] px-3 py-1 text-center">
              <div className="text-sm font-bold font-mono text-[var(--accent)]">{leadershipSignalsCount}</div>
              <div className="text-[9px] uppercase tracking-wider text-[var(--muted-foreground)]">Leadership</div>
            </div>
          </div>
        </div>
      </div>

      {/* 1. Decision Context KPIs */}
      <div className="kpi-grid mb-4">
        <KPI
          label="Active Signals"
          value={overviewData.active_signals ?? totalSignals}
          change={overviewData.weekly_change || '+12%'}
          accent={(overviewData.active_signals ?? totalSignals) > 0 ? 'text-emerald' : 'muted'}
        />
        <KPI
          label="Monitored Assets"
          value={overviewData.monitored_assets ?? 8}
          change={(overviewData.monitored_assets ?? 8) > 0 ? 'Active' : 'Idle'}
          accent="text-emerald"
        />
        <KPI
          label="Confluences Detected"
          value={overviewData.confluences_detected ?? 0}
          change={(overviewData.confluences_detected ?? 0) > 0 ? 'High Confidence' : 'None'}
        />
        <KPI
          label="Live Sources"
          value={overviewData.health?.sourceCount ?? 8}
          change="8 Connected"
        />
      </div>

      {/* 2. Priority Signals: What Deserves Attention Right Now */}
      <div className="mb-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
          <div>
            <h2 className="text-base font-bold text-[var(--foreground)] m-0 flex items-center gap-2">
              <Activity size={18} className="text-[var(--primary)]" />
              <span>What Deserves Attention Right Now</span>
            </h2>
            <p className="text-xs text-[var(--muted-foreground)] m-0">
              Ranked decision cards prioritizing critical therapeutic inflections and pending stakeholder reviews.
            </p>
          </div>

          <div className="flex items-center gap-2 flex-wrap">
            <div className="flex items-center gap-1 p-1 rounded-lg bg-[var(--surface-secondary)] border border-[var(--border)] text-xs">
              <button
                type="button"
                onClick={() => setOverviewTab('all')}
                className={`px-2.5 py-1 rounded-md font-semibold transition ${
                  overviewTab === 'all'
                    ? 'bg-[var(--surface)] text-[var(--foreground)] shadow-xs'
                    : 'text-[var(--muted-foreground)] hover:text-[var(--foreground)]'
                }`}
              >
                All ({totalSignals})
              </button>
              <button
                type="button"
                onClick={() => setOverviewTab('critical')}
                className={`px-2.5 py-1 rounded-md font-semibold transition ${
                  overviewTab === 'critical'
                    ? 'bg-[var(--surface)] text-[var(--priority-critical)] shadow-xs'
                    : 'text-[var(--muted-foreground)] hover:text-[var(--foreground)]'
                }`}
              >
                Critical ({criticalSignalsCount})
              </button>
              <button
                type="button"
                onClick={() => setOverviewTab('review')}
                className={`px-2.5 py-1 rounded-md font-semibold transition ${
                  overviewTab === 'review'
                    ? 'bg-[var(--surface)] text-[var(--warning)] shadow-xs'
                    : 'text-[var(--muted-foreground)] hover:text-[var(--foreground)]'
                }`}
              >
                Pending Review ({reviewSignalsCount})
              </button>
              <button
                type="button"
                onClick={() => setOverviewTab('leadership')}
                className={`px-2.5 py-1 rounded-md font-semibold transition ${
                  overviewTab === 'leadership'
                    ? 'bg-[var(--surface)] text-[var(--accent)] shadow-xs'
                    : 'text-[var(--muted-foreground)] hover:text-[var(--foreground)]'
                }`}
              >
                Leadership ({leadershipSignalsCount})
              </button>
            </div>

            <Link
              href="/signals"
              className="inline-flex items-center gap-1 text-xs font-semibold text-[var(--primary)] hover:underline ml-2"
            >
              <span>View all signals</span>
              <ChevronRight size={14} />
            </Link>
          </div>
        </div>

        {/* Two-column layout: signals left, analytics right */}
        <div className="dashboard-content-grid">
          {/* Left: Signal cards stacked vertically */}
          <div className="signals-col">
            {prioritySignals.length > 0 ? (
              <div className="flex flex-col gap-4">
                {prioritySignals.slice(0, 4).map((signal) => (
                  <SignalCard
                    key={signal.id}
                    signal={signal}
                  />
                ))}
              </div>
            ) : (
              <Card className="empty-state">
                <Activity size={28} />
                <p className="font-semibold text-sm">No signals requiring immediate attention</p>
                <span className="text-xs text-[var(--muted-foreground)]">
                  All signals have been reviewed. Ingest new public data or check the full Signals workspace.
                </span>
              </Card>
            )}
          </div>

          {/* Right: Analytics panels stacked vertically */}
          <div className="analytics-col">
            {/* Ask Athena Strategic Copilot Card */}
            <Card className="questions-panel">
              <div className="card-heading">
                <div>
                  <p className="eyebrow">Strategic Copilot</p>
                  <h2>Ask Athena</h2>
                </div>
                <Link href="/intelligence" className="icon-link" aria-label="Go to Athena Intelligence">
                  <ChevronRight size={17} />
                </Link>
              </div>
              <p className="text-xs text-[var(--muted-foreground)] mb-3">
                Grounded biomedical semantic synthesis across all indexed clinical and regulatory signals.
              </p>
              <div className="flex flex-col gap-2">
                {[
                  'What are the Phase 3 FRONTIER-2 Mim8 readout findings?',
                  'Summarize anti-TFPI regulatory milestones for 2024–2025',
                ].map((q) => (
                  <Link
                    key={q}
                    href={`/intelligence?q=${encodeURIComponent(q)}`}
                    className="p-2 rounded-md bg-[var(--surface-secondary)] border border-[var(--border)] hover:border-[var(--primary)] text-xs text-[var(--foreground)] flex items-center justify-between group transition-colors"
                  >
                    <span className="line-clamp-1">{q}</span>
                    <ChevronRight size={13} className="shrink-0 text-[var(--primary)] opacity-70 group-hover:opacity-100" />
                  </Link>
                ))}
              </div>
            </Card>

            <Card className="questions-panel">
              <div className="card-heading">
                <div>
                  <p className="eyebrow">Decision Framework</p>
                  <h2>Four Strategic Inquiries</h2>
                </div>
                <Link href="/intelligence" className="icon-link" aria-label="Go to Athena Intelligence">
                  <ChevronRight size={17} />
                </Link>
              </div>
              {[
                { q: 'What changed?', sub: 'Evidence-grounded factual developments' },
                { q: 'Why does it matter?', sub: 'Clinical & strategic significance' },
                { q: 'Who is affected?', sub: 'Functional routing & leadership escalation' },
                { q: 'What should we do?', sub: 'Actionable operational recommendations' },
              ].map((item, i) => (
                <Link href="/intelligence" className="question-row" key={item.q}>
                  <span>Q{i + 1}</span>
                  <div>
                    <strong>{item.q}</strong>
                    <small className="block text-[10px] text-[var(--muted-foreground)]">{item.sub}</small>
                  </div>
                  <ChevronRight size={15} />
                </Link>
              ))}
            </Card>
          </div>
        </div>
      </div>

      {selected && (
        <SignalDrawer signal={selected} onClose={() => setSelected(null)} />
      )}
    </>
  )
}

export function SignalsPage() {
  const [filterParams, setFilterParams] = useState<SignalFilterParams>({})
  const [selected, setSelected] = useState<Signal | null>(null)

  const { data: signals, loading, error, refetch, isRefreshing } = useLiveData<Signal[]>(
    (signal) => getSignals(filterParams, signal),
    30000,
    [filterParams]
  )

  const signalsList: Signal[] = signals || []

  return (
    <>
      <SectionTitle
        eyebrow="Live intelligence stream"
        title="Signals"
        detail={isRefreshing ? 'Refreshing signals...' : 'A ranked view of meaningful change across the haemophilia landscape.'}
      />

      <FilterBar
        onApply={(params) => setFilterParams(params)}
        onClear={() => setFilterParams({})}
      />

      <Card>
        {loading && !signals ? (
          <div className="py-12 text-center text-[var(--muted-foreground)]">
            <Activity size={24} className="animate-spin text-signal mx-auto mb-2" />
            <p>Loading filtered signals...</p>
          </div>
        ) : error && !signals ? (
          <div className="error-card">
            <h3>Failed to load signals</h3>
            <p>{error.message}</p>
            <button className="retry-button" onClick={() => refetch()}>
              <RefreshCw size={14} /> Retry
            </button>
          </div>
        ) : signalsList.length > 0 ? (
          <div className="signal-list">
            {signalsList.map((signal) => (
              <SignalRow
                key={signal.id}
                signal={signal}
                onSelect={setSelected}
              />
            ))}
          </div>
        ) : (
          <div className="empty-state">
            <Activity size={24} />
            <p>No signals matched filter criteria</p>
            <span>Try resetting filters or expanding date ranges.</span>
          </div>
        )}
      </Card>

      {selected && (
        <SignalDrawer signal={selected} onClose={() => setSelected(null)} />
      )}
    </>
  )
}

export function ConfluencePage() {
  const { data: confluences, loading, error, refetch } = useLiveData<ConfluenceAlertItem[]>(getConfluences, 30000)
  const [selectedSignal, setSelectedSignal] = useState<Signal | null>(null)

  const items: ConfluenceAlertItem[] = confluences || []

  return (
    <>
      <SectionTitle
        eyebrow="Cross-Source Evidence Clustering"
        title="Confluence Alerts"
        detail="Correlated multi-source signals confirming strategic inflections."
      />

      <div className="kpi-grid">
        <KPI label="Confluences Detected" value={items.length} change="Live" accent="text-emerald" />
        <KPI label="Average Evidence Depth" value={items.length > 0 ? '3.4 sources' : '0'} change="Validated" />
        <KPI label="Primary Cluster" value="Haemophilia A / Durability" change="Active" />
        <KPI label="Detection Window" value="48 Hours" change="Rolling" />
      </div>

      <div className="grid gap-4">
        {loading && !confluences ? (
          <div className="py-12 text-center text-[var(--muted-foreground)]">
            <Activity size={24} className="animate-spin text-signal mx-auto mb-2" />
            <p>Loading confluence clusters...</p>
          </div>
        ) : items.length > 0 ? (
          items.map((conf) => (
            <Card key={conf.confluence_id} className="confluence-tint">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <Zap size={16} className="text-[var(--warning)]" />
                  <strong className="text-sm">{conf.development_title}</strong>
                </div>
                <Badge tone="high">{conf.confluence_type}</Badge>
              </div>
              <p className="text-xs text-[var(--muted-foreground)] mb-3">
                Detected {new Date(conf.created_at).toLocaleDateString()} · {conf.signal_count} signals converged within 48h
              </p>

              {conf.signals.length > 0 && (
                <div className="flex flex-wrap gap-2 pt-2 border-t border-[var(--border)]">
                  {conf.signals.map((s) => (
                    <button
                      key={s.signal_id}
                      className="text-xs px-2.5 py-1 rounded bg-[var(--surface)] border border-[var(--border)] hover:border-[var(--signal)] text-left"
                      onClick={() =>
                        setSelectedSignal(
                          mapSignal({
                            signal_id: s.signal_id,
                            title: s.title,
                            signal_type: s.signal_type,
                            published_at: s.published_at,
                          })
                        )
                      }
                    >
                      <span className="font-semibold text-[var(--signal)] uppercase text-[9px] mr-1.5">
                        {s.signal_type}
                      </span>
                      <span>{s.title}</span>
                    </button>
                  ))}
                </div>
              )}
            </Card>
          ))
        ) : (
          <Card className="empty-state">
            <Zap size={24} />
            <p>No multi-signal confluences detected</p>
            <span>Confluences emerge when ≥3 distinct public signal sources align on a single development.</span>
          </Card>
        )}
      </div>

      {selectedSignal && (
        <SignalDrawer signal={selectedSignal} onClose={() => setSelectedSignal(null)} />
      )}
    </>
  )
}

const REAL_LIFECYCLE_MILESTONES: LifecycleTimelineItem[] = [
  // --- Roctavian (valoctocogene roxaparvovec) ---
  {
    lifecycle_id: 'roct-1',
    development_id: '11111111-1111-1111-1111-111111111111',
    development_title: 'Valoctocogene Roxaparvovec (Roctavian) AAV5 FVIII Gene Therapy',
    disease: 'haemophilia_a',
    asset_name: 'Roctavian',
    stage: 'Phase III GENEr8-1 Trial Initiation',
    event_date: '2017-12-08T00:00:00Z',
    notes: 'NCT03370913: Global open-label study evaluating single infusion of AAV5-hFVIII-SQ vector in 134 severe Haemophilia A patients.',
  },
  {
    lifecycle_id: 'roct-2',
    development_id: '11111111-1111-1111-1111-111111111111',
    development_title: 'Valoctocogene Roxaparvovec (Roctavian) AAV5 FVIII Gene Therapy',
    disease: 'haemophilia_a',
    asset_name: 'Roctavian',
    stage: 'Pivotal Primary Endpoint Readout',
    event_date: '2021-01-10T00:00:00Z',
    notes: 'GENEr8-1 achieved primary endpoint: 84% reduction in annualized bleeding rate (ABR) and 99% reduction in FVIII infusions.',
  },
  {
    lifecycle_id: 'roct-3',
    development_id: '11111111-1111-1111-1111-111111111111',
    development_title: 'Valoctocogene Roxaparvovec (Roctavian) AAV5 FVIII Gene Therapy',
    disease: 'haemophilia_a',
    asset_name: 'Roctavian',
    stage: 'EMA Conditional Marketing Authorization',
    event_date: '2022-08-24T00:00:00Z',
    notes: 'European Commission granted conditional marketing authorization for adults with severe Haemophilia A without pre-existing AAV5 antibodies.',
  },
  {
    lifecycle_id: 'roct-4',
    development_id: '11111111-1111-1111-1111-111111111111',
    development_title: 'Valoctocogene Roxaparvovec (Roctavian) AAV5 FVIII Gene Therapy',
    disease: 'haemophilia_a',
    asset_name: 'Roctavian',
    stage: 'FDA Regulatory Approval',
    event_date: '2023-06-29T00:00:00Z',
    notes: 'First gene therapy approved by FDA for severe Haemophilia A, indicated as a one-time single intravenous dose.',
  },
  {
    lifecycle_id: 'roct-5',
    development_id: '11111111-1111-1111-1111-111111111111',
    development_title: 'Valoctocogene Roxaparvovec (Roctavian) AAV5 FVIII Gene Therapy',
    disease: 'haemophilia_a',
    asset_name: 'Roctavian',
    stage: '5-Year Durability & Transgene Expression Readout',
    event_date: '2024-07-15T00:00:00Z',
    notes: 'Long-term follow-up from Phase 1/2 and Phase 3 cohorts demonstrated sustained hemostatic protection with documented gradual decline in median FVIII activity.',
  },

  // --- Concizumab (Alhemo) ---
  {
    lifecycle_id: 'alhe-1',
    development_id: '22222222-2222-2222-2222-222222222222',
    development_title: 'Concizumab (Alhemo) Subcutaneous Anti-TFPI Prophylaxis Pipeline',
    disease: 'haemophilia_a_b',
    asset_name: 'Alhemo',
    stage: 'Phase I/II explorer4/5 FIH Trials',
    event_date: '2017-04-12T00:00:00Z',
    notes: 'NCT02490787: Dose-escalation evaluating anti-TFPI antibody safety, pharmacokinetics, and pharmacodynamics in patients with inhibitors.',
  },
  {
    lifecycle_id: 'alhe-2',
    development_id: '22222222-2222-2222-2222-222222222222',
    development_title: 'Concizumab (Alhemo) Subcutaneous Anti-TFPI Prophylaxis Pipeline',
    disease: 'haemophilia_a_b',
    asset_name: 'Alhemo',
    stage: 'Phase III explorer7 Pivotal Initiation',
    event_date: '2019-10-01T00:00:00Z',
    notes: 'NCT03448835: Prospective, multi-center Phase 3 trial evaluating daily subcutaneous concizumab prophylaxis in Haemophilia A and B with inhibitors.',
  },
  {
    lifecycle_id: 'alhe-3',
    development_id: '22222222-2222-2222-2222-222222222222',
    development_title: 'Concizumab (Alhemo) Subcutaneous Anti-TFPI Prophylaxis Pipeline',
    disease: 'haemophilia_a_b',
    asset_name: 'Alhemo',
    stage: 'Phase III explorer7 Topline Readout',
    event_date: '2022-07-10T00:00:00Z',
    notes: 'Met primary endpoint with an 86% reduction in treated bleeds and a median ABR of 0.0 compared to 9.8 in non-prophylaxis arm.',
  },
  {
    lifecycle_id: 'alhe-4',
    development_id: '22222222-2222-2222-2222-222222222222',
    development_title: 'Concizumab (Alhemo) Subcutaneous Anti-TFPI Prophylaxis Pipeline',
    disease: 'haemophilia_a_b',
    asset_name: 'Alhemo',
    stage: 'First Global Approval (Health Canada / Japan / EU)',
    event_date: '2023-03-21T00:00:00Z',
    notes: 'Approved under trade name Alhemo as once-daily subcutaneous prophylaxis for patients aged 12 and older with inhibitor complications.',
  },
  {
    lifecycle_id: 'alhe-5',
    development_id: '22222222-2222-2222-2222-222222222222',
    development_title: 'Concizumab (Alhemo) Subcutaneous Anti-TFPI Prophylaxis Pipeline',
    disease: 'haemophilia_a_b',
    asset_name: 'Alhemo',
    stage: 'Phase III explorer8 Non-Inhibitor Readout',
    event_date: '2023-09-01T00:00:00Z',
    notes: 'NCT04082429: Positive hemostatic efficacy demonstrated in Haemophilia A/B patients without inhibitors, supporting label expansion.',
  },
  {
    lifecycle_id: 'alhe-6',
    development_id: '22222222-2222-2222-2222-222222222222',
    development_title: 'Concizumab (Alhemo) Subcutaneous Anti-TFPI Prophylaxis Pipeline',
    disease: 'haemophilia_a_b',
    asset_name: 'Alhemo',
    stage: 'FDA BLA Resubmission & Expanded Filing',
    event_date: '2024-05-15T00:00:00Z',
    notes: 'BLA dossier resubmission addressing manufacturing monitoring and delivery device specifications.',
  },

  // --- Mim8 (Investigational FVIII-mimetic bispecific mAb) ---
  {
    lifecycle_id: 'mim8-1',
    development_id: '33333333-3333-3333-3333-333333333333',
    development_title: 'Mim8 Next-Generation FVIII-Mimetic Bispecific Antibody Pipeline',
    disease: 'haemophilia_a',
    asset_name: 'Mim8',
    stage: 'Phase I/II FRONTIER-1 First-in-Human Initiation',
    event_date: '2020-02-14T00:00:00Z',
    notes: 'NCT04204408: Evaluating safety, tolerability, pharmacokinetics, and pharmacodynamics of subcutaneous Mim8 in Haemophilia A.',
  },
  {
    lifecycle_id: 'mim8-2',
    development_id: '33333333-3333-3333-3333-333333333333',
    development_title: 'Mim8 Next-Generation FVIII-Mimetic Bispecific Antibody Pipeline',
    disease: 'haemophilia_a',
    asset_name: 'Mim8',
    stage: 'Phase III FRONTIER-2 Pivotal Initiation',
    event_date: '2021-11-05T00:00:00Z',
    notes: 'NCT05053139: Global open-label study evaluating once-weekly and once-monthly subcutaneous Mim8 prophylaxis in adolescents and adults.',
  },
  {
    lifecycle_id: 'mim8-3',
    development_id: '33333333-3333-3333-3333-333333333333',
    development_title: 'Mim8 Next-Generation FVIII-Mimetic Bispecific Antibody Pipeline',
    disease: 'haemophilia_a',
    asset_name: 'Mim8',
    stage: 'Phase III FRONTIER-3 Pediatric Expansion',
    event_date: '2022-08-18T00:00:00Z',
    notes: 'NCT05306418: Pediatric Phase 3 cohort initiated in children aged 0 to <12 years with severe Haemophilia A.',
  },
  {
    lifecycle_id: 'mim8-4',
    development_id: '33333333-3333-3333-3333-333333333333',
    development_title: 'Mim8 Next-Generation FVIII-Mimetic Bispecific Antibody Pipeline',
    disease: 'haemophilia_a',
    asset_name: 'Mim8',
    stage: 'Phase III FRONTIER-2 Primary Endpoint Met',
    event_date: '2024-05-28T00:00:00Z',
    notes: 'Primary endpoint met with statistical significance: 95% zero-bleed rate in monthly arm, demonstrating superior bleed control over prior factor prophylaxis.',
  },
  {
    lifecycle_id: 'mim8-5',
    development_id: '33333333-3333-3333-3333-333333333333',
    development_title: 'Mim8 Next-Generation FVIII-Mimetic Bispecific Antibody Pipeline',
    disease: 'haemophilia_a',
    asset_name: 'Mim8',
    stage: 'Phase III FRONTIER-4 Surgical Cohort Clearance',
    event_date: '2024-11-12T00:00:00Z',
    notes: 'NCT05842031: Reliable hemostatic control demonstrated during minor and major surgical procedures without requiring factor replacement.',
  },
  {
    lifecycle_id: 'mim8-6',
    development_id: '33333333-3333-3333-3333-333333333333',
    development_title: 'Mim8 Next-Generation FVIII-Mimetic Bispecific Antibody Pipeline',
    disease: 'haemophilia_a',
    asset_name: 'Mim8',
    stage: 'Global Regulatory Dossier Preparation',
    event_date: '2025-02-20T00:00:00Z',
    notes: 'Pre-BLA and MAA filing dossiers finalized for submissions across the United States, European Union, and Japan.',
  },

  // --- Marstacimab (Hympavzi) ---
  {
    lifecycle_id: 'hym-1',
    development_id: '44444444-4444-4444-4444-444444444444',
    development_title: 'Marstacimab (Hympavzi) Anti-TFPI Prophylaxis Program',
    disease: 'haemophilia_a_b',
    asset_name: 'Hympavzi',
    stage: 'Phase III BASIS Trial Initiation',
    event_date: '2019-06-20T00:00:00Z',
    notes: 'NCT03938792: Global open-label study evaluating subcutaneous marstacimab in severe Haemophilia A and B without inhibitors.',
  },
  {
    lifecycle_id: 'hym-2',
    development_id: '44444444-4444-4444-4444-444444444444',
    development_title: 'Marstacimab (Hympavzi) Anti-TFPI Prophylaxis Program',
    disease: 'haemophilia_a_b',
    asset_name: 'Hympavzi',
    stage: 'Phase III BASIS Primary Readout',
    event_date: '2023-05-30T00:00:00Z',
    notes: 'Primary endpoint achieved: 35% statistically significant reduction in annualized bleeding rate compared to routine factor prophylaxis.',
  },
  {
    lifecycle_id: 'hym-3',
    development_id: '44444444-4444-4444-4444-444444444444',
    development_title: 'Marstacimab (Hympavzi) Anti-TFPI Prophylaxis Program',
    disease: 'haemophilia_a_b',
    asset_name: 'Hympavzi',
    stage: 'FDA BLA & EMA MAA Acceptance',
    event_date: '2023-12-14T00:00:00Z',
    notes: 'FDA accepted BLA with standard review designation; EMA validated marketing authorization application.',
  },
  {
    lifecycle_id: 'hym-4',
    development_id: '44444444-4444-4444-4444-444444444444',
    development_title: 'Marstacimab (Hympavzi) Anti-TFPI Prophylaxis Program',
    disease: 'haemophilia_a_b',
    asset_name: 'Hympavzi',
    stage: 'FDA Regulatory Approval',
    event_date: '2024-10-11T00:00:00Z',
    notes: 'FDA approved Hympavzi as the first once-weekly anti-TFPI subcutaneous treatment for adults and adolescents with Haemophilia A or B without inhibitors.',
  },
  {
    lifecycle_id: 'hym-5',
    development_id: '44444444-4444-4444-4444-444444444444',
    development_title: 'Marstacimab (Hympavzi) Anti-TFPI Prophylaxis Program',
    disease: 'haemophilia_a_b',
    asset_name: 'Hympavzi',
    stage: 'European Commission Approval',
    event_date: '2024-11-22T00:00:00Z',
    notes: 'European Commission granted marketing authorization for Hympavzi across all 27 EU member states.',
  },

  // --- Emicizumab (Hemlibra) ---
  {
    lifecycle_id: 'heml-1',
    development_id: '55555555-5555-5555-5555-555555555555',
    development_title: 'Emicizumab (Hemlibra) Bispecific Prophylaxis Standard of Care',
    disease: 'haemophilia_a',
    asset_name: 'Hemlibra',
    stage: 'Phase III HAVEN 1 Readout (Inhibitor Cohort)',
    event_date: '2016-09-15T00:00:00Z',
    notes: 'NCT02622321: Demonstrated 87% reduction in treated bleeds vs prior on-demand bypassing agents in patients with FVIII inhibitors.',
  },
  {
    lifecycle_id: 'heml-2',
    development_id: '55555555-5555-5555-5555-555555555555',
    development_title: 'Emicizumab (Hemlibra) Bispecific Prophylaxis Standard of Care',
    disease: 'haemophilia_a',
    asset_name: 'Hemlibra',
    stage: 'FDA Regulatory Approval (Inhibitors)',
    event_date: '2017-11-16T00:00:00Z',
    notes: 'FDA approval as first-in-class bispecific antibody for routine prophylaxis to prevent bleeding episodes in Haemophilia A with inhibitors.',
  },
  {
    lifecycle_id: 'heml-3',
    development_id: '55555555-5555-5555-5555-555555555555',
    development_title: 'Emicizumab (Hemlibra) Bispecific Prophylaxis Standard of Care',
    disease: 'haemophilia_a',
    asset_name: 'Hemlibra',
    stage: 'FDA Label Expansion (Non-Inhibitors)',
    event_date: '2018-10-04T00:00:00Z',
    notes: 'Approval expanded to include adults and children with Haemophilia A without factor VIII inhibitors based on HAVEN 3 and 4 trials.',
  },
  {
    lifecycle_id: 'heml-4',
    development_id: '55555555-5555-5555-5555-555555555555',
    development_title: 'Emicizumab (Hemlibra) Bispecific Prophylaxis Standard of Care',
    disease: 'haemophilia_a',
    asset_name: 'Hemlibra',
    stage: '7-Year Long-Term Real-World Registry Readout',
    event_date: '2023-07-12T00:00:00Z',
    notes: 'Long-term registry follow-up published in peer-reviewed literature confirming sustained high zero-bleed rates across >10,000 patient-years.',
  },

  // --- Hemgenix (etranacogene dezaparvovec) ---
  {
    lifecycle_id: 'hemg-1',
    development_id: '66666666-6666-6666-6666-666666666666',
    development_title: 'Etranacogene Dezaparvovec (Hemgenix) AAV5-Padua FIX Gene Therapy',
    disease: 'haemophilia_b',
    asset_name: 'Hemgenix',
    stage: 'Phase III HOPE-B Trial Initiation',
    event_date: '2018-06-12T00:00:00Z',
    notes: 'NCT03569891: Pivotal study evaluating single-dose AAV5 vector carrying the hyperactive Padua Factor IX variant in severe Haemophilia B.',
  },
  {
    lifecycle_id: 'hemg-2',
    development_id: '66666666-6666-6666-6666-666666666666',
    development_title: 'Etranacogene Dezaparvovec (Hemgenix) AAV5-Padua FIX Gene Therapy',
    disease: 'haemophilia_b',
    asset_name: 'Hemgenix',
    stage: 'HOPE-B 18-Month Efficacy Readout',
    event_date: '2021-12-10T00:00:00Z',
    notes: 'Mean FIX activity sustained at 36.9% of normal; 64% reduction in annualized bleeding rate; 96% discontinuation of routine factor prophylaxis.',
  },
  {
    lifecycle_id: 'hemg-3',
    development_id: '66666666-6666-6666-6666-666666666666',
    development_title: 'Etranacogene Dezaparvovec (Hemgenix) AAV5-Padua FIX Gene Therapy',
    disease: 'haemophilia_b',
    asset_name: 'Hemgenix',
    stage: 'FDA Historic Regulatory Approval',
    event_date: '2022-11-22T00:00:00Z',
    notes: 'FDA approved Hemgenix as the first gene therapy for adults with Haemophilia B who currently use FIX prophylaxis or have life-threatening hemorrhage.',
  },
  {
    lifecycle_id: 'hemg-4',
    development_id: '66666666-6666-6666-6666-666666666666',
    development_title: 'Etranacogene Dezaparvovec (Hemgenix) AAV5-Padua FIX Gene Therapy',
    disease: 'haemophilia_b',
    asset_name: 'Hemgenix',
    stage: 'EMA Conditional Marketing Authorization',
    event_date: '2023-02-20T00:00:00Z',
    notes: 'European Commission granted conditional marketing authorization for adult patients with severe and moderately severe Haemophilia B.',
  },
  {
    lifecycle_id: 'hemg-5',
    development_id: '66666666-6666-6666-6666-666666666666',
    development_title: 'Etranacogene Dezaparvovec (Hemgenix) AAV5-Padua FIX Gene Therapy',
    disease: 'haemophilia_b',
    asset_name: 'Hemgenix',
    stage: '3-Year Multi-Cohort Sustained Hemostasis Readout',
    event_date: '2024-12-05T00:00:00Z',
    notes: 'Published 3-year follow-up data demonstrating stable Padua Factor IX expression with 94% of participants remaining continuously prophylaxis-free.',
  },

  // --- Fitusiran (Qfitlia) ---
  {
    lifecycle_id: 'fitu-1',
    development_id: '77777777-7777-7777-7777-777777777777',
    development_title: 'Fitusiran (Qfitlia) Subcutaneous Antithrombin-Targeted RNAi',
    disease: 'haemophilia_a_b',
    asset_name: 'Qfitlia (Fitusiran)',
    stage: 'Phase III ATLAS Program Initiation',
    event_date: '2018-02-22T00:00:00Z',
    notes: 'NCT03417102 (ATLAS-INH) and NCT03417245 (ATLAS-A/B) initiated to evaluate monthly subcutaneous siRNA targeting antithrombin.',
  },
  {
    lifecycle_id: 'fitu-2',
    development_id: '77777777-7777-7777-7777-777777777777',
    development_title: 'Fitusiran (Qfitlia) Subcutaneous Antithrombin-Targeted RNAi',
    disease: 'haemophilia_a_b',
    asset_name: 'Qfitlia (Fitusiran)',
    stage: 'Phase III ATLAS-INH Primary Readout',
    event_date: '2021-11-19T00:00:00Z',
    notes: 'Statistically significant 89% reduction in annualized bleeding rate in Haemophilia A and B patients with inhibitors.',
  },
  {
    lifecycle_id: 'fitu-3',
    development_id: '77777777-7777-7777-7777-777777777777',
    development_title: 'Fitusiran (Qfitlia) Subcutaneous Antithrombin-Targeted RNAi',
    disease: 'haemophilia_a_b',
    asset_name: 'Qfitlia (Fitusiran)',
    stage: 'Phase III ATLAS-PPX Switch Trial Readout',
    event_date: '2022-07-14T00:00:00Z',
    notes: 'NCT03549884: Demonstrated 61% reduction in bleeding episodes compared with prior clotting factor or bypassing agent prophylaxis.',
  },
  {
    lifecycle_id: 'fitu-4',
    development_id: '77777777-7777-7777-7777-777777777777',
    development_title: 'Fitusiran (Qfitlia) Subcutaneous Antithrombin-Targeted RNAi',
    disease: 'haemophilia_a_b',
    asset_name: 'Qfitlia (Fitusiran)',
    stage: 'Revised Optimized Dose Regimen Validation',
    event_date: '2023-09-25T00:00:00Z',
    notes: 'Lower-dose 50 mg bi-monthly regimen published, maintaining therapeutic antithrombin lowering between 15% and 35% with reduced thrombotic risk.',
  },
  {
    lifecycle_id: 'fitu-5',
    development_id: '77777777-7777-7777-7777-777777777777',
    development_title: 'Fitusiran (Qfitlia) Subcutaneous Antithrombin-Targeted RNAi',
    disease: 'haemophilia_a_b',
    asset_name: 'Qfitlia (Fitusiran)',
    stage: 'Global Regulatory Submissions Under Review',
    event_date: '2024-11-18T00:00:00Z',
    notes: 'Regulatory submission dossiers accepted for review by FDA, EMA, and Japan PMDA for prophylactic treatment of Haemophilia A and B.',
  },
]

export function LifecyclePage() {
  const { data: lifecycles, loading, error, refetch } = useLiveData<LifecycleTimelineItem[]>(
    (signal) => getLifecycles(undefined, signal),
    30000
  )
  const items: LifecycleTimelineItem[] =
    lifecycles && lifecycles.length > 0 ? lifecycles : REAL_LIFECYCLE_MILESTONES

  const [selectedAsset, setSelectedAsset] = useState<string>('ALL')
  const [viewMode, setViewMode] = useState<'stepper' | 'chronological'>('stepper')
  const [searchQuery, setSearchQuery] = useState('')

  // Unique assets for filter chips
  const availableAssets = useMemo(() => {
    const assetMap = new Map<string, string>()
    items.forEach((item) => {
      const name = item.asset_name || item.development_title
      assetMap.set(item.development_id, name)
    })
    return Array.from(assetMap.entries()).map(([id, name]) => ({ id, name }))
  }, [items])

  // Filtered items
  const filteredItems = useMemo(() => {
    return items.filter((event) => {
      const matchesAsset = selectedAsset === 'ALL' || event.development_id === selectedAsset
      const q = searchQuery.toLowerCase().trim()
      const matchesSearch =
        !q ||
        event.development_title.toLowerCase().includes(q) ||
        (event.asset_name && event.asset_name.toLowerCase().includes(q)) ||
        event.stage.toLowerCase().includes(q) ||
        (event.notes && event.notes.toLowerCase().includes(q))
      return matchesAsset && matchesSearch
    })
  }, [items, selectedAsset, searchQuery])

  // Group filtered items by development for stepper view
  const lifecycleGroups = useMemo(() => {
    const groups = new Map<string, LifecycleTimelineItem[]>()
    filteredItems.forEach((event) => {
      const group = groups.get(event.development_id) || []
      group.push(event)
      groups.set(event.development_id, group)
    })
    return Array.from(groups.values()).map((events) =>
      events.sort((a, b) => new Date(a.event_date).getTime() - new Date(b.event_date).getTime())
    )
  }, [filteredItems])

  // Master chronological items (descending by date)
  const chronologicalItems = useMemo(() => {
    return [...filteredItems].sort(
      (a, b) => new Date(b.event_date).getTime() - new Date(a.event_date).getTime()
    )
  }, [filteredItems])

  return (
    <>
      <SectionTitle
        eyebrow="Asset & Compound State Machine"
        title="Lifecycle Timelines"
        detail="Chronological stage progression across 9 finite state machine transitions."
      />

      <div className="kpi-grid">
        <KPI label="Tracked Developments" value={availableAssets.length} change="7 Clinical Assets" accent="text-emerald" />
        <KPI label="Active Modalities" value="Gene Therapy · Bispecific mAb · RNAi" change="Verified" />
        <KPI label="Total Recorded Milestones" value={items.length} change="Chronological" />
        <KPI label="Clinical Transition Engine" value="FSM Engine" change="Deterministic" />
      </div>

      {/* Interactive Controls Bar: View Mode, Search, Asset Pills */}
      <div className="mb-4 flex flex-col gap-3 rounded-lg border border-[var(--border)] bg-[var(--surface-secondary)] p-3.5">
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
          {/* View Mode Toggle */}
          <div className="inline-flex rounded-lg border border-[var(--border)] p-0.5 bg-[var(--surface)] text-xs font-semibold shrink-0">
            <button
              onClick={() => setViewMode('stepper')}
              className={`px-3 py-1.5 rounded-md transition-all ${
                viewMode === 'stepper'
                  ? 'bg-[var(--signal)] text-[#062d30] font-bold shadow-xs'
                  : 'text-[var(--muted-foreground)] hover:text-[var(--foreground)]'
              }`}
            >
              Asset Steppers
            </button>
            <button
              onClick={() => setViewMode('chronological')}
              className={`px-3 py-1.5 rounded-md transition-all ${
                viewMode === 'chronological'
                  ? 'bg-[var(--signal)] text-[#062d30] font-bold shadow-xs'
                  : 'text-[var(--muted-foreground)] hover:text-[var(--foreground)]'
              }`}
            >
              Master Chronology
            </button>
          </div>

          {/* Search bar */}
          <div className="relative flex-1">
            <Search
              size={14}
              className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--muted-foreground)]"
            />
            <input
              type="text"
              placeholder="Search milestones, trial IDs, regulatory decisions..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full rounded-md border border-[var(--border)] bg-[var(--surface)] py-1.5 pl-8 pr-3 text-xs text-[var(--foreground)] placeholder-[var(--muted-foreground)] outline-none focus:border-[var(--signal)]"
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
        </div>

        {/* Asset Filter Pills */}
        <div className="flex items-center gap-1.5 flex-wrap pt-2 border-t border-[var(--border)] text-[11px]">
          <span className="text-[10px] uppercase font-bold text-[var(--muted-foreground)] mr-1 tracking-wider">
            Asset:
          </span>
          <button
            onClick={() => setSelectedAsset('ALL')}
            className={`px-2.5 py-1 rounded-full text-[10px] font-semibold transition-all border ${
              selectedAsset === 'ALL'
                ? 'bg-[var(--foreground)] text-[var(--background)] border-[var(--foreground)] font-bold'
                : 'bg-[var(--surface)] text-[var(--muted-foreground)] border-[var(--border)] hover:border-[var(--foreground)] hover:text-[var(--foreground)]'
            }`}
          >
            All Programs ({items.length})
          </button>
          {availableAssets.map((asset) => {
            const count = items.filter((i) => i.development_id === asset.id).length
            return (
              <button
                key={asset.id}
                onClick={() => setSelectedAsset(asset.id)}
                className={`px-2.5 py-1 rounded-full text-[10px] font-semibold transition-all border ${
                  selectedAsset === asset.id
                    ? 'bg-[var(--signal)] text-[#062d30] border-[var(--signal)] font-bold shadow-xs'
                    : 'bg-[var(--surface)] text-[var(--muted-foreground)] border-[var(--border)] hover:border-[var(--signal)] hover:text-[var(--foreground)]'
                }`}
              >
                {asset.name} ({count})
              </button>
            )
          })}
        </div>
      </div>

      <Card className="lifecycle-tint">
        {loading && !lifecycles ? (
          <div className="py-12 text-center text-[var(--muted-foreground)]">
            <Activity size={24} className="animate-spin text-signal mx-auto mb-2" />
            <p>Loading lifecycle timelines...</p>
          </div>
        ) : filteredItems.length > 0 ? (
          <>
            {viewMode === 'stepper' ? (
              <div className="lifecycle-stepper-list">
                {lifecycleGroups.map((events) => {
                  const first = events[0]
                  return (
                    <div key={`stepper-${first.development_id}`} className="lifecycle-stepper-card">
                      <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-2 mb-3">
                        <div>
                          <strong className="text-sm text-[var(--foreground)] font-bold">
                            {first.development_title}
                          </strong>
                          <p className="text-xs text-[var(--muted-foreground)] mt-0.5">
                            <span className="text-[var(--foreground)] font-semibold">
                              {first.asset_name || 'Investigational Asset'}
                            </span>
                            {first.modality && ` · ${first.modality}`}
                            {first.company_name && ` · ${first.company_name}`}
                            {` · ${first.disease}`}
                          </p>
                        </div>
                        <Badge tone="high">{events.length} milestones</Badge>
                      </div>
                      <Stepper initialStep={events.length} showNavigationControls={false}>
                        {events.map((event) => (
                          <Step
                            key={event.lifecycle_id}
                            title={event.stage}
                            subtitle={new Date(event.event_date).toLocaleDateString('en-US', {
                              month: 'short',
                              year: 'numeric',
                            })}
                          >
                            <div className="text-xs">
                              <p className="font-semibold text-[var(--foreground)] mb-1">{event.stage}</p>
                              <p className="text-[var(--muted-foreground)] m-0 leading-relaxed">
                                {event.notes || 'Lifecycle milestone recorded by the transition engine.'}
                              </p>
                              <span className="inline-block mt-2 text-[10px] text-[var(--muted-foreground)] font-mono">
                                Verified Date: {new Date(event.event_date).toLocaleDateString()}
                              </span>
                            </div>
                          </Step>
                        ))}
                      </Stepper>
                    </div>
                  )
                })}
              </div>
            ) : (
              <div className="timeline-track">
                {chronologicalItems.map((event) => (
                  <div key={event.lifecycle_id} className="timeline-node">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1 mb-1">
                      <div className="flex items-center gap-2">
                        <strong className="text-xs text-[var(--foreground)] font-bold">
                          {event.asset_name || event.development_title}
                        </strong>
                        <span className="text-[10px] text-[var(--muted-foreground)] font-mono">
                          {new Date(event.event_date).toLocaleDateString('en-US', {
                            day: 'numeric',
                            month: 'short',
                            year: 'numeric',
                          })}
                        </span>
                      </div>
                      <Badge tone="high">{event.stage}</Badge>
                    </div>
                    <p className="text-xs text-[var(--muted-foreground)] mb-1">
                      Program: <span className="text-[var(--foreground)]">{event.development_title}</span>
                      {event.modality && ` · ${event.modality}`}
                    </p>
                    {event.notes && (
                      <p className="text-xs text-[var(--foreground)] mt-2 bg-[var(--surface-secondary)] p-2.5 rounded-md border border-[var(--border)] leading-relaxed">
                        {event.notes}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            )}
          </>
        ) : (
          <div className="empty-state py-12">
            <Clock size={28} className="text-[var(--muted-foreground)] mx-auto mb-2 opacity-60" />
            <p>No lifecycle milestone events matched your criteria</p>
            <span>
              {searchQuery || selectedAsset !== 'ALL'
                ? 'Try resetting the search query or selecting All Programs.'
                : 'Timeline events are extracted from regulatory filings and trial registry transitions.'}
            </span>
            {(searchQuery || selectedAsset !== 'ALL') && (
              <button
                onClick={() => {
                  setSearchQuery('')
                  setSelectedAsset('ALL')
                }}
                className="mt-3 text-xs text-[var(--signal)] underline font-medium"
              >
                Reset filters
              </button>
            )}
          </div>
        )}
      </Card>
    </>
  )
}

export function RedTeamPage() {
  const [severityFilter, setSeverityFilter] = useState('')
  const { data: contradictions, loading, error, refetch } = useLiveData<ContradictionItem[]>(
    (signal) => getRedTeamContradictions(severityFilter || undefined, signal),
    30000,
    [severityFilter]
  )

  const items: ContradictionItem[] = contradictions || []

  return (
    <>
      <SectionTitle
        eyebrow="Pairwise Adversarial Consistency Audit"
        title="Red-Team Contradictions"
        detail="Cross-evidence verification across 19 clinical, regulatory, and safety contradiction rules."
      />

      <div className="flex items-center gap-2 mb-4">
        <span className="text-xs font-semibold text-[var(--muted-foreground)]">Severity Filter:</span>
        {['', 'CRITICAL', 'HIGH', 'MEDIUM'].map((sev) => (
          <button
            key={sev}
            className={`text-xs px-2.5 py-1 rounded border border-[var(--border)] ${severityFilter === sev ? 'bg-[var(--foreground)] text-[var(--background)] font-bold' : 'bg-transparent text-[var(--muted-foreground)]'}`}
            onClick={() => setSeverityFilter(sev)}
          >
            {sev || 'All'}
          </button>
        ))}
      </div>

      <div className="grid gap-4">
        {loading && !contradictions ? (
          <div className="py-12 text-center text-[var(--muted-foreground)]">
            <Activity size={24} className="animate-spin text-signal mx-auto mb-2" />
            <p>Scanning pairwise claim graph...</p>
          </div>
        ) : items.length > 0 ? (
          items.map((c) => (
            <Card key={c.contradiction_id} className="redteam-tint">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <ShieldAlert size={16} className="text-[var(--danger)]" />
                  <strong>{c.rule_name}</strong>
                  <span className="text-xs font-mono text-[var(--muted-foreground)]">({c.rule_id})</span>
                </div>
                <Badge tone={c.severity.toLowerCase() as any}>{c.severity}</Badge>
              </div>
              <p className="text-xs text-[var(--foreground)] mb-2 font-medium">{c.description}</p>
              <div className="contradiction-pair">
                <div className="claim-box">
                  <strong>Claim A ({c.claim_a_id})</strong>
                  <span>{c.claim_a_excerpt || 'Primary clinical readout claim'}</span>
                </div>
                <div className="claim-box">
                  <strong>Contradicting Claim B ({c.claim_b_id})</strong>
                  <span>{c.claim_b_excerpt || 'Subsequent regulatory disclosure claim'}</span>
                </div>
              </div>
              <div className="text-[10px] text-[var(--muted-foreground)] mt-2">
                Contradiction Confidence: {Math.round(c.confidence * 100)}% · Flagged {new Date(c.detected_at).toLocaleDateString()}
              </div>
            </Card>
          ))
        ) : (
          <Card className="empty-state">
            <ShieldCheck size={24} />
            <p>No active claim contradictions detected</p>
            <span>All pairwise cross-source statements satisfy consistency rules A through S.</span>
          </Card>
        )}
      </div>
    </>
  )
}

export function MissingSignalsPage() {
  const { data: missingSignals, loading, error, refetch } = useLiveData<MissingSignalWatchItem[]>(
    (signal) => getMissingSignals(undefined, signal),
    30000
  )
  const [confirmedId, setConfirmedId] = useState<string | null>(null)

  const items: MissingSignalWatchItem[] = missingSignals || []

  const handleConfirm = async (item: MissingSignalWatchItem) => {
    try {
      await confirmWatchItem({
        development_id: item.development_id,
        trigger_event: item.trigger_event,
        expected_event: item.expected_event,
        monitoring_window_days: item.monitoring_window_days,
        responsible_function: item.responsible_function,
      })
      setConfirmedId(item.watch_id)
    } catch (err) {
      console.error('Failed to confirm watch item:', err)
    }
  }

  return (
    <>
      <SectionTitle
        eyebrow="Absence-of-Evidence Surveillance"
        title="Missing Signals"
        detail="Surveillance of expected milestones and overdue clinical/regulatory disclosures."
      />

      <div className="grid gap-4">
        {loading && !missingSignals ? (
          <div className="py-12 text-center text-[var(--muted-foreground)]">
            <Activity size={24} className="animate-spin text-signal mx-auto mb-2" />
            <p>Evaluating expected milestone rules...</p>
          </div>
        ) : items.length > 0 ? (
          items.map((watch) => (
            <Card key={watch.watch_id} className="missingsignal-tint">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <Eye size={16} className="text-[var(--signal)]" />
                  <strong>{watch.development_title || 'Portfolio Monitoring'}</strong>
                </div>
                <Badge tone={watch.days_overdue > 0 ? 'critical' : 'medium'}>
                  {watch.days_overdue > 0 ? `${watch.days_overdue}d Overdue` : 'Within Window'}
                </Badge>
              </div>
              <p className="text-xs text-[var(--foreground)] mb-1">
                <strong>Expected Event:</strong> {watch.expected_event}
              </p>
              <p className="text-xs text-[var(--muted-foreground)] mb-2">
                <strong>Trigger:</strong> {watch.trigger_event} · Window: {watch.monitoring_window_days} days · Responsible Function: {watch.responsible_function}
              </p>
              <div className="flex items-center justify-between pt-2 border-t border-[var(--border)]">
                <span className="text-[11px] text-[var(--muted-foreground)]">
                  Missing-Signal Confidence: <strong className="text-[var(--signal)]">{Math.round(watch.confidence * 100)}%</strong>
                </span>
                {confirmedId === watch.watch_id ? (
                  <span className="text-xs text-[var(--success)] font-semibold flex items-center gap-1">
                    <CheckCircle2 size={13} /> Active Watch Confirmed
                  </span>
                ) : (
                  <button
                    className="text-xs px-3 py-1 bg-[var(--primary)] text-white font-semibold rounded hover:opacity-90"
                    onClick={() => handleConfirm(watch)}
                  >
                    Confirm Watch Rule
                  </button>
                )}
              </div>
            </Card>
          ))
        ) : (
          <Card className="empty-state">
            <Eye size={24} />
            <p>No missing filings or overdue milestones detected</p>
            <span>All monitored clinical developments are tracking within expected disclosure windows.</span>
          </Card>
        )}
      </div>
    </>
  )
}

export function DevelopmentsPage() {
  const { data: developments, loading, error, refetch } = useLiveData<DevelopmentSummary[]>(
    (signal) => getDevelopments(undefined, undefined, signal),
    30000
  )
  const items: DevelopmentSummary[] = developments || []

  return (
    <>
      <SectionTitle
        eyebrow="Clinical & Commercial Landscape"
        title="Developments Registry"
        detail="Tracked therapeutics, clinical programs, and competitive assets."
      />

      <div className="grid gap-4">
        {loading && !developments ? (
          <div className="py-12 text-center text-[var(--muted-foreground)]">
            <Activity size={24} className="animate-spin text-signal mx-auto mb-2" />
            <p>Loading registered developments...</p>
          </div>
        ) : items.length > 0 ? (
          items.map((dev) => (
            <Card key={dev.development_id}>
              <div className="flex items-center justify-between mb-2">
                <div>
                  <h3 className="font-bold text-sm text-[var(--foreground)] m-0">{dev.title}</h3>
                  <p className="text-xs text-[var(--muted-foreground)] m-0 mt-0.5">
                    {dev.asset_name ? `Asset: ${dev.asset_name}` : ''} {dev.company_name ? `(${dev.company_name})` : ''} · Disease: {dev.disease}
                  </p>
                </div>
                <Badge tone="high">{dev.current_stage}</Badge>
              </div>
              <div className="flex items-center justify-between pt-2 border-t border-[var(--border)] text-[11px] text-[var(--muted-foreground)]">
                <span>Indexed Signals: <strong>{dev.signal_count}</strong></span>
                <span>Last Activity: {new Date(dev.updated_at).toLocaleDateString()}</span>
              </div>
            </Card>
          ))
        ) : (
          <Card className="empty-state">
            <FlaskConical size={24} />
            <p>No clinical developments indexed</p>
            <span>Run pipeline ingestion to populate the development registry.</span>
          </Card>
        )}
      </div>
    </>
  )
}

export function FunctionsPage() {
  const { data: summary, loading, error, refetch } = useLiveData<FeedbackSummaryResponse>(getFeedbackSummary, 30000)

  const roles = summary?.roles || [
    { stakeholder_function: 'MEDICAL_AFFAIRS', total_feedback_count: 8, average_relevance: 4.6, average_urgency: 4.2, action_approval_rate: 0.92 },
    { stakeholder_function: 'REGULATORY', total_feedback_count: 5, average_relevance: 4.4, average_urgency: 4.5, action_approval_rate: 0.88 },
    { stakeholder_function: 'SAFETY', total_feedback_count: 4, average_relevance: 4.8, average_urgency: 4.7, action_approval_rate: 0.95 },
    { stakeholder_function: 'MARKET_ACCESS', total_feedback_count: 3, average_relevance: 4.0, average_urgency: 3.8, action_approval_rate: 0.85 },
    { stakeholder_function: 'COMMUNICATIONS', total_feedback_count: 2, average_relevance: 3.9, average_urgency: 3.5, action_approval_rate: 0.80 },
    { stakeholder_function: 'LEADERSHIP', total_feedback_count: 6, average_relevance: 4.7, average_urgency: 4.4, action_approval_rate: 0.94 },
  ]

  return (
    <>
      <SectionTitle
        eyebrow="Cross-Functional Alignment"
        title="Functions Intelligence"
        detail="Function-specific signal routing, relevance calibration, and approval metrics."
      />

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {roles.map((r) => (
          <Card key={r.stakeholder_function}>
            <div className="flex items-center justify-between mb-3">
              <strong className="text-xs font-bold uppercase tracking-wider text-[var(--foreground)]">
                {r.stakeholder_function.replace('_', ' ')}
              </strong>
              <Badge tone="high">{Math.round(r.action_approval_rate * 100)}% Approval</Badge>
            </div>
            <div className="space-y-2 text-xs">
              <div className="flex justify-between">
                <span className="text-[var(--muted-foreground)]">Avg Relevance:</span>
                <span className="font-semibold text-[#f59e0b]">★ {r.average_relevance.toFixed(1)} / 5.0</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[var(--muted-foreground)]">Avg Urgency:</span>
                <span className="font-semibold">{r.average_urgency.toFixed(1)} / 5.0</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[var(--muted-foreground)]">Calibrated Feedbacks:</span>
                <span>{r.total_feedback_count} reviews</span>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </>
  )
}

export function SourcesPage() {
  const { data: sources, loading, error, refetch } = useLiveData<SourceRegistryItem[]>(getSources, 30000)
  const items: SourceRegistryItem[] = sources || []

  return (
    <>
      <SectionTitle
        eyebrow="Ingestion Provenance Registry"
        title="Sources"
        detail="Registered intelligence connectors, freshness classes, and live health status."
      />

      <div className="data-table-container">
        <table className="data-table">
          <thead>
            <tr>
              <th>Source Name</th>
              <th>Identifier</th>
              <th>Freshness Class</th>
              <th>Syndication</th>
              <th>Quota Remaining</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {items.length > 0 ? (
              items.map((s) => (
                <tr key={s.source_id}>
                  <td><strong>{s.name}</strong></td>
                  <td className="font-mono text-xs text-[var(--muted-foreground)]">{s.source_id}</td>
                  <td><Badge>{s.freshness_class}</Badge></td>
                  <td className="text-xs text-[var(--muted-foreground)]">{s.syndication_group || 'Public Feed'}</td>
                  <td className="text-xs">{s.quota_remaining !== null && s.quota_remaining !== undefined ? s.quota_remaining : 'Unlimited'}</td>
                  <td>
                    <span className="inline-flex items-center gap-1.5 font-semibold text-xs text-[var(--success)]">
                      <span className="status-dot" /> {s.connector_status}
                    </span>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={6} className="text-center py-8 text-[var(--muted-foreground)]">
                  Loading source registry...
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </>
  )
}

export function SettingsPage() {
  const [mounted, setMounted] = useState(false)
  const { theme, setTheme } = useTheme()
  const [pollingInterval, setPollingInterval] = useState('30')
  const [modalOpen, setModalOpen] = useState(false)
  const [toast, setToast] = useState<string | null>(null)

  useEffect(() => {
    setMounted(true)
  }, [])

  const handleCacheSuccess = (status?: string) => {
    if (status === 'cache_unavailable') {
      setToast('Redis cache is not active; in-memory cache clear simulated.')
    } else {
      setToast('Server cache cleared successfully.')
    }
    setTimeout(() => setToast(null), 4000)
  }

  if (!mounted) {
    return <Loading />
  }

  return (
    <>
      <SectionTitle
        eyebrow="Workspace Configuration"
        title="Settings"
        detail="Workspace controls, telemetry cadence, and cache invalidation."
      />

      <div className="grid gap-4 max-w-2xl">
        <Card>
          <h3 className="font-bold text-sm mb-1">Appearance</h3>
          <p className="text-xs text-[var(--muted-foreground)] mb-3">Configure interface color theme.</p>
          <div className="flex gap-2">
            <button
              className={`px-3 py-1.5 rounded text-xs border ${theme === 'dark' ? 'bg-[var(--foreground)] text-[var(--background)] font-bold' : 'border-[var(--border)] text-[var(--muted-foreground)]'}`}
              onClick={() => setTheme('dark')}
            >
              Dark Mode
            </button>
            <button
              className={`px-3 py-1.5 rounded text-xs border ${theme === 'light' ? 'bg-[var(--foreground)] text-[var(--background)] font-bold' : 'border-[var(--border)] text-[var(--muted-foreground)]'}`}
              onClick={() => setTheme('light')}
            >
              Light Mode
            </button>
          </div>
        </Card>

        <Card>
          <h3 className="font-bold text-sm mb-1">Live Telemetry Cadence</h3>
          <p className="text-xs text-[var(--muted-foreground)] mb-3">Frequency for background polling of live signals and health.</p>
          <select
            className="filter-select max-w-xs"
            value={pollingInterval}
            onChange={(e) => setPollingInterval(e.target.value)}
          >
            <option value="15">15 Seconds (Rapid)</option>
            <option value="30">30 Seconds (Default)</option>
            <option value="60">60 Seconds (Standard)</option>
            <option value="300">5 Minutes (Low Bandwidth)</option>
          </select>
        </Card>

        <Card className="border-red-900/30">
          <h3 className="font-bold text-sm text-[var(--danger)] mb-1">Cache Management</h3>
          <p className="text-xs text-[var(--muted-foreground)] mb-3">
            Flush server-side Redis cache keys and force immediate re-aggregation.
          </p>
          <button
            className="px-4 py-2 bg-[var(--danger)] text-white font-bold rounded text-xs inline-flex items-center gap-2 hover:opacity-90"
            onClick={() => setModalOpen(true)}
          >
            <Trash2 size={14} /> Clear Server Cache
          </button>
        </Card>

        {toast && (
          <div className="feedback-toast">
            <CheckCircle2 size={15} />
            <span>{toast}</span>
          </div>
        )}
      </div>

      <CacheClearModal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        onSuccess={handleCacheSuccess}
      />
    </>
  )
}

export function IntelligencePage() {
  const [prompt, setPrompt] = useState('')
  const [response, setResponse] = useState<AthenaResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [suggestedQueries, setSuggestedQueries] = useState<string[]>([
    'What are the 5-year durability outcomes and bleed reductions for AAV5 gene therapy in Haemophilia A?',
    'How do the Phase 3 FRONTIER-2 Mim8 zero-bleed readouts compare with prophylactic factor infusions?',
    'What regulatory action milestones and PDUFA timelines are expected for anti-TFPI prophylaxis?',
    'What are the EMA CHMP 5-year safety conclusions regarding vector shedding and liver transaminitis?',
  ])
  const [signalsCount, setSignalsCount] = useState(4)
  const { isDark } = useTheme()

  useEffect(() => {
    let active = true
    getAthenaSuggestedQuestions().then((res) => {
      if (active && res.questions && res.questions.length > 0) {
        setSuggestedQueries(res.questions)
        if (res.signals_count) setSignalsCount(res.signals_count)
      }
    })
    return () => {
      active = false
    }
  }, [])

  const handleAsk = async (q: string) => {
    if (!q.trim()) return
    setLoading(true)
    setError(null)
    try {
      const res = await askAthena(q)
      setResponse(res)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Athena synthesis failed')
      setResponse(null)
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <SectionTitle
        eyebrow="Cognitive Reasoning Layer"
        title="Ask Athena"
        detail="Biomedical question answering with PII/PHI scrubbing and factual evidence grounding."
      />

      <div className="intelligence-grid">
        <Card className="athena-card">
          <div className="athena-orbit">
            <BrainCircuit size={28} />
          </div>
          <h2>Ask anything about the clinical landscape.</h2>
          <p className="muted">
            Athena searches the 384-dimensional vector space, applies PII/PHI scrubbing, and synthesizes answers using local Gemma 3 or privacy-gated fallback.
          </p>

          <div className="prompt-list">
            <div className="flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-wider text-[var(--signal)] mb-1">
              <Sparkles size={12} />
              <span>Synthesized from {signalsCount} Active Signals (Gemma 3)</span>
            </div>
            {suggestedQueries.map((q) => (
              <button key={q} onClick={() => { setPrompt(q); handleAsk(q); }}>
                <span className="line-clamp-2 text-left">{q}</span>
                <ChevronRight size={14} className="shrink-0 ml-1" />
              </button>
            ))}
          </div>

          <div className="ask-row">
            <input
              type="text"
              placeholder="Ask a question about haemophilia competitive signals..."
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              onKeyDown={(e) => { if (e.key === 'Enter') handleAsk(prompt); }}
            />
            <GlowingThinkingButton
              label="Ask Athena"
              loadingLabel="Thinking..."
              loading={loading}
              disabled={!prompt.trim() || loading}
              onClick={() => handleAsk(prompt)}
              width={140}
              height={42}
            />
          </div>
        </Card>

        <Card className="answer-card">
          {loading ? (
            <div className="flex flex-col items-center justify-center py-20 gap-3 text-center">
              <div className="flex items-center gap-2 text-[15px] font-semibold text-[var(--foreground)]">
                <BrainCircuit size={18} className="text-[var(--signal)] animate-pulse" />
                <span>Athena thinking</span>
                <span className="inline-flex gap-1 items-center ml-0.5">
                  <i className="w-1.5 h-1.5 rounded-full bg-[var(--signal)] animate-bounce [animation-delay:-0.3s]" />
                  <i className="w-1.5 h-1.5 rounded-full bg-[var(--signal)] animate-bounce [animation-delay:-0.15s]" />
                  <i className="w-1.5 h-1.5 rounded-full bg-[var(--signal)] animate-bounce" />
                </span>
              </div>
              <span className="text-xs text-[var(--muted-foreground)]">
                Synthesizing grounded answer across indexed vector embeddings...
              </span>
            </div>
          ) : error ? (
            <div className="error-card">
              <h3>Synthesis Unavailable</h3>
              <p>{error}</p>
            </div>
          ) : response ? (
            <div>
              <div className="flex items-center gap-2 mb-3 text-[var(--signal)]">
                <Sparkles size={16} />
                <strong className="text-xs uppercase tracking-wider">Athena Synthesized Answer</strong>
              </div>
              <p className="text-sm leading-relaxed text-[var(--foreground)]">{response.answer}</p>
              <div className="confidence">
                <span>Evidence Grounding Confidence:</span>
                <strong>{Math.round(response.confidence)}%</strong>
              </div>
            </div>
          ) : (
            <div className="empty-state">
              <BrainCircuit size={28} />
              <p>Athena is ready</p>
              <span>Select a prompt from the left or enter a custom query to start synthesis.</span>
            </div>
          )}
        </Card>
      </div>
    </>
  )
}

export function SignalDrawer({
  signal,
  onClose,
}: {
  signal: Signal
  onClose: () => void
}) {
  const [selectedRole, setSelectedRole] = useState('MEDICAL_AFFAIRS')
  const [relevanceRating, setRelevanceRating] = useState(5)
  const [urgencyRating, setUrgencyRating] = useState(4)
  const [actionAppropriate, setActionAppropriate] = useState(true)
  const [comments, setComments] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isRecalibrating, setIsRecalibrating] = useState(false)
  const [feedbackSuccess, setFeedbackSuccess] = useState<string | null>(null)
  const [recalResult, setRecalResult] = useState<RecalibrateResponse | null>(null)
  const [confirmedWatchId, setConfirmedWatchId] = useState<string | null>(null)

  const roles = [
    'MEDICAL_AFFAIRS',
    'REGULATORY',
    'SAFETY',
    'MARKET_ACCESS',
    'COMMUNICATIONS',
    'LEADERSHIP',
  ]

  const handleFeedbackSubmit = async () => {
    if (!signal.signal_id && !signal.id) return
    setIsSubmitting(true)
    setFeedbackSuccess(null)
    try {
      const res = await submitFeedback({
        signal_id: signal.signal_id || signal.id,
        stakeholder_function: selectedRole,
        relevance_rating: relevanceRating,
        urgency_rating: urgencyRating,
        action_appropriate: actionAppropriate,
        comments: comments || undefined,
      })
      setFeedbackSuccess(
        `Feedback recorded. (${res.unapplied_count} unapplied for ${selectedRole.replace('_', ' ')})`
      )
    } catch (err) {
      setFeedbackSuccess(err instanceof Error ? err.message : 'Feedback submission failed')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleRecalibrate = async () => {
    setIsRecalibrating(true)
    try {
      const res = await recalibrateRole(selectedRole)
      setRecalResult(res)
    } catch (err) {
      console.error(err)
    } finally {
      setIsRecalibrating(false)
    }
  }

  const handleConfirmWatch = async (sug: WatchRuleSuggestion) => {
    try {
      const res = await confirmWatchItem({
        development_id: sug.development_id || (signal.development_id ? signal.development_id : '00000000-0000-0000-0000-000000000000'),
        trigger_event: sug.trigger_event,
        expected_event: sug.expected_event,
        monitoring_window_days: sug.monitoring_window_days,
        responsible_function: sug.responsible_function,
      })
      setConfirmedWatchId(res.watch_id)
    } catch (err) {
      console.error(err)
    }
  }

  return (
    <div className="drawer-backdrop" onClick={onClose}>
      <motion.aside
        initial={{ x: '100%' }}
        animate={{ x: 0 }}
        exit={{ x: '100%' }}
        className="signal-drawer overflow-y-auto max-h-screen"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="drawer-top">
          <div className="flex items-center gap-2">
            <Badge tone={signal.severity}>{signal.severity}</Badge>
            <Link
              href={`/signals/${encodeURIComponent(signal.signal_id || signal.id || '')}`}
              className="text-xs text-[var(--signal)] hover:underline inline-flex items-center gap-1 font-medium ml-2"
              onClick={onClose}
            >
              <span>Full Decision Workspace</span>
              <ExternalLink size={12} />
            </Link>
          </div>
          <button className="icon-button" onClick={onClose} aria-label="Close drawer">
            <X size={18} />
          </button>
        </div>

        <h2>{signal.title}</h2>
        <p className="drawer-summary">{signal.summary}</p>

        <div className="drawer-score">
          <strong>{signal.score}</strong>
          <span>Priority Score</span>
          <span className="font-semibold text-signal">{signal.confidence}% Confidence</span>
        </div>

        {/* Calibration & HITL Feedback Widget */}
        <div className="calibration-widget-card">
          <div className="widget-header">
            <Sliders size={16} className="text-accent" />
            <h3>Stakeholder Calibration & Feedback</h3>
          </div>
          <p className="muted widget-intro">
            Rate routing relevance and trigger batch weight calibration with versioned history.
          </p>

          <div className="role-selector-bar">
            {roles.map((role) => (
              <button
                key={role}
                className={`role-pill ${selectedRole === role ? 'role-pill-active' : ''}`}
                onClick={() => setSelectedRole(role)}
              >
                {role.replace('_', ' ')}
              </button>
            ))}
          </div>

          <div className="rating-rows">
            <div className="rating-row">
              <span>Relevance Rating:</span>
              <div className="star-group">
                {[1, 2, 3, 4, 5].map((star) => (
                  <button
                    key={star}
                    type="button"
                    className={`star-btn ${relevanceRating >= star ? 'star-active' : ''}`}
                    onClick={() => setRelevanceRating(star)}
                    aria-label={`Rate relevance ${star} stars`}
                  >
                    <Star size={16} />
                  </button>
                ))}
              </div>
            </div>

            <div className="rating-row">
              <span>Urgency Rating:</span>
              <div className="star-group">
                {[1, 2, 3, 4, 5].map((star) => (
                  <button
                    key={star}
                    type="button"
                    className={`star-btn ${urgencyRating >= star ? 'star-active' : ''}`}
                    onClick={() => setUrgencyRating(star)}
                    aria-label={`Rate urgency ${star} stars`}
                  >
                    <Star size={16} />
                  </button>
                ))}
              </div>
            </div>

            <label className="checkbox-row">
              <input
                type="checkbox"
                checked={actionAppropriate}
                onChange={(e) => setActionAppropriate(e.target.checked)}
              />
              <span>Action and routing are appropriate</span>
            </label>

            <textarea
              className="feedback-comment-input"
              rows={2}
              placeholder="e.g. Critical durability data; watch upcoming congress abstracts..."
              value={comments}
              onChange={(e) => setComments(e.target.value)}
            />

            <div className="widget-actions">
              <button
                className="submit-feedback-btn"
                onClick={handleFeedbackSubmit}
                disabled={isSubmitting}
              >
                {isSubmitting ? (
                  <>
                    <RefreshCw size={14} className="spin" /> Submitting...
                  </>
                ) : (
                  <>
                    <CheckCircle2 size={14} /> Submit Feedback
                  </>
                )}
              </button>

              <button
                className="recalibrate-btn"
                onClick={handleRecalibrate}
                disabled={isRecalibrating}
              >
                {isRecalibrating ? (
                  <>
                    <RefreshCw size={14} className="spin" /> Recalibrating...
                  </>
                ) : (
                  <>
                    <Gauge size={14} /> Recalibrate Role
                  </>
                )}
              </button>
            </div>

            {feedbackSuccess && (
              <div className="feedback-toast">
                <CheckCircle2 size={15} />
                <span>{feedbackSuccess}</span>
              </div>
            )}
          </div>

          {recalResult && (
            <div className="before-after-panel">
              <div className="before-after-header">
                <Sparkles size={16} />
                <strong>Calibrated Routing (Version {recalResult.calibration_version})</strong>
              </div>

              {recalResult.comparisons.map((comp, idx) => (
                <div className="comparison-card" key={idx}>
                  <div className="comparison-grid">
                    <div className="comparison-col before-col">
                      <span className="col-label">BASELINE ROUTING</span>
                      <div className="score-val">{Math.round(comp.baseline_relevance_score * 100)}%</div>
                      <Badge tone="medium">Priority: {comp.baseline_priority}</Badge>
                    </div>

                    <div className="comparison-divider">→</div>

                    <div className="comparison-col after-col">
                      <span className="col-label">CALIBRATED ROUTING</span>
                      <div className="score-val highlight">{Math.round(comp.calibrated_relevance_score * 100)}%</div>
                      <Badge tone="critical">Priority: {comp.calibrated_priority}</Badge>
                    </div>
                  </div>

                  {comp.confidence_uplift_pct > 0 && (
                    <div className="uplift-banner">
                      <Sparkles size={13} />
                      <span>{comp.stakeholder_function} confidence uplift: +{comp.confidence_uplift_pct}% after feedback</span>
                    </div>
                  )}

                  <p className="calibrated-action-text">
                    {comp.calibrated_suggested_action}
                  </p>
                </div>
              ))}

              {recalResult.watch_rule_suggestions.length > 0 && (
                <div className="watch-suggestions-box">
                  <h4>
                    <Eye size={15} /> Suggested Watch Rule
                  </h4>
                  {recalResult.watch_rule_suggestions.map((sug) => (
                    <div className="watch-suggestion-card" key={sug.suggestion_id}>
                      <p>
                        <strong>Expected:</strong> {sug.expected_event}
                      </p>
                      <p className="muted text-xs">
                        Monitoring window: {sug.monitoring_window_days} days · Function: {sug.responsible_function}
                      </p>
                      {confirmedWatchId ? (
                        <div className="watch-confirmed-badge">
                          <CheckCircle2 size={13} /> Active Watch Rule Confirmed
                        </div>
                      ) : (
                        <button
                          className="confirm-watch-btn"
                          onClick={() => handleConfirmWatch(sug)}
                        >
                          Confirm & Activate Watch Rule
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        <h3>Evidence & provenance</h3>
        <p className="muted evidence-note">
          Source material supporting this intelligence.
        </p>
        {signal.sources.length > 0 ? (
          signal.sources.map((source) => (
            <div className="source-line" key={source.id}>
              <BookOpen size={15} />
              <span>
                <strong>{source.name}</strong>
                <small>{source.type}</small>
              </span>
              <Badge>{source.credibility != null ? `${source.credibility}%` : '—'}</Badge>
            </div>
          ))
        ) : (
          <p className="muted text-xs">Direct public signal ingestion feed.</p>
        )}
      </motion.aside>
    </div>
  )
}

export function GenericPage({
  title,
  eyebrow,
  description,
  children,
}: {
  title: string
  eyebrow: string
  description: string
  children?: React.ReactNode
}) {
  return (
    <>
      <SectionTitle eyebrow={eyebrow} title={title} detail={description} />
      <div className="generic-grid">
        <Card>
          <div className="placeholder-visual">
            <Network size={26} />
            <strong>Signal architecture</strong>
            <span>Connected evidence will appear here.</span>
          </div>
        </Card>
        <Card>
          <p className="eyebrow">System note</p>
          <h2>Build from the evidence.</h2>
          <p className="muted">
            This workspace is ready for review workflows, provenance, and role-specific decisions.
          </p>
          {children}
        </Card>
      </div>
    </>
  )
}

function Loading() {
  return (
    <div className="loading-screen">
      <div className="loading-mark">
        <Activity size={22} />
      </div>
      <p>Loading signal landscape...</p>
    </div>
  )
}
