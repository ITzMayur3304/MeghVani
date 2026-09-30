# PRD — National Weather Intelligence Platform
### Problem Statement 26069 | Government-facing Weather Big Data Analytics Platform

---

## 1. Product Vision
A government-style public platform that aggregates weather-related information from citizens, social platforms, official weather sources and news, verifies it using AI, and presents it as a trustworthy, real-time situational picture of weather events across India — with a built-in disaster-response layer that turns verified alerts into actionable safety guidance.

This is a **government/public-institution website**, not a consumer app or startup product. Every design decision should read as: official, trustworthy, accessible, calm under emergency, and credible to a non-technical citizen as well as a technical evaluator.

Reference for visual tone/structure (NOT to be copied, only used for layout/spacing/section inspiration): "White Hall — Municipal and Government WordPress Theme." From the actual theme screenshots, the structural patterns worth adapting are:
- **Top utility bar** (dark, above the main nav): small info strip — theme shows weather/contact/hours/social icons; our version replaces this with a live info strip (current date, national helpline number, language selector, social icons)
- **Main nav bar**: dark navy/near-black background, logo on left, horizontal nav with dropdown menus (Home, City Govt, Departments, Events, News, Contact in the reference) — our equivalent: Home, Live Map, Report an Event ▾, Alerts, About ▾, Contact — plus a search icon and grid/quick-links icon on the right, matching the reference's icon placement
- **Hero section**: full-bleed background image/photo with a dark semi-transparent overlay, large bold white headline text, a short supporting line, and one strong CTA button in the accent color (reference uses "READ MORE" in red) — ours will read "Report a Weather Event" / "View Live Map"
- **Hero slider behavior**: the reference hero is a slider — background image subtly zooms while active (a slow Ken Burns-style zoom, not a jarring jump cut), text content cross-fades or slides in per slide, with left/right arrow controls at the vertical center edges. For our platform, each "slide" should be a rotating high-severity/featured event or a rotating public-safety message rather than static marketing content — e.g. slide 1: general platform intro + "Report a Weather Event" CTA; slide 2 (only shown if there's an active alert): the current highest-severity alert with a "View Alert" CTA; slide 3: "How Verification Works" teaser. If there is no active alert, the alert slide is simply omitted from rotation rather than shown empty.
- A small "eyebrow" label above the headline (reference shows a red star + "TOURIST ATTRACTIONS" in small caps) — ours would be a small severity-colored label like "🟢 LIVE STATUS" or "🔴 ACTIVE ALERT" depending on current state, which doubles as the same status-strip concept described in Section 4.1

On accent color: the reference theme uses a strong red as its accent (nav highlight, CTA buttons, eyebrow label). Red already has a specific meaning in our system (Suspicious status / Red severity level), so we keep the saffron/amber accent from Section 2.1 for general CTAs and navigation highlights, and reserve red strictly for alert/danger states — this avoids a citizen seeing a red "Report a Weather Event" button and mistaking it for an active emergency.

---

## 2. Design System

### 2.1 Color Palette (Government / Official Tone)
Primary palette should read as trustworthy and institutional — avoid consumer-app gradients, playful colors, or startup-style vibrancy.

| Role | Color | Hex | Usage |
|---|---|---|---|
| Primary (Navy) | Deep Institutional Blue | `#0B3D62` | Header, nav bar, primary buttons, footer |
| Primary Dark | Darker Navy | `#082C47` | Hover states, admin panel sidebar |
| Secondary (Accent) | Saffron/Amber | `#E8A33D` | CTAs, highlights, "Report Now" button — evokes Indian govt tricolor without being literal |
| Success / Verified | Green | `#1E8A4C` | Verified status badges, safe indicators |
| Warning | Amber-Orange | `#D9822B` | "Review" status, Orange severity level |
| Danger / Alert | Red | `#C0392B` | "Suspicious" status, Red severity level, disaster alert banners |
| Info / Neutral Event | Slate Blue | `#4A6FA5` | Default map markers, informational chips |
| Background | Off-White | `#F7F9FB` | Page background |
| Surface / Cards | White | `#FFFFFF` | Cards, panels, tables |
| Text Primary | Charcoal | `#1E2A32` | Body text |
| Text Muted | Slate Gray | `#5C6B73` | Secondary text, captions |
| Border | Light Gray | `#DDE3E8` | Card borders, table dividers |

**Severity Level Colors (must match IMD's official color code exactly since this is explicitly referenced in the pitch):**
- Green `#2E9E44` — Normal
- Yellow `#F2C230` — Watch
- Orange `#E8792B` — Alert
- Red `#D33B3B` — Severe/Emergency

### 2.2 Typography
- Headings: a clean, slightly formal sans-serif (e.g. "Merriweather Sans" or "Source Sans Pro") — avoid trendy/rounded fonts
- Body: "Inter" or "Noto Sans" (Noto Sans also gives good Devanagari/Marathi/Hindi glyph support for multi-language reporting)
- Government sites should favor generous line-height and larger base font size (16–18px body) for accessibility

### 2.3 UI Principles
- WCAG-AA accessible contrast minimum throughout (government site requirement)
- No dark mode needed for MVP — light, official theme only
- Icons: simple line icons (map pin, shield, cloud, drop, alert triangle) — no illustrated/cartoon icon sets
- Mobile-first spacing: design components in a single-column-first mindset so the same component logic ports directly to a future React Native/Flutter app

---

## 3. Information Architecture (Mobile-Convertible)

Build the frontend as componentized React (cards, list items, map view, filter bar, status badges) so each screen maps 1:1 to a future mobile screen. Avoid desktop-only patterns (hover-dependent menus, multi-column dashboards with no responsive collapse) — every screen must degrade cleanly to a single-column mobile layout, since a mobile app (React Native / Flutter) is a planned next phase.

### Site Map
```
/                        → Public Landing Page
/report                  → Citizen Report Submission Form
/map                     → Live Weather Map (full view)
/events/:id              → Individual Event Detail Page
/alerts                  → Disaster Alerts & Safe Zones (public)
/about                   → About the Platform / How Verification Works
/admin/login             → Admin Login
/admin/dashboard         → Admin Dashboard (protected)
/admin/reports           → Report Verification Queue (protected)
/admin/sources           → Source Reliability Management (protected)
/admin/alerts            → Alert & Severity Management (protected)
```

---

## 4. Page-by-Page Experience

### 4.1 Public Landing Page (`/`) — What ANY visitor sees first
This is the most important page for first impressions — it must immediately look official and trustworthy, not like a hackathon demo.

**Above the fold:**
- **Top utility bar** (dark navy, thin strip): current date + national helpline number + a live-updated "Last synced: X min ago" indicator, language selector (EN/HI/MR), social/official-links icons on the right
- **Main navigation bar** (dark navy/near-black, below utility bar): logo + platform name on left; center/right nav with dropdowns — Home, Live Map, Report an Event ▾, Alerts, About ▾, Contact; search icon and quick-links grid icon on the far right
- **Hero slider** (full-bleed background, dark overlay, slow background zoom while active):
  - Small eyebrow label above headline that reflects live state: `🟢 LIVE STATUS` in normal conditions, or `🔴 ACTIVE ALERT` styled in the matching severity color when one exists
  - Large bold headline, e.g. "Real-time, verified weather intelligence for India"
  - Short supporting line
  - One primary CTA button in saffron/amber: **"Report a Weather Event"**, secondary text-link style CTA: "View Live Map"
  - Left/right arrow controls at the vertical center edges to move between slides
  - Slide rotation: Slide 1 = general intro + report CTA (always present); Slide 2 = current highest-severity active alert with "View Alert" CTA (only included in rotation when an alert is active); Slide 3 = "How Verification Works" teaser
- Directly beneath the hero, a slim status strip persists on scroll (sticky), showing the national severity summary at a glance, e.g. `🟢 Normal — 3 Active Watches` — this remains visible even after the hero slider is scrolled past, so the live status is never more than a glance away anywhere on the page

**Below the fold, in order:**
1. **Live India Map preview** (embedded, smaller version of the full map) with current active event markers
2. **Key stats bar**: Total Reports Today, Verified Reports, Active Alerts, Reports Under Review — styled like a government dashboard summary, not a startup metric bar
3. **Latest Verified Reports feed** — a scrolling/paginated list of recent verified reports (city, event type, time, status badge)
4. **How Verification Works** — a short 3–4 step visual explainer (Report Submitted → AI Classification → Cross-Verification → Published) — builds public trust
5. **Active Disaster Alerts section** (only rendered if severity ≥ Orange) — shown prominently with precaution guidance and safe-zone links; hidden/collapsed entirely when there's no active alert, so the page doesn't look alarmist in normal conditions
6. Footer: official-style footer with About, Data Sources, Contact, Disclaimer, language selector (English/Hindi/Marathi)

### 4.2 Citizen Report Form (`/report`)
- Simple, form-first page — no distractions
- Fields: Description (textarea, supports Hindi/Marathi/English input), Event Type (optional dropdown — AI can also infer it), City/State (auto-suggest or GPS auto-detect), Photo/Video upload (optional), "Use my current location" button
- On submit: show a confirmation state with a generated Report ID and a short message: "Your report is being verified. Thank you for contributing to public safety."
- This page must work flawlessly on mobile — assume most citizen reports will come from phones in the field during an actual weather event

### 4.3 Live Weather Map (`/map`)
- Full-screen India map (Leaflet), color-coded markers by event type, clustered when zoomed out
- Filter bar (sticky on mobile: collapses into a filter icon/drawer): Date range, Event type, State/City, Verification status
- Clicking a marker opens a side panel (desktop) or bottom sheet (mobile) with report details: event, location, time, source, confidence score, status badge, photo if available
- Legend showing event-type color key and verification status key

### 4.4 Event Detail Page (`/events/:id`)
- Full detail of a single event cluster: all contributing reports (citizen + Reddit + news + weather API cross-check), timeline of how the event developed, current severity level, and — if severity is elevated — the disaster response panel (precautions + nearest safe zones) embedded directly on this page

### 4.5 Alerts & Safe Zones (`/alerts`) — Public
- Always accessible (not just when there's an active alert), so citizens know where to check during an emergency
- If no active alerts: calm "No active alerts. Stay prepared." state with general seasonal safety tips
- If active alerts: clear severity-colored cards per affected region, precaution list for that event type, and a small map showing nearest safe zones relative to the affected area

### 4.6 Admin Login (`/admin/login`)
- Minimal, secure-looking login form — no public nav/footer clutter, just platform logo + login card
- Username/password only for MVP (JWT-based); no need for OAuth/2FA in the 2-day build

### 4.7 Admin Dashboard (`/admin/dashboard`) — What admin sees after login
This is the operational control room view — denser and more data-rich than the public site, but still using the same color system.

- Top summary cards: Pending Verification count, Verified Today, Suspicious/Flagged, Active Severity Level (with quick escalate/de-escalate control)
- **AI Verification Queue** (the core admin feature, and the one that most directly demonstrates the "identify fake/misleading reports, verify untrusted sources, remove duplicates, auto-categorize events" requirement from the problem statement):
  - A table/list of incoming reports, each row showing: text snippet, source, AI-assigned event type + confidence %, duplicate-cluster indicator (e.g. "3 similar reports"), source reliability score, and action buttons: **Verify / Mark Suspicious / Reject / View Similar Reports**
  - Clicking a report expands full detail: original text, photo/video if present, map location, the AI's reasoning summary (which factors contributed to the confidence score — source reliability, location match, weather API agreement, duplicate corroboration), and full duplicate cluster list
- **Source Reliability panel**: list of sources (citizen accounts, Reddit, news outlets) with their reliability score and history, with ability to manually adjust/flag a source as untrusted
- **Severity & Alert Control panel**: current severity per active event cluster, with manual override capability (admin can force-escalate or de-escalate ahead of/instead of the automatic threshold, for real-world judgment calls)
- **Activity log**: recent admin actions (who verified/rejected what, when) for accountability — appropriate for a government tool

### 4.8 Admin — Report Verification Queue (`/admin/reports`)
- Dedicated full-page version of the verification queue above, with pagination, sort by confidence/date/city, and bulk actions (e.g. bulk-verify a duplicate cluster once one report in it is confirmed genuine)

### 4.9 Admin — Source Management (`/admin/sources`)
- Table of all known sources and their current reliability scores, editable by admin

### 4.10 Admin — Alert Management (`/admin/alerts`)
- List of all event clusters currently at Yellow/Orange/Red, with the ability to edit the precaution text shown to the public and manage the safe-zone list per city

---

## 5. AI/ML Feature Requirements (Explicit Problem Statement Mapping)
These are called out separately because they are directly graded against the problem statement text and must be visibly demonstrable in the admin queue and event detail pages, not just implemented in the backend.

| Problem Statement Requirement | Where It's Shown in the UI |
|---|---|
| Identify fake or misleading reports | Confidence score + "Suspicious" status badge, visible on report cards (public: subtly; admin: explicitly with reasoning) |
| Verify untrusted sources | Source Reliability score shown next to every report; dedicated Source Management admin page |
| Remove duplicate entries | Duplicate-cluster indicator on report cards; "View Similar Reports" grouping in admin queue; duplicates shown as corroborating evidence, not deleted |
| Automatically categorize weather events | Event Type badge (rainfall/thunderstorm/flood/heatwave/fog/dust storm/strong wind) auto-assigned and shown on every report, map marker, and event detail page, with confidence % visible on hover/tap |

The admin queue's "expand report" reasoning view (Section 4.7) is the single most important screen for demonstrating AI transparency to judges — do not skip it even under time pressure.

---

## 6. Mobile App Conversion Notes
Design and build decisions now that make a later React Native/Flutter app straightforward:
- Keep all business logic in the FastAPI backend — the web frontend should be a thin client calling REST endpoints, so a mobile app can call the same API with no backend changes
- Componentize the frontend so each public page (landing, report form, map, alerts, event detail) has a clear mobile-equivalent screen already implied by this PRD's structure
- The citizen Report Form (4.2) and Alerts page (4.5) are the two screens most likely to be used first as a standalone mobile app (field reporting + emergency lookup) — prioritize their UX quality and mobile responsiveness above all other public pages
- Avoid any desktop-only interaction pattern (right-click menus, hover-only tooltips, multi-pane layouts without a collapse strategy)

---

## 7. Out of Scope for This PRD / 2-Day Build
- Native mobile app itself (planned future phase, not this sprint)
- Multi-language full UI translation (Hindi/Marathi selector can be present as UI, but full translation coverage is a stretch goal only)
- OAuth/2FA for admin login
- CMS-style content management for footer/about pages (hardcode this content for the prototype)
