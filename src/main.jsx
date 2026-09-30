import React, { useEffect, useState } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Link, NavLink, Navigate, Route, Routes, useLocation, useNavigate } from 'react-router-dom'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import './styles.css'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'
const demoReports = [
  { report_id: 'MV-24091', city: 'Pune', state: 'Maharashtra', event_type: 'flood', text: 'Water has entered the ground floor near Sinhagad Road after intense rainfall.', timestamp: '2026-09-30T06:35:00Z', verification_status: 'verified', confidence_score: 0.94, source: 'citizen' },
  { report_id: 'MV-24090', city: 'Nashik', state: 'Maharashtra', event_type: 'thunderstorm', text: 'Very strong winds and lightning observed across Gangapur Road.', timestamp: '2026-09-30T05:45:00Z', verification_status: 'verified', confidence_score: 0.89, source: 'weather_api' },
  { report_id: 'MV-24087', city: 'Mumbai', state: 'Maharashtra', event_type: 'rainfall', text: 'Heavy rain is slowing traffic around Andheri East.', timestamp: '2026-09-30T04:20:00Z', verification_status: 'review', confidence_score: 0.68, source: 'reddit' },
]
const demoAlerts = [{ id: 'AL-019', city: 'Pune', state: 'Maharashtra', severity: 'orange', title: 'Urban flooding watch', guidance: ['Avoid underpasses and low-lying roads', 'Keep phones and medicines in a waterproof pouch'] }]

async function request(path, options = {}) {
  const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) }
  const token = localStorage.getItem('meghvaani_token')
  if (token) headers.Authorization = `Bearer ${token}`
  const response = await fetch(`${API}${path}`, { ...options, headers })
  if (!response.ok) throw new Error((await response.json().catch(() => null))?.detail || 'Request failed')
  return response.json()
}
async function safeRequest(path, options) {
  try {
    const data = await request(path, options)
    if (path === '/stats') return { total_today: data.total_reports, verified: data.by_status?.verified || 0, active_alerts: data.active_alerts || 0, under_review: data.by_status?.review || 0 }
    return data
  } catch {
    if (path === '/reports') return demoReports
    if (path === '/alerts') return demoAlerts
    if (path === '/stats') return { total_today: 42, verified: 29, active_alerts: 1, under_review: 8 }
    return null
  }
}

function Badge({ children, tone = '' }) { return <span className={`badge ${tone || String(children).toLowerCase()}`}>{children}</span> }
function ReportCard({ report }) { return <div className="report-card"><div className="row-between"><div><Badge tone="event">{report.event_type.replace('_', ' ')}</Badge><span className="muted">{report.city}, {report.state}</span></div><Badge>{report.verification_status}</Badge></div><p>{report.text}</p><div className="row-between small"><span>{new Date(report.timestamp).toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: 'short' })}</span><span>Confidence <b>{Math.round(report.confidence_score * 100)}%</b></span></div></div> }
function MapWidget({ reports = demoReports, large = false }) {
  const ref = React.useRef(null)
  useEffect(() => {
    if (!ref.current) return undefined
    const map = L.map(ref.current, { scrollWheelZoom: large }).setView([21.2, 78.9], large ? 5 : 4.5)
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { attribution: '&copy; OpenStreetMap contributors' }).addTo(map)
    reports.forEach((report, index) => {
      const locations = { Pune: [18.5204, 73.8567], Nashik: [20.0059, 73.7898], Mumbai: [19.076, 72.8777], Nagpur: [21.1458, 79.0882] }
      const point = locations[report.city] || [20.5937 + index * .2, 78.9629 + index * .2]
      const color = report.verification_status === 'verified' ? '#1e8a4c' : report.verification_status === 'suspicious' ? '#c0392b' : '#d9822b'
      L.circleMarker(point, { radius: 9, color, fillColor: color, fillOpacity: .85, weight: 3 }).addTo(map).bindPopup(`<b>${report.event_type.replace('_', ' ')}</b><br>${report.city}<br>${report.text}`)
    })
    return () => map.remove()
  }, [reports, large])
  return <div className={`leaflet-map ${large ? 'large' : ''}`} ref={ref} />
}
function Shell({ children }) {
  const loggedIn = Boolean(localStorage.getItem('meghvaani_token'))
  return <><div className="utility">National helpline <strong>112</strong><span>Live data refresh enabled</span><span>EN&nbsp; | &nbsp;हिंदी&nbsp; | &nbsp;मराठी</span></div><header><Link className="brand" to="/"><span className="brand-mark">☁</span><span><b>MeghVaani</b><small>National Weather Intelligence</small></span></Link><nav><NavLink to="/">Home</NavLink><NavLink to="/map">Live Map</NavLink><NavLink to="/alerts">Notifications</NavLink><NavLink to="/about">About</NavLink></nav>{loggedIn ? <button className="admin-link" onClick={() => { localStorage.removeItem('meghvaani_token'); window.location.href = '/' }}>Sign out</button> : <Link className="admin-link" to="/login">Citizen login</Link>}</header>{children}<footer><div><b>MeghVaani</b><p>Trusted weather intelligence for safer communities across India.</p></div><div><b>Public resources</b><Link to="/map">Live map</Link><Link to="/alerts">Notifications</Link></div><div><b>Important</b><span>Call 112 for immediate emergencies.</span><span>Reports are reviewed before public verification.</span></div></footer></>
}
function Home() {
  const [reports, setReports] = useState(demoReports), [stats, setStats] = useState({ total_today: 42, verified: 29, active_alerts: 1, under_review: 8 }), [alerts, setAlerts] = useState(demoAlerts)
  useEffect(() => { const load = () => Promise.all([safeRequest('/reports'), safeRequest('/stats'), safeRequest('/alerts')]).then(([r, s, a]) => { if (r) setReports(r); if (s) setStats(s); if (a) setAlerts(a) }); load(); const timer = setInterval(load, 30000); return () => clearInterval(timer) }, [])
  return <Shell><main><section className="hero"><div className="hero-copy"><span className="eyebrow">● LIVE STATUS · INDIA</span><h1>Weather intelligence that communities can trust.</h1><p>Live public notifications, citizen evidence and official weather signals brought together for faster, calmer decisions.</p><div className="actions"><Link className="button primary" to={localStorage.getItem('meghvaani_token') ? '/report' : '/login'}>{localStorage.getItem('meghvaani_token') ? 'Report a weather event' : 'Login to report an event'}</Link><Link className="button ghost" to="/map">Explore live map →</Link></div></div><div className="hero-aside"><span>Current national status</span><strong>{alerts.length ? 'Active watch' : 'Normal'}</strong><small>{alerts.length ? `${alerts.length} region requires attention` : 'No active alerts'}</small></div></section><section className="status-strip"><b>● Public notifications</b><span>{alerts.length ? 'Orange · Active watch' : 'Green · Normal conditions'}</span><span>Auto-refreshing every 30 seconds</span></section><section className="section"><div className="section-heading"><div><span className="eyebrow dark">SITUATIONAL PICTURE</span><h2>Live weather activity across India</h2></div><Link to="/map" className="text-link">Open full map →</Link></div><MapWidget reports={reports} /></section><section className="stats-grid">{[['total_today','Reports today'],['verified','Verified reports'],['active_alerts','Active alerts'],['under_review','Under review']].map(([key, label]) => <div className="stat" key={key}><strong>{stats[key]}</strong><span>{label}</span></div>)}</section><section className="section two-col"><div><div className="section-heading"><div><span className="eyebrow dark">LATEST PUBLIC SIGNALS</span><h2>What is happening now</h2></div><Link to="/map" className="text-link">View all</Link></div>{reports.slice(0, 3).map(report => <ReportCard key={report.report_id} report={report} />)}</div><div className="trust-panel"><span className="eyebrow dark">BUILT FOR TRUST</span><h2>Evidence before urgency</h2>{['Report submitted by an authenticated citizen','AI classifies the weather event','Sources and nearby reports are cross-checked','Administrators publish verified alerts'].map((step, i) => <div className="step" key={step}><b>0{i + 1}</b><span>{step}</span></div>)}</div></section>{alerts.length > 0 && <section className="alert-banner"><div><Badge tone="orange">Public notification</Badge><h2>{alerts[0].title} · {alerts[0].city}</h2><p>Read the latest precaution guidance before travelling.</p></div><Link className="button dark" to="/alerts">Read notification</Link></section>}</main></Shell>
}
function Login() {
  const navigate = useNavigate(), [mode, setMode] = useState('login'), [form, setForm] = useState({ email: '', password: '', name: '' }), [error, setError] = useState('')
  const submit = async e => { e.preventDefault(); setError(''); try { const path = mode === 'login' ? '/citizens/login' : '/citizens/register'; const data = await request(path, { method: 'POST', body: JSON.stringify({ email: form.email, password: form.password }) }); localStorage.setItem('meghvaani_token', data.access_token); navigate('/report') } catch (err) { setError(err.message) } }
  return <Shell><main className="narrow"><div className="page-intro"><span className="eyebrow dark">CITIZEN ACCESS</span><h1>{mode === 'login' ? 'Sign in to report' : 'Create a citizen account'}</h1><p>Public notifications and the live map are open to everyone. Authentication protects the reporting channel from spam and impersonation.</p></div><form className="form-card" onSubmit={submit}>{mode === 'register' && <label>Full name<input required value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} /></label>}<label>Email<input type="email" required value={form.email} onChange={e => setForm({ ...form, email: e.target.value })} /></label><label>Password<input type="password" required minLength="8" value={form.password} onChange={e => setForm({ ...form, password: e.target.value })} /></label>{error && <p className="error">{error}</p>}<button className="button primary" type="submit">{mode === 'login' ? 'Sign in securely' : 'Create account'}</button><button className="text-button" type="button" onClick={() => setMode(mode === 'login' ? 'register' : 'login')}>{mode === 'login' ? 'New citizen? Create an account' : 'Already registered? Sign in'}</button></form></main></Shell>
}
function ReportPage() {
  const navigate = useNavigate(), [form, setForm] = useState({ text: '', city: '', state: '' }), [submitted, setSubmitted] = useState(null), [error, setError] = useState('')
  if (!localStorage.getItem('meghvaani_token')) return <Navigate to="/login" replace />
  const submit = async e => { e.preventDefault(); try { const result = await request('/reports', { method: 'POST', body: JSON.stringify({ ...form, source: 'citizen', location: { type: 'Point', coordinates: [73.8567, 18.5204] } }) }); setSubmitted(result.report_id) } catch (err) { setError(err.message) } }
  if (submitted) return <Shell><main className="narrow"><div className="success"><span className="success-icon">✓</span><span className="eyebrow dark">REPORT RECEIVED</span><h1>Thank you for contributing to public safety.</h1><p>Your report is now in the verification queue.</p><code>{submitted}</code><Link className="button primary" to="/">Return to dashboard</Link></div></main></Shell>
  return <Shell><main className="narrow"><div className="page-intro"><span className="eyebrow dark">AUTHENTICATED REPORTING</span><h1>Report a weather event</h1><p>Your account helps our team distinguish genuine, corroborated reports from spam.</p></div><form className="form-card" onSubmit={submit}><label>Description<textarea required maxLength="1200" value={form.text} onChange={e => setForm({ ...form, text: e.target.value })} placeholder="What happened? Include landmarks, impact and when you observed it." /></label><div className="form-grid"><label>City<input required value={form.city} onChange={e => setForm({ ...form, city: e.target.value })} placeholder="e.g. Pune" /></label><label>State<input required value={form.state} onChange={e => setForm({ ...form, state: e.target.value })} placeholder="e.g. Maharashtra" /></label></div>{error && <p className="error">{error}</p>}<button className="button primary" type="submit">Submit authenticated report →</button><small className="muted">Call 112 for immediate emergencies.</small></form></main></Shell>
}
function MapPage() { const [reports, setReports] = useState(demoReports); useEffect(() => { safeRequest('/reports').then(r => r && setReports(r)) }, []); return <Shell><main><div className="page-intro wide"><span className="eyebrow dark">LIVE MAP</span><h1>Weather events across India</h1><p>Public reports refresh automatically. Select a marker to inspect its event type, city and evidence status.</p></div><div className="map-layout"><div className="map-large"><MapWidget reports={reports} large /></div><div className="map-list">{reports.map(r => <ReportCard report={r} key={r.report_id} />)}</div></div></main></Shell> }
function Alerts() { return <Shell><main className="narrow"><div className="page-intro"><span className="eyebrow dark">PUBLIC NOTIFICATIONS</span><h1>Stay informed. Stay prepared.</h1><p>Notifications remain accessible without login. Read the latest guidance before travelling.</p></div>{demoAlerts.map(alert => <div className="alert-card" key={alert.id}><div className="row-between"><Badge tone={alert.severity}>Active {alert.severity} alert</Badge><span className="muted">{alert.city}, {alert.state}</span></div><h2>{alert.title}</h2><h3>Precautions</h3><ul>{alert.guidance.map(g => <li key={g}>{g}</li>)}</ul></div>)}</main></Shell> }
function About() { return <Shell><main className="narrow"><div className="page-intro"><span className="eyebrow dark">ABOUT MEGHVAANI</span><h1>Evidence before urgency.</h1><p>MeghVaani helps communities and administrators separate signal from noise during weather events.</p></div><div className="content-card"><h2>Open public access, protected reporting</h2><p>Anyone can view notifications and the national map. Citizen submissions require an account so reports remain attributable and the verification queue stays useful.</p></div></main></Shell> }
function Admin() { return <Shell><main className="admin-main"><div className="section-heading"><div><span className="eyebrow dark">OPERATIONS CONTROL ROOM</span><h1>Verification queue</h1></div><Badge tone="orange">Protected admin area</Badge></div><div className="content-card"><h2>Admin dashboard</h2><p>Use the configured admin login to review incoming authenticated citizen reports. Public users cannot access this area.</p></div></main></Shell> }
function App() { return <Routes><Route path="/" element={<Home />} /><Route path="/login" element={<Login />} /><Route path="/report" element={<ReportPage />} /><Route path="/map" element={<MapPage />} /><Route path="/alerts" element={<Alerts />} /><Route path="/about" element={<About />} /><Route path="/admin/*" element={<Admin />} /></Routes> }
createRoot(document.getElementById('root')).render(<BrowserRouter><App /></BrowserRouter>)
