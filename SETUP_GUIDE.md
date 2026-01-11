# Project Setup Guide (PLN HSE Dashboard)

## 1. Python Version
**Strict Requirement:** `Python 3.7.x`
This project is optimized for Python 3.7. Using newer versions (3.10+) may cause dependency conflicts with legacy Pandas/SQLAlchemy versions used here.

## 2. Key Libraries & Versions
The `requirements.txt` file handles everything, but pay special attention to:

| Library | Version Constraint | Why? |
| :--- | :--- | :--- |
| **Pandas** | `1.3.x` (Default on Py3.7) | Core data processing. |
| **SQLAlchemy**| **`< 2.0`** (e.g. 1.4.x) | **CRITICAL:** Version 2.0+ crashes with Pandas 1.3. We have pinned this in `requirements.txt`. |
| **Psycopg2** | `psycopg2-binary` | Required for PostgreSQL connection. |
| **Streamlit** | Latest (Compatible) | User Interface. |

## 3. Installation Steps for Colleagues

### Windows (PowerShell)
```powershell
# 1. Verify you are using Python 3.7
python --version

# 2. Create a Virtual Environment (Recommended)
python -m venv venv

# 3. Activate the Environment
.\venv\Scripts\Activate

# 4. Install Dependencies
pip install -r requirements.txt
```

## 4. Database Credentials
Ensure the `.streamlit/secrets.toml` file is shared securely with your team (do not commit it to Git).
It should look like this:

```toml
[postgres]
user = "postgres.hmdbqxhdvebwheyucmvo"
password = "..."  # Get from Admin
host = "aws-1-ap-southeast-2.pooler.supabase.com"
port = "5432"
dbname = "postgres"
```
