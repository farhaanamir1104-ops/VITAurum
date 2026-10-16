"""
main.py
Command-line interface for SmartBudget. Run this file to use the app:

    python main.py

Everything here is just user interaction (input/print) and calling
into FinanceManager — no business logic lives in this file.
"""

from database import init_db
from getpass import getpass

from finance_manager import FinanceManager
from security import has_pin, set_pin, remove_pin, verify_pin, login
from emailer import (EmailError, get_email, set_email, send_email, summary_text, valid_email)


MENU = """
=========== SmartBudget ===========
1. Add Income
2. Add Expense
3. View Balance
4. Set Budget for a Category
5. View Budget Status
6. View Monthly Summary
7. Set / View Savings Goal
8. Get a Financial Habit Tip
9. Recent Entries / Delete
10. Month-End Forecast
11. Export to CSV
12. Settings (alert limit, PIN)
13. Email Summary to Gmail
14. Exit
====================================
"""


def prompt_float(message: str) -> float:
    while True:
        try:
            return float(input(message).strip())
        except ValueError:
            print("Please enter a valid number.")


def show_alerts(alerts):
    for alert in alerts:
        print(f"\n⚠️  {alert['message']}")
        print(f"💡 Tip: {alert['tip']}")


def add_income(fm: FinanceManager):
    amount = prompt_float("Amount received: ")
    description = input("Description (e.g. 'Salary', 'Freelance'): ").strip()
    result = fm.add_transaction(amount, "income", description)
    print(f"\n✅ Income of ₹{amount:.2f} added under '{result['category']}'.")


def add_expense(fm: FinanceManager):
    amount = prompt_float("Amount spent: ")
    description = input("Description (e.g. 'Zomato dinner'): ").strip()
    category_input = input("Category (leave blank to auto-detect): ").strip()
    category = category_input if category_input else None

    result = fm.add_transaction(amount, "expense", description, category=category)
    print(f"\n✅ Expense of ₹{amount:.2f} logged under '{result['category']}'.")
    show_alerts(result["alerts"])


def view_balance(fm: FinanceManager):
    balance = fm.get_balance()
    print(f"\n💰 Current balance: ₹{balance:.2f}")
    if balance < fm.low_balance_threshold:
        print(f"⚠️  This is below your safety threshold of ₹{fm.low_balance_threshold:.2f}.")


def set_budget(fm: FinanceManager):
    category = input("Category to budget (e.g. 'Food'): ").strip().title()
    limit = prompt_float(f"Monthly limit for '{category}': ")
    fm.set_budget(category, limit)
    print(f"\n✅ Budget for '{category}' set to ₹{limit:.2f}/month.")


def view_budget_status(fm: FinanceManager):
    status = fm.check_budget_status()
    if not status:
        print("\nNo budgets set yet. Use option 4 to set one.")
        return

    print("\n--- Budget Status (this month) ---")
    for category, info in status.items():
        flag = "🔴 OVER" if info["over_budget"] else "🟢 OK"
        print(f"{category:<15} spent ₹{info['spent']:.2f} / ₹{info['limit']:.2f}  [{flag}]")


def view_monthly_summary(fm: FinanceManager):
    summary = fm.monthly_summary()
    print("\n--- Monthly Summary ---")
    print(f"Income:  ₹{summary['income']:.2f}")
    print(f"Expense: ₹{summary['expense']:.2f}")
    print(f"Net:     ₹{summary['net']:.2f}")

    if summary["by_category"]:
        print("\nSpending by category:")
        for category, total in summary["by_category"].items():
            print(f"  {category:<15} ₹{total:.2f}")
    else:
        print("\nNo expenses logged yet this month.")


def savings_goal(fm: FinanceManager):
    progress = fm.goal_progress()
    if progress:
        label, target, balance, percent = progress
        print(f"\n🎯 {label}: ₹{balance:.2f} / ₹{target:.2f} ({percent:.1f}%)")
    else:
        print("\nNo savings goal set yet.")

    choice = input("Set a new goal? (y/N): ").strip().lower()
    if choice == "y":
        label = input("Goal name (e.g. 'Emergency Fund'): ").strip() or "Savings Goal"
        target = prompt_float("Target amount: ")
        fm.set_savings_goal(target, label)
        print(f"\n✅ Goal '{label}' set to ₹{target:.2f}.")


def recent_and_delete(fm: FinanceManager):
    rows = fm.recent_transactions(10)
    if not rows:
        print("\nNo entries yet.")
        return
    print()
    for r in rows:
        sign = "+" if r["type"] == "income" else "-"
        print(f"#{r['id']:<4} {r['date']}  {sign}₹{r['amount']:.2f}  {r['category']:<13} {r['description']}")
    choice = input("\nEnter an ID to delete it (blank to go back): ").strip()
    if choice:
        print("Deleted." if fm.delete_transaction(int(choice)) else "No entry with that ID.")


def forecast(fm: FinanceManager):
    spent, projected = fm.projected_month_spend()
    print(f"\nSpent so far this month: ₹{spent:.2f}")
    print(f"At this pace, month-end spending: ₹{projected:.2f}")
    income = fm.monthly_summary()["income"]
    if income and projected > income:
        print("⚠️  That is more than your income this month.")
        print(f"💡 Tip: {fm.random_habit_tip()}")


def export_data(fm: FinanceManager):
    path = input("File name [transactions.csv]: ").strip() or "transactions.csv"
    count = fm.export_csv(path)
    print(f"\n✅ Exported {count} entries to {path}.")


def settings_menu(fm: FinanceManager):
    print(f"\nLow-balance alert limit: ₹{fm.low_balance_threshold:.2f}")
    new = input("New limit (blank to keep): ").strip()
    if new:
        fm.set_threshold(float(new))
        print("Updated.")
    print("PIN lock is", "ON" if has_pin() else "OFF")
    choice = input("(s)et/change PIN, (r)emove PIN, (e)mail address, Enter to go back: ").strip().lower()
    if choice == "e":
        set_email(input("Gmail address: ").strip())
        print("Email address saved.")
    elif choice == "s":
        set_pin(getpass("New PIN (4-6 digits): "))
        print("PIN saved.")
    elif choice == "r" and has_pin():
        if verify_pin(getpass("Current PIN: ")):
            remove_pin()
            print("PIN removed.")
        else:
            print("Wrong PIN.")


def email_summary(fm: FinanceManager):
    address = get_email()
    if address:
        print(f"\nSending to {address} (change it with option 12 > e).")
    else:
        address = input("\nYour Gmail address: ").strip()
        if not valid_email(address):
            print("That does not look like an email address.")
            return
        set_email(address)
    try:
        send_email(address, "My VIT Aurum summary", summary_text(fm))
        print(f"✅ Summary sent to {address}. Check your inbox.")
    except EmailError as e:
        print(f"❌ {e}")


def main():
    init_db()
    if not login():
        return
    fm = FinanceManager(low_balance_threshold=1000.0)

    print("Welcome to SmartBudget — your personal finance planner.")

    while True:
        print(MENU)
        choice = input("Choose an option: ").strip()

        try:
            if choice == "1":
                add_income(fm)
            elif choice == "2":
                add_expense(fm)
            elif choice == "3":
                view_balance(fm)
            elif choice == "4":
                set_budget(fm)
            elif choice == "5":
                view_budget_status(fm)
            elif choice == "6":
                view_monthly_summary(fm)
            elif choice == "7":
                savings_goal(fm)
            elif choice == "8":
                print(f"\n💡 {fm.random_habit_tip()}")
            elif choice == "9":
                recent_and_delete(fm)
            elif choice == "10":
                forecast(fm)
            elif choice == "11":
                export_data(fm)
            elif choice == "12":
                settings_menu(fm)
            elif choice == "13":
                email_summary(fm)
            elif choice == "14":
                print("\nGoodbye! Keep those good financial habits going. 💰")
                break
            else:
                print("\nInvalid option, please choose 1-14.")
        except ValueError as e:
            print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()
