# 🎓 ClassOps – Institutional Workflow Automation

**ClassOps** is a streamlined, enterprise-grade institutional management platform. It empowers educators and administrators to automate academic workflows with a focus on speed, security, and high-fidelity institutional insights.

---

## 🚀 Key Institutional Features

- **Simplified RBAC (Dual-Tier Matrix):** A refined Role-Based Access Control system focusing on `VIEW` and `EDIT` permissions for total administrative clarity.
- **Bulk Deployment Suite:** Orchestrate large-scale onboarding by deploying institutional roles and member assignments via JSON specifications.
- **Differentiated Portals:** Independent, secure interfaces for Students (**Portal**) and Teachers (**Insights**), optimized for their specific academic needs.
- **Institutional Analytics:** Unified dashboard for course health, syllabus completion metrics, and global institutional stats.
- **Automated Compliance:** Subject-wise tracking with Google Classroom synchronization and NBA/NAAC compliance report generation.

---

## 🏗 System Architecture

### Institutional Command Center (`/admin`)
The centralized administrative authority. A standalone website featuring a **high-end shadcn-inspired dark theme**.
- **Identities Management:** Define roles and tag them with parent departments (e.g., CSE, MECH).
- **Focused Matrix:** A 2-tier grid to toggle capabilities per role:
    - `VIEW`: Data acquisition and visibility rights.
    - `EDIT`: Content mutation and system-level authority.
- **Bulk Operations:** Drag-and-drop JSON deployment for mass identity provisioning.

### Optimized Native Frontend
A high-performance React/Vite application built for maximum productivity:
- **Automatic Routing:** Upon login, the system discovers authorized portals and defaults to the most relevant dashboard (Student vs. Teacher).
- **Core Feature Set:** Focused on 7 institutional nodes: Insights, Portal, Attendance, Meet, AI Tools, Evaluations, and Timetable.

---

## 🛠 Tech Stack

- **Frontend:** React (Vite), TailwindCSS, Vue.js (Admin UI)
- **Backend:** Flask (Python), Jinja2
- **Database:** AWS DynamoDB (Scalable NoSQL with persistent institutional registry)
- **Integrations:** Google Classroom API, Google Calendar, Gemini AI (Vertex AI)

---

## ⚙️ Institutional Setup

### Deployment
1. `cd Backend` -> `pip install -r requirements.txt` -> `python app.py`
2. `cd Frontend` -> `npm install` -> `npm run dev`

### Administrative Access
Navigate to `{BACKEND_URL}/admin`
- **Identifier:** `username`
- **Passcode:** `password`
*(Highly recommended to set `ADMIN_USERNAME` and `ADMIN_PASSWORD` in environment variables).*

---

## 🔒 Security & Integrity

- **Database-First:** The system is 100% database-driven. Configurations are permanent and never reset on server restarts.
- **API Hardening:** Every endpoint is protected by real-time institutional permission decorators.
- **Isolated Control:** Administrative functions are decoupled from Google OAuth to minimize the attack surface.
