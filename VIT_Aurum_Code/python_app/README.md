# SmartBudget — Personal Finance Planner

A simple command-line personal finance planner built in Python.

## Features
- Log income and expenses (with keyword-based auto-categorization)
- Set monthly budgets per category, with over-budget alerts
- Low-balance warnings with rotating money-saving tips
- Monthly summary report (income, expense, net, spend by category)
- Savings goal tracker with progress percentage
- On-demand "good financial habit" tips
- PIN login (salted PBKDF2 hash, slowed and capped guesses) via `security.py`
- Recent entries with delete, month-end spending forecast, CSV export (formula-injection safe), editable alert limit

## How to run
No external libraries needed — pure Python standard library (`sqlite3`).

```bash
python main.py
```

A `finance.db` SQLite file will be created automatically in this folder
the first time you run it — that's where all your data is stored.

## File structure
- `database.py` — SQLite schema and connection setup
- `categorizer.py` — keyword-based auto-categorization rules
- `tips.py` — libraries of rotating savings/habit tips
- `finance_manager.py` — core business logic (the "brain" of the app)
- `security.py` — PIN hashing and login
- `emailer.py` — sends your summary to Gmail over SMTP
- `main.py` — command-line menu (the interface)

## Next steps (good ideas for your Second Review demo)
- Add a Tkinter or Streamlit GUI on top of `finance_manager.py`
  (no changes needed to the logic layer — just call the same methods)
- Add CSV import for bank statements
- Add PDF/Excel export of the monthly summary
- Add charts (Matplotlib/Plotly) for spending by category

## Emailing your summary to Gmail (menu option 13)
Gmail needs an **App Password**, not your normal password:
1. Turn on 2-Step Verification at https://myaccount.google.com/security
2. Create an app password at https://myaccount.google.com/apppasswords
3. Either set it once per session (`export GMAIL_APP_PASSWORD="abcd efgh ijkl mnop"`)
   or type it when asked. It is never saved to disk.
