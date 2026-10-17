ROLES = ("user", "admin", "demo")
PROFILE_TYPES = ("student", "employee", "freelancer")
LIVING_TYPES = ("hostel", "pg", "day_scholar", "home")
TX_TYPES = ("income", "expense")

# Each profile type gets its own expense categories and income sources.
CATEGORIES = {
    "student": {
        "expense": [
            "Food & Canteen", "Hostel & Rent", "Books & Stationery", "Fees",
            "Travel", "Subscriptions", "Events & Hackathons", "Shopping",
            "Health", "Fun", "Other",
        ],
        "income": ["Allowance", "Scholarship", "Stipend", "Part-time", "Other Income"],
    },
    "employee": {
        "expense": [
            "Rent & Housing", "Food & Dining", "Groceries", "Transport",
            "Bills & Utilities", "EMI & Loans", "Shopping", "Health",
            "Entertainment", "Investments", "Other",
        ],
        "income": ["Salary", "Bonus", "Other Income"],
    },
    "freelancer": {
        "expense": [
            "Business Expenses", "Software & Tools", "Taxes", "Food & Dining",
            "Rent & Housing", "Transport", "Health", "Entertainment", "Other",
        ],
        "income": ["Client Payment", "Other Income"],
    },
}

# Student: big one-off costs shown separately so they don't wreck the daily budget
SEMESTER_CATEGORIES = {"Fees", "Books & Stationery", "Events & Hackathons"}

# Employee: 50/30/20 rule grouping (anything not listed counts as "wants")
NEEDS = {"Rent & Housing", "Groceries", "Transport", "Bills & Utilities", "EMI & Loans", "Health"}
SAVINGS = {"Investments"}

# Default monthly budget template as a share of monthly income
BUDGET_TEMPLATES = {
    "student": {
        "Food & Canteen": 0.30, "Travel": 0.10, "Subscriptions": 0.05,
        "Shopping": 0.10, "Fun": 0.10, "Health": 0.05,
    },
    "employee": {
        "Rent & Housing": 0.25, "Food & Dining": 0.08, "Groceries": 0.08,
        "Transport": 0.05, "Bills & Utilities": 0.05, "Shopping": 0.07,
        "Entertainment": 0.05, "Investments": 0.20,
    },
    "freelancer": {
        "Business Expenses": 0.10, "Software & Tools": 0.05, "Taxes": 0.15,
        "Food & Dining": 0.10, "Rent & Housing": 0.25, "Entertainment": 0.05,
    },
}


def categories_for(profile_type: str | None) -> dict:
    return CATEGORIES.get(profile_type or "student", CATEGORIES["student"])


def all_categories(profile_type: str | None) -> list[str]:
    c = categories_for(profile_type)
    return c["expense"] + c["income"]
