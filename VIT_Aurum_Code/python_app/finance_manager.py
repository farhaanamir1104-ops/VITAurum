"""
finance_manager.py
Core business logic for SmartBudget, wrapped in a single class so
main.py (the CLI) stays thin and just calls methods on it.

Covers:
- Adding income/expense transactions (with auto-categorization)
- Calculating balance
- Budget tracking per category, with over-budget alerts
- Low-balance detection with rotating savings tips
- A simple savings goal + progress tracker
- A monthly summary report
"""

import calendar
import csv
from datetime import datetime

from database import get_connection
from categorizer import guess_category
from tips import LOW_BALANCE_TIPS, OVER_BUDGET_TIPS, GOOD_HABIT_TIPS, random_tip


class FinanceManager:
    def __init__(self, low_balance_threshold: float = 1000.0):
        # Below this balance, the app will nudge the user to save.
        self.low_balance_threshold = low_balance_threshold
        saved = self._get_setting("low_balance_threshold")
        if saved:
            self.low_balance_threshold = float(saved)

    # ------------------------------------------------------------------
    # Transactions
    # ------------------------------------------------------------------
    def add_transaction(self, amount: float, type_: str, description: str = "",
                         category: str = None, date: str = None) -> dict:
        """
        Insert a transaction. If category isn't given, auto-guess it
        from the description for expenses. Returns a dict with any
        alerts/tips that should be shown to the user right after.
        """
        if amount <= 0:
            raise ValueError("Amount must be greater than zero.")
        if type_ not in ("income", "expense"):
            raise ValueError("Type must be 'income' or 'expense'.")

        date = date or datetime.now().strftime("%Y-%m-%d")

        if type_ == "expense" and not category:
            category = guess_category(description)
        elif not category:
            category = "Income"

        conn = get_connection()
        conn.execute(
            "INSERT INTO transactions (date, type, category, amount, description) "
            "VALUES (?, ?, ?, ?, ?)",
            (date, type_, category, amount, description),
        )
        conn.commit()
        conn.close()

        result = {"category": category, "alerts": []}

        if type_ == "expense":
            balance = self.get_balance()
            if balance < self.low_balance_threshold:
                result["alerts"].append({
                    "type": "low_balance",
                    "message": f"Your balance (₹{balance:.2f}) is below your "
                               f"safety threshold (₹{self.low_balance_threshold:.2f}).",
                    "tip": random_tip(LOW_BALANCE_TIPS),
                })

            over_budget = self.check_budget_status().get(category)
            if over_budget and over_budget["over_budget"]:
                result["alerts"].append({
                    "type": "over_budget",
                    "message": f"You've spent ₹{over_budget['spent']:.2f} in "
                               f"'{category}', over your ₹{over_budget['limit']:.2f} "
                               f"monthly budget.",
                    "tip": random_tip(OVER_BUDGET_TIPS),
                })

        return result

    # ------------------------------------------------------------------
    # Balance & reporting
    # ------------------------------------------------------------------
    def get_balance(self) -> float:
        """Total income minus total expenses, all-time."""
        conn = get_connection()
        income = conn.execute(
            "SELECT COALESCE(SUM(amount), 0) AS total FROM transactions WHERE type = 'income'"
        ).fetchone()["total"]
        expense = conn.execute(
            "SELECT COALESCE(SUM(amount), 0) AS total FROM transactions WHERE type = 'expense'"
        ).fetchone()["total"]
        conn.close()
        return income - expense

    def monthly_summary(self, year: int = None, month: int = None) -> dict:
        """
        Returns a dict: {
            'income': float, 'expense': float, 'net': float,
            'by_category': {category: total_spent, ...}
        } for the given month (defaults to current month).
        """
        now = datetime.now()
        year = year or now.year
        month = month or now.month
        month_prefix = f"{year:04d}-{month:02d}"

        conn = get_connection()
        income = conn.execute(
            "SELECT COALESCE(SUM(amount), 0) AS total FROM transactions "
            "WHERE type = 'income' AND date LIKE ?",
            (f"{month_prefix}%",),
        ).fetchone()["total"]

        expense = conn.execute(
            "SELECT COALESCE(SUM(amount), 0) AS total FROM transactions "
            "WHERE type = 'expense' AND date LIKE ?",
            (f"{month_prefix}%",),
        ).fetchone()["total"]

        rows = conn.execute(
            "SELECT category, COALESCE(SUM(amount), 0) AS total FROM transactions "
            "WHERE type = 'expense' AND date LIKE ? GROUP BY category ORDER BY total DESC",
            (f"{month_prefix}%",),
        ).fetchall()
        conn.close()

        by_category = {row["category"]: row["total"] for row in rows}

        return {
            "income": income,
            "expense": expense,
            "net": income - expense,
            "by_category": by_category,
        }

    # ------------------------------------------------------------------
    # Budgets
    # ------------------------------------------------------------------
    def set_budget(self, category: str, monthly_limit: float):
        if monthly_limit <= 0:
            raise ValueError("Budget limit must be greater than zero.")
        conn = get_connection()
        conn.execute(
            "INSERT INTO budgets (category, monthly_limit) VALUES (?, ?) "
            "ON CONFLICT(category) DO UPDATE SET monthly_limit = excluded.monthly_limit",
            (category, monthly_limit),
        )
        conn.commit()
        conn.close()

    def check_budget_status(self) -> dict:
        """
        Returns {category: {'limit': x, 'spent': y, 'over_budget': bool}}
        for every category that has a budget set, for the current month.
        """
        summary = self.monthly_summary()
        spent_by_category = summary["by_category"]

        conn = get_connection()
        budgets = conn.execute("SELECT category, monthly_limit FROM budgets").fetchall()
        conn.close()

        status = {}
        for row in budgets:
            category = row["category"]
            limit = row["monthly_limit"]
            spent = spent_by_category.get(category, 0.0)
            status[category] = {
                "limit": limit,
                "spent": spent,
                "over_budget": spent > limit,
            }
        return status

    # ------------------------------------------------------------------
    # Savings goal
    # ------------------------------------------------------------------
    def set_savings_goal(self, target_amount: float, label: str = "Savings Goal"):
        conn = get_connection()
        conn.execute(
            "INSERT INTO settings (key, value) VALUES ('goal_amount', ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (str(target_amount),),
        )
        conn.execute(
            "INSERT INTO settings (key, value) VALUES ('goal_label', ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (label,),
        )
        conn.commit()
        conn.close()

    def goal_progress(self):
        """Returns (label, target, current_balance, percent) or None if no goal set."""
        conn = get_connection()
        row = conn.execute("SELECT value FROM settings WHERE key = 'goal_amount'").fetchone()
        label_row = conn.execute("SELECT value FROM settings WHERE key = 'goal_label'").fetchone()
        conn.close()

        if not row:
            return None

        target = float(row["value"])
        label = label_row["value"] if label_row else "Savings Goal"
        balance = max(self.get_balance(), 0)
        percent = min((balance / target) * 100, 100) if target > 0 else 0
        return label, target, balance, percent

    # ------------------------------------------------------------------
    # Settings, recent entries, forecast, export
    # ------------------------------------------------------------------
    def _get_setting(self, key):
        conn = get_connection()
        row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        conn.close()
        return row["value"] if row else None

    def set_threshold(self, value: float):
        if value < 0:
            raise ValueError("Limit cannot be negative.")
        conn = get_connection()
        conn.execute(
            "INSERT INTO settings (key, value) VALUES ('low_balance_threshold', ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value", (str(value),))
        conn.commit()
        conn.close()
        self.low_balance_threshold = value

    def recent_transactions(self, limit: int = 10):
        conn = get_connection()
        rows = conn.execute(
            "SELECT id, date, type, category, amount, description FROM transactions "
            "ORDER BY date DESC, id DESC LIMIT ?", (limit,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def delete_transaction(self, tx_id: int) -> bool:
        conn = get_connection()
        cur = conn.execute("DELETE FROM transactions WHERE id = ?", (tx_id,))
        conn.commit()
        conn.close()
        return cur.rowcount > 0

    def projected_month_spend(self):
        """(spent so far, projected month-end spend) using the average daily pace."""
        now = datetime.now()
        spent = self.monthly_summary()["expense"]
        days_in_month = calendar.monthrange(now.year, now.month)[1]
        return spent, spent / now.day * days_in_month

    @staticmethod
    def _safe_cell(value):
        """Stop spreadsheet formula injection: text starting with = + - @ is defanged."""
        text = "" if value is None else str(value)
        return "'" + text if text[:1] in ("=", "+", "-", "@") else text

    def export_csv(self, path: str) -> int:
        conn = get_connection()
        rows = conn.execute(
            "SELECT date, type, category, amount, description FROM transactions "
            "ORDER BY date, id").fetchall()
        conn.close()
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["date", "type", "category", "amount", "description"])
            for r in rows:
                writer.writerow([self._safe_cell(r[k]) for k in
                                 ("date", "type", "category", "amount", "description")])
        return len(rows)

    @staticmethod
    def random_habit_tip():
        return random_tip(GOOD_HABIT_TIPS)
