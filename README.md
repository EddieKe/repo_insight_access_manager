# RepoInsight Access Manager

![React](https://img.shields.io/badge/React-18.x-61DAFB?logo=react&style=for-the-badge)
![Material UI](https://img.shields.io/badge/Material%20UI-v5-007FFF?logo=mui&style=for-the-badge)
![Flask](https://img.shields.io/badge/Flask-2.x-000000?logo=flask&logoColor=white&style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?logo=python&style=for-the-badge)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)

> **Explore platform access rights – fast, reliable, and enterprise-ready.**

---

## What is RepoInsight Access Manager?

A comprehensive dashboard for managing platform repository permissions and user access. This application provides a visual interface to explore workspaces, code repositories, security teams, and user access rights within your organization.

---

## Architecture Overview

```mermaid
graph LR
  A[React Frontend] <--> B[Flask API<br/>+ Cache Layer]
  B <--> C[Platform REST APIs]

  subgraph Local / Hosted App
    A
    B
  end

  C --> Platform[Your Code Hosting Platform]


Project Structure
text
├── backend/                # Python Flask backend
│   ├── app.py              # REST API endpoints
│   ├── platform_client.py  # Platform data retrieval and processing
│   ├── cache.py            # Caching system
│   ├── settings_manager.py # Configuration management
│   ├── excel_generator.py  # Excel export functionality
│   └── report_*.py         # Access report generation and parsing
│
└── frontend/               # React frontend
    ├── src/
    │   ├── api/            # API integration
    │   ├── components/     # React components
    │   └── assets/         # Static assets
    └── public/             # Public files
Setup & Installation
Prerequisites
Python 3.8 or higher

Node.js 16 or higher

Access to a platform (e.g., Azure DevOps) with appropriate credentials

Backend Setup
Navigate to the backend directory:

text
cd backend
Create a virtual environment (optional but recommended):

text
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
Install dependencies:

text
pip install -r requirements.txt
Start the Flask server:

text
python app.py
The API will be available at http://localhost:5000/v1

Frontend Setup
Navigate to the frontend directory:

text
cd frontend
Install dependencies:

text
npm install
Start the development server:

text
npm run dev
The application will be available at http://localhost:5173

