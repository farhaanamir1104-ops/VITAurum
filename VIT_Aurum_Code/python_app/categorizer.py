"""
categorizer.py
Very small rule-based classifier: guesses a spending category from
a free-text description, using keyword matching. This is what lets
the app auto-categorize expenses instead of forcing the user to pick
a category every time.
"""

# Map of category -> list of keywords that suggest that category.
# Everything is compared in lowercase.
CATEGORY_KEYWORDS = {
    "Food":         ["restaurant", "food", "swiggy", "zomato", "lunch",
                      "dinner", "breakfast", "cafe", "grocery", "groceries"],
    "Transport":    ["uber", "ola", "petrol", "fuel", "bus", "train",
                      "metro", "taxi", "auto", "parking"],
    "Rent":         ["rent", "landlord", "housing"],
    "Utilities":    ["electricity", "water bill", "wifi", "internet",
                      "recharge", "gas bill", "phone bill"],
    "Entertainment": ["movie", "netflix", "spotify", "game", "concert",
                       "party", "outing"],
    "Shopping":     ["amazon", "flipkart", "myntra", "clothes", "shopping"],
    "Health":       ["medicine", "hospital", "doctor", "pharmacy", "clinic"],
    "Education":    ["course", "book", "tuition", "fees", "college", "exam"],
    "Savings":      ["savings", "fd", "deposit", "mutual fund", "sip"],
}

DEFAULT_CATEGORY = "Other"


def guess_category(description: str) -> str:
    """
    Look through CATEGORY_KEYWORDS for the first category whose keyword
    appears in the description. Falls back to 'Other' if nothing matches.
    """
    if not description:
        return DEFAULT_CATEGORY

    text = description.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text:
                return category

    return DEFAULT_CATEGORY
