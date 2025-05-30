# EventFlow

EventFlow is a secure event management platform designed to facilitate role-based event creation, registration, and moderation. The application was developed using **Domain-Driven Design (DDD)** and aligned with the **Secure Software Development Lifecycle (SSDLC)** methodology to ensure a modular architecture and strong security practices throughout development.

---

## 📋 Prerequisites

- Python 3.10+
- Docker
- Firebase account and service account JSON key
- Environment variables:
  - `FIREBASE_API_KEY`
  - `API_URL` (default: http://localhost:8000)
  - `GOOGLE_APPLICATION_CREDENTIALS` (path to Firebase JSON key)

---

## 🚀 Technologies Used

* **Backend:** Python + FastAPI
* **Frontend:** Streamlit (Python), HTML/CSS/JavaScript (template-based)
* **Database:** Firebase (User Storage) Firestore (Events and Categories storage)
* **Security & DevSecOps Tools:**

  * Bandit
  * Semgrep (via Docker)
  * pip-audit
  * Snyk
  * OWASP ZAP
* **Other:** Docker, Git, VS Code

---

## ✅ Core Features by Role

### 🔐 General

* Secure user registration and login with Firebase Authentication
* Role-based access control (RBAC)

### 👤 Admin

* Manage users and roles
* Create and manage event categories
* Access audit logs and security scan results

### 🧑‍💼 Event Manager

* Create, edit, and cancel events
* View registrations and feedback for their own events

### 👥 Client

* View available events
* Register for upcoming events
* Submit feedback

### 🛠️ Moderator

* Review and delete inappropriate feedback
* Assist Admin in comment moderation

### 🏢 Supplier

* Submit service proposals (e.g., catering, venue)
* Associate services with events

---

## 🧱 Architecture & Methodologies

* **DDD (Domain-Driven Design):**

  * Clear separation of aggregates, entities, and boundaries
  * Organized package/module structure

* **SSDLC (Secure Software Development Lifecycle):**

  * Integrated security tools during development
  * Audit logging and access control policies

* **Diagrams Included:**

  * UML class diagrams
  * DFDs (Level 1 and Level 2)
  * STRIDE threat model

---

## 🔐 Security Strategy Overview

| Type     | Phase           | Tool(s)                  | Goal                                       |
| -------- | --------------- | ------------------------ | ------------------------------------------ |
| **SAST** | Development     | Bandit, Semgrep (Docker) | Detect code flaws and insecure practices   |
| **SCA**  | Development     | pip-audit, Snyk          | Detect vulnerable dependencies             |
| **DAST** | Post-deployment | OWASP ZAP                | Simulate external hacker behavior          |
| **IAST** | Optional        | Contrast, Seeker         | Combine SAST + DAST for dynamic validation |

## ⚙️ Setup

1. Clone the repo

2. Create `.env` file based on `.env.example` with required variables

3. Install dependencies:

pip install -r requirements.txt

```bash
pip install -r requirements.txt

## 🛠️ How to Run the System

Make sure Docker and Git are installed. Run all commands from the project root.

### 1. Start Backend and Frontend

```bash
# Start FastAPI backend (exposes API at localhost:8000)
uvicorn app.main:app --reload

# Start Streamlit UI frontend (default localhost:8501)
streamlit run streamlit_app/app.py

# Admin tools for role assignment and more
streamlit run streamlit_app/admin.py
```

### 2. Assign Roles

```bash
# Assign Firebase roles manually:
python app/assign_role.py --email user@example.com --role Event_manager
```

---

## 🔒 Run Security Analysis Tools & Tests

### Prerequisites

```bash
pip install bandit pip-audit snyk
# Ensure Docker is running
chmod +x run_sast.sh run_sca.sh
```

### 3. Run SAST and SCA (Linux/macOS)

```bash
sh Security/Analysis/run_sast.sh && sh Security/Analysis/run_sca.sh
```

### 4. Run SAST and SCA (Windows PowerShell)

```powershell
.\Security\Analysis
un_sast.ps1
.\Security\Analysis
un_sca.ps1
```

These scripts scan:

* **SAST:** source code vulnerabilities with Bandit and Semgrep
* **SCA:** dependencies using pip-audit and Snyk

### 4. Run SAST and SCA (Windows PowerShell)

Run automated tests with:

pytest tests/

---

## 📁 Project Structure Overview

```
├── app/
│   ├── main.py               # FastAPI backend
│   ├── assign_role.py        # Firebase role setter
│   └── firebase_key.json     # Firebase Admin SDK
│
├── streamlit_app/
│   ├── app.py                # Main Streamlit UI
│   ├── admin.py              # Admin dashboard (optional)
│   └── modules/              # Pages: events, categories, feedback
│
├── Security/
│   └── Analysis/             # Scripts for SAST/SCA
├── requirements.txt
└── README.md
```

---

## 📌 Final Notes

* Use environment variables to store sensitive data like Firebase API keys
* Keep Firebase rules updated to ensure access control
* Review audit logs periodically to detect anomalies
* Regularly run the provided security scripts to keep dependencies and code secure

---

