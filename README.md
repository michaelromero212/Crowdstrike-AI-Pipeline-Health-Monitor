# CrowdStrike AI Pipeline Health Monitor

A demo-ready AI pipeline health monitoring application showcasing ML/LLM infrastructure monitoring, automated remediation, and cost optimization. Designed for interview demonstrations and production-minded engineering practices.

![Dashboard Preview](docs/dashboard-preview.png)

## Features

- **Health Checks**: Continuous monitoring of ML pipeline latency, correctness, drift, and resource utilization
- **Auto-Remediation**: Configurable remediation strategies with dry-run support
- **Incident Management**: Track incidents, remediation attempts, and resolution history
- **Infrastructure Analysis**: Multi-cloud metrics simulation (AWS/GCP/OCI)
- **Rightsizing Recommendations**: Cost optimization with actionable recommendations
- **Interactive Dashboard**: React + Plotly visualizations with CrowdStrike-inspired design

## Quick Start

### Using Docker Compose (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/Crowdstrike-AI-Pipeline-Health-Monitor.git
cd Crowdstrike-AI-Pipeline-Health-Monitor

# Start all services
docker-compose up --build

# Open the dashboard
open http://localhost:3000
```

### Local Development

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## Demo Walkthrough

### 5-Minute Demo Script

1. **Show Healthy State** (1 min)
   - Open dashboard at http://localhost:3000
   - Point out all health checks passing (green indicators)
   - Show the latency trend chart

2. **Inject Failure** (1 min)
   ```bash
   python scripts/inject_failure.py --type latency --severity high
   ```
   - Click "Run All Checks" on dashboard
   - Observe failing check and incident creation

3. **Demonstrate Remediation** (1 min)
   - Navigate to Incidents tab
   - Select the incident
   - Click "Dry Run" to preview remediation
   - Click "Restart Service" to remediate

4. **Show Infrastructure View** (1 min)
   - Switch to Infrastructure tab
   - Highlight multi-cloud metrics
   - Show rightsizing opportunities table
   - Point out potential monthly savings

5. **Verify Recovery** (1 min)
   ```bash
   python scripts/inject_failure.py --clear
   ```
   - Run checks again, show all passing
   - Incident status changes to "Resolved"

## Architecture

```
┌─────────────────┐     ┌─────────────────┐
│  React Frontend │────▶│  FastAPI Backend │
│  (Plotly.js)    │     │  (Python 3.11)   │
└─────────────────┘     └────────┬─────────┘
                                 │
        ┌────────────────────────┼────────────────────────┐
        │                        │                        │
        ▼                        ▼                        ▼
┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│ Health Checker │     │ Auto-Remediator│     │Cloud Ingestor │
│ - Latency      │     │ - Restart      │     │ - AWS metrics │
│ - Correctness  │     │ - Clear Cache  │     │ - GCP metrics │
│ - Drift (KS)   │     │ - Scale Hint   │     │ - OCI metrics │
│ - Resources    │     │ - Rollback     │     └───────────────┘
└───────────────┘     └───────────────┘
        │                        │
        ▼                        ▼
┌─────────────────────────────────────────┐
│            SQLite Database              │
│  - health_checks, check_runs            │
│  - incidents, remediation_attempts      │
│  - instance_metrics, volumes            │
└─────────────────────────────────────────┘
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/healthchecks` | GET | List all configured health checks |
| `/healthchecks/run` | POST | Run a specific health check |
| `/healthchecks/run-all` | POST | Run all enabled health checks |
| `/incidents` | GET | List incidents with filtering |
| `/remediate` | POST | Trigger remediation for an incident |
| `/metrics` | GET | Prometheus metrics endpoint |
| `/infrastructure/summary` | GET | Multi-cloud infrastructure summary |
| `/rightsizing/opportunities` | GET | List rightsizing recommendations |
| `/inject-failure` | POST | Inject failure for demo |

## Tech Stack

- **Backend**: Python 3.11, FastAPI, SQLAlchemy, Prometheus Client
- **Frontend**: React 18, TypeScript, Plotly.js, Vite
- **Database**: SQLite (demo) / PostgreSQL (production)
- **Container**: Docker, Docker Compose
- **Analysis**: NumPy, SciPy (KS-test for drift detection)

## Configuration

Copy the environment template and customize:

```bash
cp infra/localsample.env .env
```

Key configuration options:
- `DATABASE_URL`: Database connection string
- `LATENCY_THRESHOLD_MS`: Health check latency threshold
- `MAX_REMEDIATION_RETRIES`: Auto-remediation retry limit
- `SLACK_WEBHOOK_URL`: (Optional) Slack alerting

## Testing

```bash
# Backend tests
cd backend
pytest tests/ -v

# Frontend tests
cd frontend
npm test
```

## CrowdStrike Alignment

This project demonstrates skills relevant to the Infrastructure Optimization Engineer role:

| Job Requirement | Project Feature |
|----------------|-----------------|
| Analyze infrastructure utilization | Multi-cloud metrics ingestor |
| Monitoring, analysis, and reporting | Health checks + Plotly dashboards |
| Scripts for analysis & automation | Demo scripts + remediation logic |
| Infrastructure optimization | Rightsizing recommendation engine |
| Incident response | Incident management + auto-remediation |
| Multi-cloud experience | AWS/GCP/OCI metric simulation |
| Containerization & K8s | Docker Compose + K8s-style configs |
| DB & SQL proficiency | SQLite + example queries |

## Project Structure

```
Crowdstrike-AI-Pipeline-Health-Monitor/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application
│   │   ├── db.py                # Database models
│   │   ├── metrics.py           # Prometheus exporter
│   │   ├── api/                 # API routes
│   │   └── services/            # Business logic
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── App.tsx              # Main component
│   │   ├── pages/               # Dashboard, Infrastructure, Incidents
│   │   ├── components/          # Reusable components
│   │   └── styles/              # CrowdStrike theme
│   └── Dockerfile
├── scripts/
│   ├── inject_failure.py        # Failure injection CLI
│   └── demo_run.sh              # Interactive demo script
├── examples/queries/            # SQL analysis examples
├── optimization_playbooks/      # Report templates
└── docker-compose.yml
```

## License

MIT License - Demo/Interview Project

---

Built for CrowdStrike Infrastructure Optimization Engineer interview demonstration.
