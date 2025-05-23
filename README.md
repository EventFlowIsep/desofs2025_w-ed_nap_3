Event Management Platform – EventFlow

This project is a web-based platform designed to manage events. The application allows users to create, edit, register for, moderate, and manage events and services, with features tailored to different user roles: Administrator, Event Manager, Client, Moderator, and Supplier.

The goal is to provide a modular, secure, and scalable solution for managing events of various types (conferences, workshops, webinars, etc.), promoting collaboration among organizers, participants, and service providers.

Built with a Domain-Driven Design (DDD) architecture and following Secure Software Development Lifecycle (SSDLC) practices, the system ensures clarity in domain logic, role separation, and continuous security validation.

Technologies Used

Backend: Python + FastAPI

Frontend: HTML/CSS/JavaScript (with templates)

Database: SQLite

Security Tools: Bandit, Semgrep (via Docker), pip-audit, Snyk, OWASP ZAP

Others: Docker, Git, VS Code

Core Features

✅ Secure user registration and login with role-based access control

✅ Creation and editing of events by authorized Event Managers

✅ Client registration to events with capacity validation

✅ Feedback system with moderation workflows

✅ Supplier registration of services (e.g., catering, venue rental)

✅ Event category management by administrators

✅ Audit logging of critical operations for traceability

📄 Documentation Overview

This project includes:

UML and DFD diagrams (Level 1 and Level 2) for each main use case

Aggregate and package structure based on DDD

STRIDE threat model and qualitative risk analysis

Security scripts and vulnerability documentation

🔐 Security Strategy

Security was implemented with a structured plan aligned to SSDLC principles:

✅ Types of Analysis

SAST(Static Application Security Testing) - Development - Bandit, Semgrep (via Docker) Goal: Identify flaws on the source code

SCA(Software Composition Analysis) - Development - pip-audit, Snyk Goal: Verify the used librarys

DAST(Dynamic Application Security Testing) - Post-deployment (local/staging) - OWASP ZAP Goal: Simulate a attack by an external hacker

IAST(Interactive Application Security Testing) - Optional (with automated tests) - Contrast, Seeker Goal: Combine static analysis with dinamic, usefull in apps with a lot of functional tests.

Example Vulnerability Documentation

Vulnerability: Use of hardcoded password in login.py (line 14) Phase Detected: Development Type of Analysis: SAST Tool: Semgrep (Docker) Severity: High Mitigation: Replace hardcoded password with secure credential storage (e.g., environment variables or a secrets vault).

uvicorn app.main:app --reload
streamlit run streamlit_app/app.py
streamlit run streamlit_app/admin.py
python app/assign_role.py --email adminuser@gmail.com --role admin

Correr os SAST E SCA
pip install bandit
pip install pip-audit
snyk auth
Docker tem de estar aberto
chmod +x run_sast.sh run_sca.sh
./run_sast.ps1 && ./run_sca.ps1
.\Security\Analysis\run_sast.ps1
.\Security\Analysis\run_sca.ps1
Necessário ter o git instalado e correr sh Security/Analysis/run_sast.sh

