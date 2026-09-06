# 🎓 ClassOps – Institutional Workflow Automation

**ClassOps** is a streamlined, enterprise-grade institutional management platform. It empowers educators and administrators to automate academic workflows with a focus on speed, security, and high-fidelity institutional insights.

---

## 🚀 Key Features

- **Simplified RBAC (Dual-Tier Matrix):** A refined Role-Based Access Control system focusing on `VIEW` and `EDIT` permissions for total administrative clarity.
- **Bulk Deployment Suite:** Orchestrate large-scale onboarding by deploying institutional roles and member assignments via JSON specifications.
- **Differentiated Portals:** Independent, secure interfaces for Students (**Portal**) and Teachers (**Insights**), optimized for their specific academic needs.
- **Institutional Analytics:** Unified dashboard for course health, syllabus completion metrics, and global institutional stats.
- **Automated Compliance:** Subject-wise tracking with Google Classroom synchronization and NBA/NAAC compliance report generation.

---

## ⚙️ Getting Started

### Prerequisites
- **Python** 3.9+
- **Node.js** 18+ and npm

### Backend
```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
# source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

The backend serves on `http://localhost:5000` (see `.env.example` → `BASE_URL`).

### Frontend
```bash
cd frontend
npm install
npm run dev
```

The dev server starts at `http://localhost:5173`.

### Administrative Access
Navigate to `{BACKEND_URL}/admin`
- **Identifier:** `username`
- **Passcode:** `password`
*(Highly recommended to set `ADMIN_USERNAME` and `ADMIN_PASSWORD` in environment variables).*

---

## 🧪 Testing

Lint the frontend from `frontend/`:

```bash
npm run lint
```
