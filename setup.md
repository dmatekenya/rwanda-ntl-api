# Setup Guide

This guide will walk you through setting up the Rwanda Night-Time Lights API on your local machine.

## Prerequisites
- **Database Ready**: We assume you have already set up your PostgreSQL database with the night-time lights tables from yesterday's session

## Step 1: Python Environment Setup

### 1.1 Clone the Repository

```bash
# Clone the repository
git clone https://github.com/your-username/rwanda-ntl-api.git
cd rwanda-ntl-api
```

### 1.2 Create Python Virtual Environment

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On macOS/Linux:
source .venv/bin/activate

# On Windows:
.venv\Scripts\activate

# Verify activation (should show your project path)
which python
```

### 1.3 Install Python Dependencies

```bash
# Install required packages
pip install -r requirements.txt

# Or install individually:
pip install fastapi uvicorn psycopg2-binary python-dotenv pydantic
```


## Step 2: Database Connection

Since you already have your PostgreSQL database set up from yesterday's session with all the required tables (`cells`, `pop`, `ntl_annual`, `ntl_monthly`), we just need to ensure our API can connect to it.

## Step 3: Configuration

### 3.1 Create Environment File

Create a `.env` file in your project root:

```bash
# Create .env file
touch .env
```

Add your database configuration to `.env` (use your actual database credentials from yesterday):
```env
DATABASE_HOST=localhost
DATABASE_NAME=your_database_name
DATABASE_USER=your_username
DATABASE_PASSWORD=your_password
DATABASE_PORT=5432
```


## Step 4: Running the API

### 4.1 Test Database Connection

First, verify that your API can connect to the database by runnuing the code below in Jupyter Notebook:

```python
import sys
import os
sys.path.append('src')

from database import get_db_cursor

try:
    cursor, conn = get_db_cursor()
    cursor.execute("SELECT COUNT(*) FROM cells")
    result = cursor.fetchone()
    print(f"✅ Database connection successful! Found {result[0]} cells in database")
    cursor.close()
    conn.close()
except Exception as e:
    print(f"❌ Database connection failed: {e}")
```

### 4.2 Start the FastAPI Application

Start the development server:

```bash
# Make sure you're in the project root directory
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

You should see output like:
```
INFO:     Will watch for changes in these directories: ['/path/to/rwanda-ntl-api']
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using WatchFiles
INFO:     Started server process [12346]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### 4.3 Test API Endpoints

Open your browser and test these URLs:

1. **Basic health check**: http://localhost:8000/
2. **Database health check**: http://localhost:8000/health
3. **API documentation**: http://localhost:8000/docs
4. **Get cells data**: http://localhost:8000/cells


## Step 5: Share Your API with ngrok

Want to share your API with friends or access it from anywhere? Use **ngrok** to create a public tunnel to your local API!

### 5.1 Install ngrok
- Follow installation instructions for your platform from [here](https://dashboard.ngrok.com/get-started/setup/windows)

### 5.2 Set Up ngrok Authentication

1. **Create a free account** at [ngrok.com](https://ngrok.com/signup)
2. **Get your authtoken** from [dashboard.ngrok.com/get-started/your-authtoken](https://dashboard.ngrok.com/get-started/your-authtoken)
3. **Add your authtoken** to ngrok:

```bash
# Replace YOUR_AUTH_TOKEN with your actual token
ngrok authtoken YOUR_AUTH_TOKEN
```

### 5.3 Expose Your API

With your FastAPI server running on port 8000:

```bash
# In a new terminal window (keep your API running in the other terminal)
ngrok http 8000
```

You'll see output like:
```
ngrok                                                           

Session Status                online
Account                       your-email@example.com
Version                       3.x.x
Region                        United States (us)
Latency                       -
Web Interface                 http://127.0.0.1:4040
Forwarding                    https://abc123.ngrok-free.app -> http://localhost:8000

Connections                   ttl     opn     rt1     rt5     p50     p90
                              0       0       0.00    0.00    0.00    0.00
```

### 5.4 Share Your API

Now you can share your API with anyone using the public URL! For example:

- **Your API**: `https://abc123.ngrok-free.app/`
- **API Documentation**: `https://abc123.ngrok-free.app/docs`
- **Get cells data**: `https://abc123.ngrok-free.app/cells`

### 5.5 Monitor API Usage

ngrok provides a web interface to monitor requests:
- Open: `http://127.0.0.1:4040`
- See all API requests in real-time
- Debug any issues with requests

**Note**: The free ngrok URL changes each time you restart ngrok. For a permanent URL, consider upgrading to a paid plan.
