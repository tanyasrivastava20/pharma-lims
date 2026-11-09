# PharmaLIMS 4.0

A Laboratory Information Management System (LIMS) for a pharmaceutical lab, modelled on industrial pharma ERP/LIMS software.
It manages products and materials, sample login, the lab workflow (receipt, allocation, testing, review), master data, users and reports.

- **Frontend:** React 18 + Vite (plain CSS, light and dark theme)
- **Backend:** Python Flask, SQLAlchemy, SQLite, JWT login, bcrypt password hashing
- **Reports:** CSV and PDF export, checked CSV import

## What it does

| Area | Features |
|---|---|
| Sign-in | Username and password, JWT tokens, logout that invalidates the token, change password |
| Roles | Admin, Quality Analyst, Lab Technician - menus and API both enforce them |
| Sample login | Create, change, delete/cancel, display; packaging rows; history of every change; PDF report per sample |
| Lab workflow | Sample Created -> Received -> Testing Assigned -> Analysis Completed -> Approved / Rejected |
| Products | Product / Material Master with search, sorting, paging, CSV and PDF export, checked CSV import |
| Master data | Parties, test characteristics, miscellaneous, assays, sampling inspection, specifications |
| Users (Admin) | Create, edit, activate/deactivate, reset passwords, delete |
| Logging | access, audit (logins, changes, workflow, exports), app and error logs in `backend/logs/` |

## Project layout

```
pharma-lims/
├── backend/                 Flask API
│   ├── app.py               starts the server
│   ├── config.py            settings (read from .env)
│   ├── database.py          SQLAlchemy / SQLite setup
│   ├── seed.py              creates the starter accounts and demo data
│   ├── models/              database tables
│   ├── routes/              REST endpoints (one file per area)
│   ├── services/            business rules and validation
│   ├── middleware/          login/role checks, error handling, request logging
│   ├── utils/               helpers (passwords, paging, logging, demo data)
│   ├── logs/                log files are written here
│   └── instance/            the SQLite database file is created here
├── frontend/                React app
│   └── src/
│       ├── pages/           one file per screen
│       ├── components/      header, sidebar, shared widgets
│       ├── services/api.js  all calls to the backend
│       └── styles/app.css
└── .vscode/                 tasks to start both servers
```

## Requirements

- **Python 3.10 or newer** (developed on 3.12, also used with 3.14)
- **Node.js 20.19 or newer** (check with `node -v`)

## Setup (first time only)

### 1. Backend

Windows (PowerShell or Command Prompt):

```
cd backend
py -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python seed.py --demo
```

macOS / Linux:

```
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python seed.py --demo
```

`seed.py` creates the three starter accounts below. Add `--demo` to also load sample products, parties and four demo samples.
It is safe to run more than once.

### 2. Frontend

```
cd frontend
npm install
```

## Run it

You need two terminals, one for each part. Leave both open.

**Terminal 1 - backend** (from `backend/`, with the virtual environment active):

```
python app.py
```

**Terminal 2 - frontend** (from `frontend/`):

```
npm run dev
```

Then open **http://localhost:5173**.

In VS Code you can instead press `Ctrl+Shift+P`, choose **Tasks: Run Task**, and pick **Run everything**.

## Starter accounts

| Username | Password | Role |
|---|---|---|
| admin | admin123 | Admin |
| analyst | Analyst12345 | Quality Analyst |
| technician | Technician12345 | Lab Technician |

These are **demo passwords**. Change them (user menu -> Change password, or the Users page) before showing the project to anyone,
and set your own values in `backend/.env` (`SEED_*_PASSWORD`) before running `seed.py` on a real setup.
Passwords may contain letters and numbers only: at least 8 characters, with an uppercase letter, a lowercase letter and a number.

## What each role can do

| | Admin | Quality Analyst | Lab Technician |
|---|---|---|---|
| See samples | all | only samples assigned to them | assigned to them, plus ones they logged |
| Log and edit samples | yes | no | create; edit their own until received |
| Delete / cancel samples | yes | no | no |
| Receive samples | yes | no | yes |
| Assign to an analyst | yes | no | no |
| Record test results | yes | their assigned samples | their assigned samples |
| Complete the analysis | yes | yes | no |
| Approve / reject | yes | no | no |
| Products, master data | read and change | read only | read only |
| Users | manage | no | no |

## API overview

All responses look like `{"success": true, "message": "", "data": {...}}`. Errors use `"success": false` with a message.
Send the token as `Authorization: Bearer <token>`.

| Area | Endpoints |
|---|---|
| Auth | `POST /api/auth/login`, `/register` (Admin), `/logout`, `/change-password`, `GET /api/auth/me` |
| Users (Admin) | `GET/POST /api/users`, `GET/PUT/DELETE /api/users/<id>`, `POST /api/users/<id>/reset-password` |
| Products | `GET/POST /api/products`, `GET/PUT/DELETE /api/products/<id>` |
| Samples | `GET/POST /api/samples`, `GET/PUT/DELETE /api/samples/<id>`, `GET /api/samples/summary` |
| Workflow | `POST /api/samples/<id>/receive`, `/assign`, `/observe`, `/approve`, `/reject` |
| Master data | `GET/POST /api/master/<type>`, `GET/PUT/DELETE /api/master/<type>/<id>` (`party`, `test`, `misc`, `assay`, `sampling`, `spec`) |
| Search | `GET /api/search/samples` (also `?q=`, `?status=`, `?batch_no=` ... on the sample list) |
| Export | add `?format=pdf` to `/api/export/samples`, `/products`, `/master/<type>`; `GET /api/export/samples/<id>` is a one-sample PDF report |
| Import (Admin) | `POST /api/import/products`, `/api/import/master/<type>` with `?dry_run=true` and `?mode=create\|upsert` |
| Health | `GET /api/health` |

List endpoints accept `page`, `per_page`, `sort`, `order` and search/filter parameters.

## Troubleshooting

- **PowerShell says "running scripts is disabled"** when you run `npm`: run
  `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned`, or use `npm.cmd` instead of `npm`, or use Command Prompt.
- **"Cannot reach the server" in the browser:** the backend is not running. Start it (Terminal 1) and refresh.
- **Port already in use:** another copy is still running. Close the old terminal (Ctrl+C) and start again.
- **Forgot the admin password:** from `backend/` with the virtual environment active, delete `instance/pharmalims.db` and run `python seed.py --demo` again (this erases all data).
- **Logs:** look in `backend/logs/` - `audit.log` shows who did what, `error.log` shows crashes with a reference number.

## Before publishing to GitHub

- Never commit `backend/.env` (it is already in `.gitignore`). Only `.env.example` is meant to be public.
- Replace the demo passwords and set long random `SECRET_KEY` and `JWT_SECRET_KEY` values in your own `.env`
  (for example with `python -c "import secrets; print(secrets.token_hex(32))"`).
- The database (`backend/instance/*.db`) and logs are ignored, so no data is uploaded.

## Not included

SAP integration (the Receipt From SAP screen explains this), and the Addons, QMS and STP modules. There is no automated test suite in this repository.
