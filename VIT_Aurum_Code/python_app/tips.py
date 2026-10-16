"""
tips.py
Small libraries of rotating advice strings. Keeping these as plain
data (lists of strings) makes it easy to add more tips later without
touching any logic.
"""

import random

LOW_BALANCE_TIPS = [
    "Try the 50/30/20 rule: 50% needs, 30% wants, 20% savings.",
    "Pause non-essential spending for a few days to rebuild your buffer.",
    "Review your last 10 transactions — small purchases add up fast.",
    "Set up an automatic transfer to savings right after you get paid.",
    "Cancel or pause one subscription you rarely use this month.",
    "Cook at home for a few days instead of ordering food.",
    "Track every rupee for a week — awareness alone often cuts spending.",
]

OVER_BUDGET_TIPS = [
    "Consider moving next month's budget for this category slightly higher "
    "if it's consistently tight, and cut elsewhere to compensate.",
    "Check if any purchases in this category were one-time, not recurring.",
    "Set a weekly (not just monthly) limit to catch overspending earlier.",
    "Compare this month to last month — is this a trend or a one-off?",
]

GOOD_HABIT_TIPS = [
    "Log expenses daily rather than in a big batch — it's more accurate.",
    "Review your budget vs. actual spending every Sunday.",
    "Keep an emergency fund worth 3–6 months of expenses.",
    "Automate savings before you spend, not after.",
    "Set one specific savings goal with a deadline — it's easier to stick to.",
]


def random_tip(tip_list):
    """Return one random tip from the given list."""
    return random.choice(tip_list)
