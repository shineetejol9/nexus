<h1 align="center">🚀 NEXUS</h1>

<p align="center">
  <strong>Enterprise Data Intelligence & Decision Platform</strong><br>
  Transform raw data into clean, trusted, and actionable insights through an intelligent data pipeline.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/React-19-61DAFB?style=for-the-badge&logo=react&logoColor=white" />
  <img src="https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white" />
  <img src="https://img.shields.io/badge/Tailwind_CSS-06B6D4?style=for-the-badge&logo=tailwind-css&logoColor=white" />
  <img src="https://img.shields.io/badge/JWT-Authentication-000000?style=for-the-badge&logo=jsonwebtokens&logoColor=white" />
  <img src="https://img.shields.io/badge/Pytest-Testing-0A9EDC?style=for-the-badge&logo=pytest&logoColor=white" />
</p>

---

## 📖 About

**NEXUS** is an Enterprise Data Intelligence & Decision Platform designed to transform raw and unreliable data into clean, validated, trusted, and actionable information.

The platform provides an end-to-end data pipeline that handles **data ingestion, profiling, validation, cleaning, transformation, quality analysis, storage, analytics, and anomaly detection**.

Instead of simply uploading a dataset and displaying it, NEXUS focuses on answering an important question:

> **Can we trust this data before using it for analysis and decision-making?**

The platform processes data through multiple stages and presents the resulting insights through REST APIs and an enterprise dashboard.

---

## 🔄 Data Pipeline

```text
📂 Data Sources
      ↓
📥 Ingestion
      ↓
🔍 Profiling & Validation
      ↓
🧹 Data Cleaning
      ↓
🔄 Transformation
      ↓
📊 Data Quality Engine
      ↓
🗄️ PostgreSQL
      ↓
📈 Analytics
      ↓
🚨 Anomaly Detection
      ↓
🌐 REST APIs
      ↓
📊 Enterprise Dashboard
```

---

## 📁 Project Structure

```text
nexus/
│
├── backend/
│   ├── analytics.py
│   ├── anomaly.py
│   ├── auth.py
│   ├── cleaning.py
│   ├── database.py
│   ├── ingestion.py
│   ├── profiling.py
│   ├── quality.py
│   ├── rules.py
│   ├── transformation.py
│   └── upload.py
│
├── frontend/
│   ├── public/
│   └── src/
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── quarantine/
│
├── tests/
├── notebooks/
│
├── docs/
│   ├── architecture.svg
│   ├── pipeline.svg
│   ├── ai-tools.svg
│   └── tech-stack.svg
│
├── requirements.txt
└── README.md
```

---

## 🤖 AI-Assisted Development

It helped with:

- 🏗️ Understanding the overall project structure
- 🔧 Multi-file implementation
- 🔄 Connecting frontend and backend functionality
- 🧩 Implementing features across different modules
- 🛠️ Refactoring existing code
- 🐛 Debugging project-wide issues

---

## 🔄 Development Workflow

```text
💡 Idea
   ↓
🤖 Ask AI
   ↓
🧠 Understand the Problem
   ↓
🏗️ Plan the Solution
   ↓
💻 Implement
   ↓
▶️ Run the Application
   ↓
🐛 Debug
   ↓
🧪 Test
   ↓
🔍 Review
   ↓
✅ Improve & Integrate
```

---

## 🔐 Authentication & Role-Based Access Control

NEXUS uses **JWT-based authentication** and **Role-Based Access Control (RBAC)** to provide different levels of access to different users. There are three roles: **Admin**, **Data Engineer**, and **Viewer**.

### 👑 Admin

The **Admin** has full system-level access and can:

- 📂 Upload datasets
- 🔍 View and check over all data in the system
- ⬇️ Download clean/processed data
- 👥 Manage users
- 🔒 Remove or deactivate any user account
- 📝 Monitor what each user has uploaded
- ⚙️ Manage platform operations

### 🛠️ Data Engineer

The **Data Engineer** is responsible for data and pipeline operations.

They can:

- 🧹 Modify, clean, and transform datasets
- 🔍 Profile and validate data
- ⚙️ Execute data pipelines
- 📊 Monitor data quality
- 🚨 Inspect anomalies
- 📈 Work with processed datasets

### 👁️ Viewer

The **Viewer** has restricted read-only access.

They can:

- 📊 View permitted datasets
- 🔍 Explore available information
- 📈 View analytics and insights
- 📋 View data quality information

Viewers cannot perform privileged operations such as uploading datasets or managing users.

### 🔐 Access Flow

```text
User
  ↓
Login
  ↓
JWT Authentication
  ↓
Role Verification
  ↓
Permission Check
  ↓
┌─────────────┬────────────────┬──────────┐
│    Admin    │ Data Engineer  │  Viewer  │
├─────────────┼────────────────┼──────────┤
│ Full Access │ Data & Pipeline│ Read Only│
│ User Mgmt   │  Operations    │  Access  │
└─────────────┴────────────────┴──────────┘
```

---

## 🚀 Getting Started

Clone the repository:

```bash
git clone https://github.com/shineetejol9/nexus.git
```

Move into the project:

```bash
cd nexus
```

Create a virtual environment:

```bash
python -m venv venv
```

Activate it on Windows:

```bash
venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Configure the required environment variables and PostgreSQL database, then start the backend and frontend development servers.

---

## 🤝 Contributing

Want to contribute to NEXUS?

```text
🍴 Fork
   ↓
📥 Clone
   ↓
🌿 Create Feature Branch
   ↓
💻 Build Feature
   ↓
🧪 Add Tests
   ↓
⬆️ Push Changes
   ↓
🔀 Pull Request
   ↓
🔍 Review
   ↓
✅ Merge
```

Create a feature branch:

```bash
git checkout -b feature/your-feature
```

Commit your changes:

```bash
git add .
git commit -m "Add your feature"
```

Push your branch:

```bash
git push origin feature/your-feature
```

---

## 🔮 Vision

```text
Raw Data
   ↓
Clean Data
   ↓
Trusted Data
   ↓
Analytics
   ↓
Intelligence
   ↓
Better Decisions
```


https://github.com/user-attachments/assets/f7f5a449-d876-4465-bcae-0803ce9854f9

