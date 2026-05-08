# 🌍 AI Travel Planning & Experience Engine

> **Hackathon Submission** · Intelligent travel assistant powered by **Gemini AI** and **Google Maps**

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg)](https://fastapi.tiangolo.com)
[![Gemini AI](https://img.shields.io/badge/Gemini-AI-4285F4.svg)](https://ai.google.dev/)
[![Google Cloud Run](https://img.shields.io/badge/Cloud%20Run-Deployed-34A853.svg)](https://cloud.google.com/run)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

🚀 **Live Demo (Google Cloud Run):** [https://ai-travel-planner-295285969833.us-central1.run.app](https://ai-travel-planner-295285969833.us-central1.run.app)
> **API Docs:** [https://ai-travel-planner-295285969833.us-central1.run.app/api/docs](https://ai-travel-planner-295285969833.us-central1.run.app/api/docs)

---

## 📌 Problem Statement

Modern travelers struggle with **fragmented travel planning** — manually searching for itineraries, comparing budgets, discovering local food, and finding hidden gems across dozens of tabs. This project solves that with a single AI-powered assistant that delivers a complete, personalized trip plan in seconds. 

By heavily leveraging the **Google Cloud Ecosystem** and **Google Services**, this application achieves a seamless user experience. We use **Google Gemini 1.5 Flash** for high-speed, intelligent itinerary generation and **Google Maps Platform** (Places, Geocoding, Distance Matrix, and Maps JavaScript API) to ground the AI's suggestions in real-world location data. Furthermore, user behavior is tracked using **Google Analytics (GA4)** and **Google Tag Manager (GTM)** to enable continuous optimization, and the entire stack is deployed serverless on **Google Cloud Run** using **Google Cloud Build** and **Artifact Registry**.

---

## ✨ Features

| Feature | Details |
|---|---|
| 🤖 **AI Itinerary Generation** | Day-wise plans powered by Gemini 1.5 Flash |
| 🗺️ **Attraction Discovery** | Curated recommendations tailored to your interests |
| 🍜 **Local Food Suggestions** | Authentic dining experiences with price ranges |
| 💎 **Hidden Gems** | Off-the-beaten-path discoveries |
| 💰 **Smart Budget Allocation** | Auto-classified spending across 6 categories |
| 🌤️ **Real Weather Data** | 7-day forecast via Open-Meteo (no API key required) |
| 📍 **Nearby Places** | Live data from Google Maps Places API |
| 🏛️ **Trip History** | All plans persisted in PostgreSQL / Cloud SQL |
| 📱 **Responsive UI** | Works on mobile, tablet and desktop |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Browser (HTML/CSS/JS)                       │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP POST /api/plan-trip
┌────────────────────────────▼────────────────────────────────────┐
│                  Google Cloud Run (FastAPI)                      │
│              Pydantic validation · CORS · Routing               │
└──────┬──────────┬──────────┬──────────┬────────────────────────┘
       │          │          │          │
  ┌────▼────┐ ┌──▼────┐ ┌──▼─────┐ ┌──▼──────────┐
  │ Gemini  │ │ Maps  │ │Weather │ │   Budget    │
  │   AI    │ │  API  │ │Service │ │   Service   │
  └────┬────┘ └──┬────┘ └──┬─────┘ └──┬──────────┘
       └─────────┴──────────┴──────────┘
                             │ Parallel async orchestration
                     ┌───────▼────────┐
                     │  In-Memory     │
                     │  (Stateless)   │
                     └────────────────┘
```

---

## 📁 Project Structure

```
travel-planner-engine/
├── main.py                  # FastAPI app + routes
├── database.py              # SQLAlchemy engine & session
├── models.py                # ORM models (TripPlan)
├── schemas.py               # Pydantic request/response schemas
├── requirements.txt
├── Dockerfile
├── .env.example
├── .gitignore
│
├── services/
│   ├── gemini_service.py    # Gemini AI integration
│   ├── maps_service.py      # Google Maps (Places, Geocoding, Distance)
│   ├── itinerary_service.py # Orchestration & DB persistence
│   ├── weather_service.py   # Open-Meteo weather (free, no key)
│   └── budget_service.py    # Budget classification & validation
│
├── templates/
│   └── index.html           # Jinja2 template (served at /)
│
├── static/
│   ├── style.css            # Dark elegant theme
│   └── script.js            # Vanilla JS (rendering & API calls)
│
└── tests/
    └── test_api.py          # pytest test suite (30+ tests)
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- pip

### 1. Clone & Install

```bash
git clone https://github.com/yourname/travel-planner-engine.git
cd travel-planner-engine
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env and fill in your API keys
```

### 3. Run the Application

```bash
python main.py
```

Open **http://localhost:8000** in your browser.

> **Note:** Without API keys the app still works — it uses a smart fallback plan and SQLite automatically.

---

## 🔑 Environment Setup

| Variable | Description | Required |
|---|---|---|
| `GEMINI_API_KEY` | [Google AI Studio](https://aistudio.google.com/) key | Yes (AI features) |
| `GOOGLE_MAPS_API_KEY` | Maps Platform key with Places + Geocoding + Distance Matrix | Yes (Maps features) |
| `DATABASE_URL` | PostgreSQL connection string | No (defaults to SQLite) |
| `APP_HOST` | Server host (default: `0.0.0.0`) | No |
| `APP_PORT` | Server port (default: `8000`) | No |
| `DEBUG` | Enable hot reload (default: `false`) | No |

---

## ☁️ Google Cloud SQL Setup

```bash
# 1. Create Cloud SQL PostgreSQL instance
gcloud sql instances create travel-planner-db \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=us-central1

# 2. Create database and user
gcloud sql databases create travel_planner --instance=travel-planner-db
gcloud sql users create traveler --instance=travel-planner-db --password=<strong-password>

# 3. Get connection name
gcloud sql instances describe travel-planner-db --format="value(connectionName)"

# 4. Set DATABASE_URL in .env
DATABASE_URL=postgresql://traveler:<password>@/travel_planner?host=/cloudsql/<CONNECTION_NAME>
```

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Serve frontend UI |
| `GET` | `/health` | Health check |
| `POST` | `/api/plan-trip` | Generate AI trip plan |
| `GET` | `/api/docs` | Swagger UI |
| `GET` | `/api/redoc` | ReDoc UI |

### Example Request

```bash
curl -X POST http://localhost:8000/api/plan-trip \
  -H "Content-Type: application/json" \
  -d '{
    "destination": "Kyoto, Japan",
    "days": 5,
    "budget": 2000,
    "travelers": 2,
    "interests": ["culture", "food", "history"]
  }'
```

---

## 🧪 Testing

```bash
# Install test dependencies (included in requirements.txt)
pytest tests/ -v

# With coverage
pytest tests/ -v --tb=short
```

The test suite covers:
- Health & frontend endpoints
- Trip CRUD operations
- Input validation (22+ edge cases)
- Budget service logic
- OpenAPI schema availability

---

## 🐳 Docker Deployment

```bash
# Build
docker build -t travel-planner-engine .

# Run
docker run -p 8000:8000 \
  -e GEMINI_API_KEY=your_key \
  -e GOOGLE_MAPS_API_KEY=your_key \
  travel-planner-engine
```

---

## ☁️ Google Cloud Run Deployment

```bash
# 1. Authenticate
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# 2. Enable APIs
gcloud services enable run.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com

# 3. Create Artifact Registry
gcloud artifacts repositories create travel-planner-repo \
  --repository-format=docker --location=us-central1

# 4. Build & Push via Cloud Build
gcloud builds submit \
  --tag us-central1-docker.pkg.dev/YOUR_PROJECT_ID/travel-planner-repo/travel-planner:latest

# 5. Deploy to Cloud Run
gcloud run deploy ai-travel-planner \
  --image us-central1-docker.pkg.dev/YOUR_PROJECT_ID/travel-planner-repo/travel-planner:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8000 \
  --memory 512Mi \
  --set-env-vars "GEMINI_API_KEY=your_key,GOOGLE_MAPS_API_KEY=your_key,APP_HOST=0.0.0.0,APP_PORT=8000"

# 6. Get your live URL
gcloud run services describe ai-travel-planner \
  --region us-central1 \
  --format="value(status.url)"
```

> 🔗 **Live URL format:** `https://ai-travel-planner-xxxx-uc.a.run.app`

---

## 🔐 Security Features

- **Environment variables** — all secrets via `.env` / Cloud Secret Manager
- **Pydantic validation** — strict input validation with whitelist for interests
- **CORS middleware** — configurable allowed origins
- **Non-root Docker** — runs as `appuser`
- **Exception handling** — global handler, no stack trace leakage
- **SQL injection safe** — SQLAlchemy ORM parameterized queries
- **Input sanitization** — destination `strip().title()` normalization

---

## 🛣️ Future Improvements

- [ ] User authentication (Google OAuth)
- [ ] Real-time collaboration on trip plans
- [ ] Flight and hotel booking integration
- [ ] Offline mode with service workers
- [ ] Multi-language support
- [ ] AR destination previews
- [ ] Social sharing of itineraries
- [ ] Currency conversion with live rates

---

## 🏆 Google Services Integration

| Service | Usage | Status |
|---|---|---|
| **Gemini 1.5 Flash** | Full AI itinerary, attractions, food, gems, tips, budget | ✅ Active |
| **Google Maps Places API** | Nearby tourist attractions from real Maps data | ✅ Active |
| **Google Maps JavaScript API**| Interactive, dynamic maps rendering destination and nearby places on the frontend | ✅ Active |
| **Geocoding API** | Destination lat/lng for map context | ✅ Active |
| **Distance Matrix API** | Travel time between places | ✅ Active |
| **Google Analytics (GA4)** | Advanced user behavior tracking, funnel analysis, and conversion events | ✅ Active |
| **Google Tag Manager** | Centralized tag management for seamless marketing and tracking deployments | ✅ Active |
| **Google Cloud Run** | Serverless container deployment — scales to zero | ✅ Deployed |
| **Google Cloud Build** | CI/CD pipeline — builds Docker image in the cloud | ✅ Active |
| **Google Artifact Registry** | Stores Docker images for Cloud Run deployments | ✅ Active |

---

## 📄 License

MIT — see [LICENSE](LICENSE) for details.

---

*Built for the AI Travel Planning Hackathon · Powered by Google Cloud & Gemini AI*

---

> 🛠️ **Developed using [Antigravity](https://antigravity.dev) by Google DeepMind** — an advanced agentic AI coding assistant that scaffolded the full-stack architecture, services, frontend, tests, and deployment configuration of this project.
