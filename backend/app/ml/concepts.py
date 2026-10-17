"""
The classifier predicts a universal *concept* (food, transport, rent ...).
Each profile type then maps concepts to its own categories, so a single model
serves students, employees and freelancers.
"""

EXPENSE_CONCEPTS = [
    "food", "groceries", "transport", "travel", "shopping", "subscriptions",
    "utilities", "rent", "fees", "books", "health", "entertainment", "events",
    "emi", "investment", "software", "taxes", "transfer_out", "cash",
]
INCOME_CONCEPTS = [
    "salary", "stipend", "allowance", "scholarship", "client_payment",
    "refund", "interest", "transfer_in",
]
CONCEPTS = EXPENSE_CONCEPTS + INCOME_CONCEPTS

# Well-known brands -> concept. Matched as whole words on the cleaned narration.
KEYWORDS = {
    "food": [
        "SWIGGY", "ZOMATO", "DOMINOS", "MCDONALDS", "KFC", "STARBUCKS", "BURGER KING",
        "PIZZA HUT", "SUBWAY", "HALDIRAMS", "CHAAYOS", "CCD", "CAFE COFFEE DAY", "EATSURE",
        "BIKANERVALA", "WOW MOMO", "FAASOS", "BEHROUZ", "CANTEEN", "MESS", "TEA STALL",
        "BARISTA", "THIRD WAVE", "BLUE TOKAI", "DUNKIN", "BASKIN", "NATURALS", "UBER EATS",
    ],
    "groceries": [
        "BLINKIT", "ZEPTO", "BIGBASKET", "DMART", "JIOMART", "INSTAMART", "RELIANCE FRESH",
        "MORE RETAIL", "SPENCERS", "NATURES BASKET", "SWIGGY INSTAMART", "MILKBASKET",
        "COUNTRY DELIGHT", "DUNZO", "KIRANA", "GENERAL STORE", "WALMART",
    ],
    "transport": [
        "UBER", "OLA", "RAPIDO", "DMRC", "METRO", "BMTC", "DTC", "INDIAN OIL", "IOCL",
        "HPCL", "BPCL", "PETROL", "FUEL", "FASTAG", "PARKING", "YULU", "BLUSMART", "NAMMA YATRI",
    ],
    "travel": [
        "IRCTC", "MAKEMYTRIP", "GOIBIBO", "INDIGO", "AIR INDIA", "VISTARA", "AKASA",
        "SPICEJET", "REDBUS", "CLEARTRIP", "IXIGO", "OYO", "AIRBNB", "ZOSTEL", "YATRA",
    ],
    "shopping": [
        "AMAZON", "FLIPKART", "MYNTRA", "AJIO", "MEESHO", "NYKAA", "DECATHLON", "ZARA",
        "H&M", "UNIQLO", "CROMA", "RELIANCE DIGITAL", "LIFESTYLE", "WESTSIDE", "PANTALOONS",
        "TATA CLIQ", "LENSKART", "BOAT", "IKEA", "PEPPERFRY", "SNAPDEAL",
    ],
    "subscriptions": [
        "NETFLIX", "SPOTIFY", "HOTSTAR", "JIOHOTSTAR", "PRIME VIDEO", "AMAZON PRIME",
        "YOUTUBE PREMIUM", "YOUTUBE", "SONYLIV", "ZEE", "APPLE", "GOOGLE PLAY", "ICLOUD",
        "GOOGLE ONE", "CHATGPT", "OPENAI", "CLAUDE", "LINKEDIN PREMIUM", "DUOLINGO",
    ],
    "utilities": [
        "AIRTEL", "JIO", "VI", "VODAFONE", "BSNL", "ACT FIBERNET", "TATA PLAY", "BESCOM",
        "TATA POWER", "BSES", "ADANI ELECTRICITY", "MSEDCL", "ELECTRICITY", "RECHARGE",
        "BROADBAND", "GAS", "INDANE", "WATER BILL", "MAHANAGAR GAS",
    ],
    "rent": ["RENT", "HOSTEL", "PG", "NOBROKER", "NESTAWAY", "STANZA", "ZOLO", "HOUSING", "MAINTENANCE"],
    "fees": [
        "FEE", "FEES", "TUITION", "UNIVERSITY", "COLLEGE", "EXAM", "SEMESTER", "ADMISSION",
        "IGDTU", "IIT", "NIT", "DTU", "NSUT", "IPU", "GGSIPU", "REGISTRATION",
    ],
    "books": [
        "BOOK", "BOOKS", "STATIONERY", "STATIONERS", "XEROX", "PHOTOCOPY", "PRINTOUT",
        "UDEMY", "COURSERA", "UNACADEMY", "BYJUS", "PHYSICS WALLAH", "SCALER", "GFG",
        "GEEKSFORGEEKS", "CODING NINJAS", "EDX", "LEETCODE",
    ],
    "health": [
        "APOLLO", "PHARMACY", "PHARMEASY", "NETMEDS", "TATA MG", "MEDPLUS",
        "PRACTO", "HOSPITAL", "CLINIC", "MEDICAL", "MEDICOS", "CHEMIST", "DIAGNOSTICS",
        "LAB", "GYM", "CULTFIT", "CULT", "HEALTHIFYME",
    ],
    "entertainment": [
        "BOOKMYSHOW", "PVR", "INOX", "CINEPOLIS", "STEAM", "PLAYSTATION", "XBOX",
        "DISTRICT", "PAYTM INSIDER", "TIMEZONE", "SMAAASH", "BOWLING", "CONCERT",
    ],
    "events": [
        "DEVFOLIO", "UNSTOP", "HACKATHON", "HACKEREARTH", "MLH", "FEST", "TECHFEST",
        "CONFERENCE", "MEETUP", "WORKSHOP", "EVENTBRITE", "KONFHUB", "TOWNSCRIPT",
    ],
    "emi": [
        "EMI", "LOAN", "BAJAJ FINANCE", "BAJAJ FINSERV", "HOME CREDIT", "CRED", "CREDIT CARD BILL",
        "CC BILL", "LIC", "INSURANCE", "POLICYBAZAAR", "HDFC LIFE", "ICICI PRU", "SBI LIFE",
    ],
    "investment": [
        "ZERODHA", "GROWW", "UPSTOX", "ANGEL ONE", "KUVERA", "COIN", "SIP", "MUTUAL FUND",
        "PPF", "NPS", "SMALLCASE", "INDMONEY", "PAYTM MONEY", "FIXED DEPOSIT", "RD",
    ],
    "software": [
        "GITHUB", "AWS", "AMAZON WEB SERVICES", "GOOGLE CLOUD", "GCP", "AZURE", "DIGITALOCEAN",
        "VERCEL", "NETLIFY", "HEROKU", "FIGMA", "NOTION", "CANVA", "ADOBE", "JETBRAINS",
        "SLACK", "ZOOM", "GODADDY", "NAMECHEAP", "HOSTINGER", "RENDER", "ATLASSIAN",
    ],
    "taxes": ["GST", "INCOME TAX", "ADVANCE TAX", "TDS", "TAX", "CBDT", "ITR"],
    "cash": ["ATM", "CASH WDL", "CASH WITHDRAWAL", "ATW", "NFS"],
    "salary": ["SALARY", "SAL", "PAYROLL", "WAGES"],
    "stipend": ["STIPEND", "INTERN", "INTERNSHIP"],
    "allowance": ["POCKET MONEY", "ALLOWANCE", "MOM", "DAD", "PAPA", "MAA", "MUMMY", "FAMILY"],
    "scholarship": ["SCHOLARSHIP", "NSP", "MERIT", "FELLOWSHIP", "PRAGATI", "INSPIRE"],
    "client_payment": [
        "UPWORK", "FIVERR", "TOPTAL", "FREELANCER", "INVOICE", "PAYPAL", "STRIPE",
        "RAZORPAY", "CONSULTING", "PROJECT PAYMENT", "CLIENT",
    ],
    "refund": ["REFUND", "CASHBACK", "REVERSAL", "REVERSED", "REWARD"],
    "interest": ["INTEREST", "INT CR", "DIVIDEND", "SB INT"],
}

# concept -> category for each profile type
CONCEPT_TO_CATEGORY = {
    "student": {
        "food": "Food & Canteen", "groceries": "Food & Canteen", "transport": "Travel",
        "travel": "Travel", "shopping": "Shopping", "subscriptions": "Subscriptions",
        "utilities": "Subscriptions", "rent": "Hostel & Rent", "fees": "Fees",
        "books": "Books & Stationery", "health": "Health", "entertainment": "Fun",
        "events": "Events & Hackathons", "emi": "Other", "investment": "Other",
        "software": "Subscriptions", "taxes": "Other", "transfer_out": "Other", "cash": "Other",
        "salary": "Part-time", "stipend": "Stipend", "allowance": "Allowance",
        "scholarship": "Scholarship", "client_payment": "Part-time", "refund": "Other Income",
        "interest": "Other Income", "transfer_in": "Allowance",
    },
    "employee": {
        "food": "Food & Dining", "groceries": "Groceries", "transport": "Transport",
        "travel": "Transport", "shopping": "Shopping", "subscriptions": "Entertainment",
        "utilities": "Bills & Utilities", "rent": "Rent & Housing", "fees": "Other",
        "books": "Shopping", "health": "Health", "entertainment": "Entertainment",
        "events": "Entertainment", "emi": "EMI & Loans", "investment": "Investments",
        "software": "Bills & Utilities", "taxes": "Other", "transfer_out": "Other", "cash": "Other",
        "salary": "Salary", "stipend": "Salary", "allowance": "Other Income",
        "scholarship": "Other Income", "client_payment": "Other Income", "refund": "Other Income",
        "interest": "Other Income", "transfer_in": "Other Income",
    },
    "freelancer": {
        "food": "Food & Dining", "groceries": "Food & Dining", "transport": "Transport",
        "travel": "Transport", "shopping": "Other", "subscriptions": "Entertainment",
        "utilities": "Business Expenses", "rent": "Rent & Housing", "fees": "Business Expenses",
        "books": "Business Expenses", "health": "Health", "entertainment": "Entertainment",
        "events": "Business Expenses", "emi": "Other", "investment": "Other",
        "software": "Software & Tools", "taxes": "Taxes", "transfer_out": "Other", "cash": "Other",
        "salary": "Client Payment", "stipend": "Client Payment", "allowance": "Other Income",
        "scholarship": "Other Income", "client_payment": "Client Payment", "refund": "Other Income",
        "interest": "Other Income", "transfer_in": "Other Income",
    },
}

# Reverse map (category -> concept) so user corrections can become training data.
# "Other"/"Other Income" are deliberately left out: they carry no signal.
_CANONICAL = {
    "employee": {"Entertainment": "entertainment", "Bills & Utilities": "utilities"},
    "freelancer": {"Business Expenses": "events", "Entertainment": "entertainment"},
}
CATEGORY_TO_CONCEPT = {}
for _ptype, _mapping in CONCEPT_TO_CATEGORY.items():
    rev = {}
    for _concept, _cat in _mapping.items():
        if _cat not in ("Other", "Other Income"):
            rev.setdefault(_cat, _concept)  # first concept wins as the canonical one
    rev.update(_CANONICAL.get(_ptype, {}))
    CATEGORY_TO_CONCEPT[_ptype] = rev


def concept_type(concept: str) -> str:
    return "income" if concept in INCOME_CONCEPTS else "expense"
