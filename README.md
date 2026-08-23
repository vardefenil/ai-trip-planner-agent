# 🌏 Yatra AI — India Travel Planner Agent

[![Live Demo](https://img.shields.io/badge/Live_Demo-Visit_Yatra_AI-00C853?style=for-the-badge&logo=vercel&logoColor=white)](https://ai-trip-planner-agent.vercel.app)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](http://localhost:8000/docs)
[![Next.js](https://img.shields.io/badge/Frontend-Next.js_16-000000?style=for-the-badge&logo=nextdotjs&logoColor=white)](http://localhost:3000)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)

An intelligent, AI-powered travel planning agent that creates **5 personalised India trip packages** from a single natural-language request with live SSE streaming, interactive budget allocation, day-by-day itineraries, and deep-link bookings.

---

## 🚀 Live Demo & Deployment

- **Frontend Demo (Vercel)**: [https://ai-trip-planner-agent.vercel.app](https://ai-trip-planner-agent.vercel.app)
- **Backend API (Swagger Docs)**: [http://localhost:8000/docs](http://localhost:8000/docs)

> **Note**: To deploy your own live copy:
> 1. Deploy the FastAPI backend on **[Render](https://render.com)** or **[Railway](https://railway.app)** and set your `GEMINI_API_KEY` & `GOOGLE_PLACES_API_KEY`.
> 2. Deploy the Next.js frontend on **[Vercel](https://vercel.com)** and set `NEXT_PUBLIC_API_URL=https://your-backend.onrender.com/api`.

---

## Architecture

```
User Query
    ↓
[Gemini] Parse & Allocate Budget (Pydantic)
    ↓
┌──────────────┬──────────────────┬──────────────────┐
Stay Search    Transport Search   Local Rentals
(Google Places) (IRCTC/Mock/Amadeus) (Google Places)
└──────────────┴──────────────────┴──────────────────┘
    ↓
[Gemini] Rank & Build Itinerary (Day-by-Day)
    ↓
Present 5 Packages (with Edit Loop)
    ↓
Booking Summary (Deep-Links to IRCTC, Booking.com, etc.)
```

## Tech Stack

| Layer | Tech |
|-------|------|
| LLM | Google Gemini 1.5 Flash |
| Agent | LangGraph StateGraph |
| Backend | FastAPI + SSE streaming |
| Frontend | Next.js 14 + TypeScript |
| Hotels | Google Places API |
| Transport | Mock IRCTC/Train data + Amadeus (optional) |
| Rentals | Google Places API |

---

## Quick Start

### 1. Clone & Setup Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Mac/Linux

# Install dependencies
pip install -r requirements.txt
```

### 2. Add API Keys

Edit `backend/.env`:

```env
GEMINI_API_KEY=your_gemini_api_key_here
GOOGLE_PLACES_API_KEY=your_google_places_api_key_here
```

**Get API Keys:**
- Gemini: https://aistudio.google.com/app/apikey
- Google Places: https://console.cloud.google.com/ → Enable "Places API"

### 3. Start Backend

```bash
cd backend
uvicorn main:app --reload --port 8000
```

Visit http://localhost:8000/docs for the Swagger UI.

### 4. Start Frontend

```bash
cd frontend
npm run dev
```

Visit http://localhost:3000

---

## Example Queries

- `Plan a 5-day Goa trip for 2 people with ₹35,000 budget`
- `7-day Manali adventure solo, ₹25,000`
- `Kerala backwaters + hills, 6 days for couple, ₹40,000`
- `Rajasthan heritage tour, 8 days, budget ₹60,000 for 3 people`

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/chat` | Conversational Q&A |
| POST | `/api/plan-trip` | Full pipeline (SSE stream) |
| POST | `/api/modify-trip` | Modify existing packages |
| GET | `/health` | Health check |

---

## Project Structure

```
trip-planner-agent/
├── backend/
│   ├── main.py              # FastAPI entry
│   ├── requirements.txt
│   ├── .env                 # Your API keys
│   ├── agent/
│   │   ├── graph.py         # LangGraph pipeline
│   │   ├── state.py         # Pydantic state schema
│   │   ├── nodes/           # 6 pipeline stages
│   │   └── tools/           # Gemini, Places, Transport
│   └── routers/
│       ├── trip.py          # SSE streaming endpoint
│       └── chat.py          # Chat endpoint
└── frontend/
    └── src/
        ├── app/             # Next.js pages
        ├── components/      # UI components
        ├── lib/             # API client
        └── types/           # TypeScript types
```

---

## Features

- **Conversational AI** — Ask anything about India travel (Yatra AI persona)
- **6-Stage Pipeline** — Parse → Search → Rank → Package → Book
- **Live Progress** — SSE streaming shows each pipeline stage in real-time
- **5 Package Variants** — Budget, Mid-range, Premium, Adventure, Unique
- **Day-by-Day Itinerary** — Expandable per package
- **Booking Deep-Links** — IRCTC, Booking.com, MakeMyTrip, RedBus
- **Edit Loop** — "Make it cheaper" / "more premium" re-ranks packages
- **Travel Tips** — Destination-specific tips (Goa, Manali, Kerala, Rajasthan)
