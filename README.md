# 💰 AI Money Tracker

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Django](https://img.shields.io/badge/Django-5.x-green)
![License](https://img.shields.io/badge/License-MIT-yellow)
![Deployment](https://img.shields.io/badge/Deployed%20on-Render-purple)
![Status](https://img.shields.io/badge/Project-Active-brightgreen)

AI Money Tracker is a full‑stack personal finance web application built using Python Django.

The application allows users to:

* Track income and expenses
* Manage loans and EMIs
* Visualize financial trends with charts
* Receive AI‑based financial insights

It demonstrates full‑stack development, data visualization, and financial analytics, making it a strong portfolio project.

---

# 🌐 Live Demo

🚀 Try the live application

[https://ai-money-tracker-ejvs.onrender.com](https://ai-money-tracker-ejvs.onrender.com)

---

# ✨ Key Features

## 🔐 Authentication System

* User registration
* Secure login/logout
* Django authentication system
* Session-based authentication

---

## 📊 Financial Dashboard

Users get an instant overview of their finances.

Includes:

* Total Income
* Total Expenses
* Remaining Balance
* Monthly financial summary

---

## 💸 Expense & Income Tracking

Users can:

* Add income transactions
* Add expense transactions
* Categorize transactions
* Add description and date
* Track spending history

---

## 📁 Category System

Predefined categories:

* Food
* Travel
* Rent
* Shopping
* Utilities

Categories can easily be extended.

---

## 💳 Loan & EMI Tracking

Track personal loans and monthly EMIs.

Features include:

* Add multiple loans
* Track EMI payments
* Monitor remaining loan balance
* Loan payment history
* EMI progress tracking

Example loans:

* Home Loan
* Car Loan
* Education Loan
* Personal Loan

---

## 📈 Data Visualization

Charts built using Chart.js.

Includes:

### Expense Distribution

Pie chart showing spending categories.

### Monthly Expense Trend

Bar chart showing monthly spending patterns.

---

## 🤖 AI Spending Insights

Financial insights generated using Pandas.

Examples:

* Detect categories exceeding 40% of total spending
* Identify overspending patterns
* Provide financial insights

---

## 📤 Additional Features

* Monthly expense analysis
* Category filtering
* CSV export of financial data
* Responsive Bootstrap UI

---


# 🚀 Installation

Clone the repository.

```
git clone https://github.com/yourusername/ai-money-tracker.git
cd ai-money-tracker
```

Create virtual environment.

```
python -m venv venv
```

Activate environment.

Windows:

```
.\\venv\\Scripts\\Activate.ps1
```

Linux / Mac:

```
source venv/bin/activate
```

Install dependencies.

```
pip install -r requirements.txt
```

Run migrations.

```
python manage.py migrate
```

Start development server.

```
python manage.py runserver
```

Open in browser:

[http://127.0.0.1:8000/](http://127.0.0.1:8000/)

---

# ⚙ Admin Panel

Create admin user:

```
python manage.py createsuperuser
```

Access admin panel:

```
/admin/
```

---

# 🧰 Tech Stack

| Layer         | Technology          |
| ------------- | ------------------- |
| Backend       | Django 5            |
| Database      | SQLite / PostgreSQL |
| Frontend      | Bootstrap 5         |
| Charts        | Chart.js            |
| Data Analysis | Pandas              |
| Deployment    | Render              |
| Server        | Gunicorn            |

---

# 🗂 Project Structure

```
money-tracker/
│
├── manage.py
│
├── money_tracker/
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
│
├── tracker/
│   ├── models.py
│   ├── views.py
│   ├── forms.py
│   ├── ai_analyzer.py
│   ├── expense_predictor.py
│   └── admin.py
│
├── templates/
├── static/
└── requirements.txt
```

---

# 🌍 Deployment

The application is deployed using:

* Render (cloud hosting)
* Gunicorn (WSGI server)
* PostgreSQL (production database)

Live application:

[https://ai-money-tracker-ejvs.onrender.com](https://ai-money-tracker-ejvs.onrender.com)

---

# 📈 Future Improvements

Potential upgrades:

* Recurring transactions
* Financial goal tracking
* Notification system for spending alerts
* Mobile-friendly UI improvements
* Advanced analytics dashboard
* Bank account integration (open banking APIs)
* Mobile app version

---


# 👨‍💻 Author

Anandu Narayanan

AI Trainer | Machine Learning | Django Developer

Focus areas:

* Artificial Intelligence
* Machine Learning
* Django Web Applications
* Data Analytics

---

# ⭐ Support

If you like this project:

* Star the repository
* Fork it
* Share it
