# AI Money Tracker

A production-quality personal finance web application built with Python Django, Bootstrap 5, SQLite, Chart.js, and Pandas. Record income and expenses, visualize spending with charts, and get AI-based spending insights.

## Features

- **User Authentication**: Register, login, logout using Django built-in auth
- **Dashboard**: Total Income, Total Expense, Remaining Balance
- **Transaction Management**: Add income/expense with category, description, date
- **Category System**: Food, Travel, Rent, Shopping, Utilities (extensible)
- **Charts**: 
  - Expense Distribution (Pie Chart)
  - Monthly Expense Trend (Bar Chart)
- **AI Spending Insights**: Detects categories exceeding 40% of expenses
- **Bonus Features**: Monthly trend chart, filter by category, CSV export

## Quick Start

```bash
# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1   # Windows PowerShell
# source venv/bin/activate     # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Start server
python manage.py runserver
```

Visit http://127.0.0.1:8000/

## Project Structure

```
money-tracker/
├── manage.py
├── money_tracker/          # Project settings
├── tracker/                # Main app
│   ├── models.py
│   ├── views.py
│   ├── forms.py
│   ├── ai_analyzer.py
│   └── admin.py
├── templates/
├── static/
└── requirements.txt
```

## Admin Panel

Create a superuser to access the admin panel at `/admin/`:

```bash
python manage.py createsuperuser
```

## Tech Stack

- **Backend**: Django 5.x
- **Database**: SQLite
- **Frontend**: Bootstrap 5
- **Charts**: Chart.js
- **Analysis**: Pandas
