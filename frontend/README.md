# AUI Email Support — Frontend Dashboard

A React dashboard for the **AUI Email Support System**. It lets staff review
AI-generated email replies, approve or reject them before they are sent,
browse full email history, and view aggregate statistics.

Built with **Vite + React 18**, **React Router v6**, **Zustand**, **Recharts**,
**Tailwind CSS**, and **Axios**.

## Features

- **Login** — JWT auth against `POST /auth/login`, token stored in
  `localStorage` (key `aui_token`).
- **Dashboard** — 4 stat cards (Pending / Sent / Rejected / Total), the 5 most
  recent pending emails, and a "Process Gmail" button (`POST /emails/run`).
  Auto-refreshes every 30s.
- **Pending** — the main validation view. Each email shows the original message
  on the left and an **editable** AI reply on the right, with Approve & Send /
  Reject / Edit actions, confidence / urgency / category / language badges, and
  toast feedback. Auto-refreshes every 30s.
- **History** — full email history with filters (status / category / language /
  urgency), search (sender / subject), date sorting, pagination (20/page), and
  expandable rows.
- **Stats** — bar chart by category, pie chart by language, and bar chart by
  urgency (Recharts), sourced from `GET /stats`.
- Dark, industrial theme. Mobile-responsive sidebar. Global toast notifications.
  Any `401` response triggers logout + redirect to `/login`.

## Prerequisites

- Node.js 18+ (developed on Node 22)
- A running instance of the FastAPI backend (default `http://localhost:8000`)

## Getting started

```bash
# from the repo root
cd frontend

# 1. install dependencies
npm install

# 2. configure the backend URL
cp .env.example .env        # then edit if your backend is elsewhere

# 3. start the dev server
npm run dev
```

The app runs at **http://localhost:5173**.

## Environment variables

| Variable       | Description                       | Default                 |
| -------------- | --------------------------------- | ----------------------- |
| `VITE_API_URL` | Base URL of the FastAPI backend   | `http://localhost:8000` |

See [`.env.example`](./.env.example). The backend must allow CORS from the
frontend origin (it does for `localhost`).

## Scripts

| Command           | Description                          |
| ----------------- | ------------------------------------ |
| `npm run dev`     | Start the Vite dev server            |
| `npm run build`   | Production build into `dist/`        |
| `npm run preview` | Preview the production build locally |
| `npm run lint`    | Run ESLint                           |

## Project structure

```
src/
  main.jsx              # entry + Router
  App.jsx               # routes, protected routes, 401 handler
  api/                  # axios client + endpoint wrappers
  store/                # Zustand stores (auth, emails)
  pages/                # Login, Dashboard, Pending, History, Stats
  components/
    layout/             # AppLayout, Sidebar, Topbar
    emails/             # EmailCard, EmailList, ReplyEditor, StatusBadge
    ui/                 # Toast, StatCard, Spinner, EmptyState
  hooks/                # useToast, useAutoRefresh
  styles/globals.css    # Tailwind + design tokens
```
