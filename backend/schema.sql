-- Run in Supabase SQL editor. The service-role client bypasses RLS; browser clients do not.
create table if not exists public.reports (
  report_id text primary key,
  source text not null check (source in ('citizen','reddit','weather_api','news','simulated')),
  source_id text,
  text text not null,
  timestamp timestamptz not null,
  city text not null,
  state text not null,
  location jsonb not null, -- GeoJSON Point: {"type":"Point","coordinates":[lng,lat]}
  event_type text not null,
  classification_confidence double precision not null check (classification_confidence between 0 and 1),
  confidence_score double precision not null check (confidence_score between 0 and 1),
  verification_status text not null,
  duplicate_of text references public.reports(report_id),
  source_reliability double precision not null check (source_reliability between 0 and 1),
  photo_url text,
  video_url text,
  created_at timestamptz not null default now()
);
create index if not exists reports_city_timestamp_idx on public.reports (city, timestamp desc);
create index if not exists reports_event_status_idx on public.reports (event_type, verification_status);
create unique index if not exists reports_source_id_idx on public.reports (source, source_id) where source_id is not null;
alter table public.reports enable row level security;
-- Add explicit authenticated read/insert/update policies if browser access is needed.
-- Keep the service role key server-side; never expose it in frontend code.
