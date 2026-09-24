# 🎓 Campus Hub — Unified Campus Management System

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/Framework-Flask_3.0.3-green.svg)](https://flask.palletsprojects.com/)
[![Database](https://img.shields.io/badge/Database-SQLite%2FSQLAlchemy-orange.svg)](https://www.sqlalchemy.org/)
[![Frontend](https://img.shields.io/badge/Frontend-HTML5%20%7C%20CSS3%20%7C%20JS-yellow.svg)](#frontend--backend-architecture)
[![PWA Ready](https://img.shields.io/badge/PWA-Supported-purple.svg)](#progressive-web-app-pwa)
[![License](https://img.shields.io/badge/License-MIT-brightgreen.svg)](#license)

> **Campus Hub** is a full-stack, single-repository Web Application designed to streamline daily campus life for students and administrators. It integrates notice broadcasting, mess menu schedules, hostel maintenance complaints tracking, lost & found reporting, and real-time in-app notifications into a single, modern interface.

---

## 📌 Repository Submission Compliance

This repository satisfies all **Mandatory Project Submission Rules**:
- **Single GitHub Repository:** Full-stack codebase contained within one unified repository.
- **Frontend & Backend Integrated:** Backend built with **Python/Flask** RESTful routing and object-relational mapping (SQLAlchemy); Frontend built with dynamic **Jinja2 Templates**, custom responsive **Vanilla CSS**, and **JavaScript PWA** service workers.

---

## ✨ Key Features

### 🔐 1. Authentication & Role-Based Access Control (RBAC)
* Secure student registration with Roll Number and Hostel details.
* Password hashing with `werkzeug.security` (PBKDF2 SHA-256).
* Role segregation into **Student** and **Administrator** views with protected decorated routes (`@login_required`, `@admin_required`).

### 📢 2. Campus Notice Board
* Dynamic notice creation with categories (*Academic*, *Hostel*, *Events*, *General*).
* Support for **pinned priority notices** that remain at the top of student feeds.

### 🍲 3. Weekly Mess Menu
* Interactive daily meal schedule tracker for Breakfast, Lunch, and Dinner across all 7 days of the week.
* Admin panel to edit and update weekly meal offerings dynamically.

### 🛠️ 4. Hostel Complaint Management System
* Lodging complaints with category tags (*Plumbing*, *Electrical*, *Carpentry*, etc.) and priority levels (*High*, *Medium*, *Low*).
* Status tracking pipeline: `Pending` ➔ `In Progress` ➔ `Resolved`.
* Worker assignment tracking and expected resolution timelines updated directly by hostel admins.

### 🔍 5. Lost & Found Portal
* Report lost items or catalog found belongings around campus.
* Status management (`Active`, `Claimed`) to keep listings clean and updated.

### 🔔 6. Real-Time In-App Notifications
* Automatic notifications triggered upon complaint status updates or admin announcements.
* Unread badge counter and history view.

### 📱 7. Progressive Web App (PWA)
* Web App Manifest (`manifest.json`) and Service Worker (`sw.js`) integration for mobile installability and offline support.

---

## 🏗️ Architecture & Project Structure

```
Campus_hub-project/
├── app.py                  # Main Flask Server, API routes, App Context & Seed Logic
├── models.py               # SQLAlchemy ORM Models (User, Complaint, Notice, MessMenu, etc.)
├── requirements.txt        # Python package dependencies
├── .gitignore              # Ignored files (virtual environment, database instances, cache)
├── README.md               # Complete Project Documentation
├── static/                 # Static Assets (Frontend)
│   ├── css/
│   │   └── style.css       # Custom Glassmorphism UI Styling & Responsive Layouts
│   ├── manifest.json       # PWA Web App Manifest
│   └── sw.js               # Service Worker Script
└── templates/              # Frontend Views (Jinja2 HTML Templates)
    ├── base.html           # Master layout with navigation header & mobile sidebar
    ├── login.html          # User authentication login view
    ├── signup.html         # User registration view
    ├── dashboard.html      # Student dashboard summary
    ├── complaints.html     # Complaint submission & history modal
    ├── lost_found.html     # Lost & found catalog & item submission
    ├── mess_menu.html      # Weekly mess schedule
    ├── notices.html        # Notice board feed
    ├── notifications.html  # User notification history
    ├── profile.html        # User profile & account details
    └── admin/              # Administrator Control Center
        ├── dashboard.html  # System-wide metrics & complaint management
        ├── mess_menu.html  # Admin weekly menu editor
        └── notices.html    # Admin notice publishing portal
```

---

## 🚀 Quickstart & Installation Guide

### Prerequisites
* **Python 3.10+**
* `pip` (Python package manager)

### 1. Clone the Repository
```bash
git clone https://github.com/Sachin95999/Campus_hub-project.git
cd Campus_hub-project
```

### 2. Set Up Virtual Environment (Optional but Recommended)
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the Application
```bash
python app.py
```

The application will start on **`http://127.0.0.1:5000`**. The database schema (`campus.db`) and seed data (default notices & mess menu) will be automatically created on initial boot.

---

## 🛠️ Tech Stack Details

| Layer | Technology |
|---|---|
| **Backend Framework** | Python 3.14 / Flask 3.0.3 |
| **ORM / Database** | SQLAlchemy / SQLite |
| **Frontend Templates** | Jinja2 Engine |
| **Styling** | Vanilla CSS3 (Custom Responsive Grid, CSS Variables, Glassmorphism) |
| **Client-Side Scripts** | JavaScript (ES6+), PWA Service Worker |
| **Security** | Werkzeug Password Hashing, Session Security, RBAC Guards |

---

## 🔑 Demo Account Setup & Testing Guide

To test administrator functionality during evaluation:
1. Register a new user account through the `/signup` route.
2. To grant **Admin privileges** to the user in SQLite database:
   ```python
   # Run in python interactive terminal or via app context
   from app import app, db, User
   with app.app_context():
       u = User.query.filter_by(roll_no="YOUR_ROLL_NO").first()
       u.is_admin = True
       db.session.commit()
   ```
3. Log back in to access the `/admin/dashboard` route.

---

## 📄 License
This project is open-source under the **MIT License**.
