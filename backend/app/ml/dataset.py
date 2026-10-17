"""
Synthetic training data that looks like real Indian bank narrations.

Two kinds of merchants per concept:
  * brands  ("SWIGGY", "IRCTC")         -> the rule layer already knows these
  * generic ("SHARMA MEDICAL STORE")     -> what the ML model must generalise to

Every row is (merchant_id, narration, concept). merchant_id lets us split
train/test *by merchant*, so the reported accuracy is on merchants the model
has never seen, not on memorised strings.
"""
import random

from app.ml.concepts import KEYWORDS, INCOME_CONCEPTS

NAMES = [
    "SHARMA", "GUPTA", "AGARWAL", "SINGH", "VERMA", "JAIN", "BANSAL", "KRISHNA", "GANESH",
    "SAI", "SHREE", "BALAJI", "ROYAL", "GOLDEN", "CITY", "STAR", "MAHALAXMI", "OM",
    "SUNRISE", "GREEN", "MODERN", "NATIONAL", "UNITED", "PRIME", "APEX", "NOVA", "VEDA",
    "KAPOOR", "MEHTA", "REDDY", "IYER", "NAIR", "PATEL", "DESAI", "CHOPRA", "MALHOTRA",
    "LAKSHMI", "DURGA", "HANUMAN", "SHIVA", "GOPAL", "ANAND", "NEW", "JAI HIND", "BHARAT",
    "OCEAN", "SKY", "LOTUS", "TULSI", "SAFFRON", "PEARL", "CROWN", "EMPIRE", "METRO CITY",
]
FIRST = ["RAHUL", "PRIYA", "AMIT", "NEHA", "ROHAN", "ANJALI", "KARAN", "POOJA", "VIKRAM",
         "SNEHA", "ARJUN", "KAVYA", "ADITYA", "ISHA", "SIDDHARTH", "RIYA", "MANISH", "TANYA"]
LAST = ["SHARMA", "GUPTA", "SINGH", "VERMA", "JAIN", "PATEL", "REDDY", "NAIR", "MEHTA",
        "KAPOOR", "IYER", "DAS", "BOSE", "KHAN", "YADAV", "MISHRA", "PANDEY", "CHAUHAN"]

GENERIC = {
    "food": ["{N} FOODS", "{N} KITCHEN", "{N} DHABA", "{N} CAFE", "{N} RESTAURANT",
             "{N} SWEETS", "{N} BAKERY", "{N} CHAI POINT", "{N} BIRYANI HOUSE", "{N} JUICE CENTER",
             "{N} PIZZERIA", "{N} TIFFIN SERVICE", "{N} CANTEEN", "{N} MESS", "{N} FAST FOOD"],
    "groceries": ["{N} KIRANA STORE", "{N} GENERAL STORE", "{N} SUPERMART", "{N} DAIRY",
                  "{N} PROVISION STORE", "{N} VEGETABLES", "{N} FRUITS", "{N} SUPERMARKET",
                  "{N} MART", "{N} GROCERY"],
    "transport": ["{N} FILLING STATION", "{N} PETROL PUMP", "{N} AUTO SERVICE", "{N} CABS",
                  "{N} FUELS", "{N} SERVICE STATION", "{N} PARKING", "{N} METRO RECHARGE"],
    "travel": ["{N} TRAVELS", "{N} TOURS", "HOTEL {N}", "{N} RESORT", "{N} HOLIDAYS",
               "{N} TOURS AND TRAVELS", "{N} GUEST HOUSE", "{N} BUS SERVICE"],
    "shopping": ["{N} FASHION", "{N} GARMENTS", "{N} FOOTWEAR", "{N} ELECTRONICS", "{N} MOBILES",
                 "{N} COLLECTION", "{N} BOUTIQUE", "{N} CLOTHING", "{N} DEPARTMENTAL STORE",
                 "{N} GIFTS", "{N} WATCHES", "{N} OPTICALS"],
    "subscriptions": ["{N} PREMIUM PLAN", "{N} SUBSCRIPTION", "{N} OTT", "{N} MUSIC PREMIUM",
                      "{N} PLUS MONTHLY", "{N} STREAMING"],
    "utilities": ["{N} BROADBAND", "{N} ELECTRICITY BOARD", "{N} MOBILE RECHARGE", "{N} TELECOM",
                  "{N} POWER DISTRIBUTION", "{N} GAS AGENCY", "{N} FIBERNET", "{N} WATER SUPPLY"],
    "rent": ["{N} PG", "{N} HOSTEL", "{N} RENT", "{N} RESIDENCY RENT", "{N} GIRLS PG",
             "{N} BOYS HOSTEL", "{N} CO LIVING", "{N} HOUSE RENT", "{N} SOCIETY MAINTENANCE"],
    "fees": ["{N} UNIVERSITY", "{N} COLLEGE FEES", "{N} INSTITUTE OF TECHNOLOGY", "{N} SCHOOL FEES",
             "EXAM FEE {N}", "{N} SEMESTER FEE", "{N} UNIVERSITY EXAM", "{N} ADMISSION"],
    "books": ["{N} BOOK DEPOT", "{N} STATIONERS", "{N} XEROX", "{N} BOOK STORE", "{N} ACADEMY",
              "{N} PHOTOSTAT", "{N} PRINTERS", "{N} COACHING", "{N} LEARNING", "{N} TUTORIALS"],
    "health": ["{N} MEDICAL STORE", "{N} PHARMACY", "{N} HOSPITAL", "{N} CLINIC", "{N} DIAGNOSTICS",
               "{N} FITNESS", "{N} CHEMIST", "{N} DENTAL CARE", "{N} PATH LAB", "{N} GYM",
               "{N} MEDICOS", "{N} HEALTHCARE"],
    "entertainment": ["{N} CINEMAS", "{N} MULTIPLEX", "{N} GAMING ZONE", "{N} FUN ZONE",
                      "{N} BOWLING", "{N} AMUSEMENT PARK", "{N} THEATRE", "{N} EVENTS LIVE"],
    "events": ["{N} HACKATHON", "{N} TECHFEST", "{N} SUMMIT", "{N} FEST REGISTRATION",
               "{N} CONFERENCE", "{N} WORKSHOP", "{N} CODING CONTEST", "{N} MEETUP TICKET"],
    "emi": ["{N} FINANCE EMI", "{N} LOAN EMI", "{N} INSURANCE PREMIUM", "{N} CAPITAL EMI",
            "{N} CREDIT CARD BILL", "{N} HOUSING FINANCE", "{N} LIFE INSURANCE"],
    "investment": ["{N} SECURITIES", "{N} MUTUAL FUND SIP", "{N} STOCK BROKING", "{N} WEALTH",
                   "{N} AMC SIP", "{N} INVESTMENTS", "{N} GOLD SAVINGS"],
    "software": ["{N} CLOUD", "{N} HOSTING", "{N} SOFTWARE", "{N} DOMAINS", "{N} SAAS",
                 "{N} DEV TOOLS", "{N} API CREDITS", "{N} SERVER"],
    "taxes": ["GST PAYMENT {N}", "INCOME TAX {N}", "{N} TAX PAYMENT", "ADVANCE TAX {N}",
              "TDS PAYMENT {N}", "PROFESSIONAL TAX {N}"],
    "transfer_out": ["{P}", "{P}", "{P} SPLIT", "SENT TO {P}", "{P} SHARE"],
    "cash": ["ATM WDL {N}", "CASH WITHDRAWAL {N}", "NFS ATM {N}", "ATM CASH {N}"],
    "salary": ["{N} TECHNOLOGIES SALARY", "{N} SOLUTIONS PAYROLL", "SALARY {N} PVT LTD",
               "{N} SYSTEMS SAL", "{N} INFOTECH SALARY CREDIT"],
    "stipend": ["{N} LABS STIPEND", "INTERNSHIP STIPEND {N}", "{N} TECH INTERN STIPEND",
                "{N} RESEARCH STIPEND", "STIPEND {N} INNOVATIONS"],
    "allowance": ["{P} POCKET MONEY", "FROM PAPA {P}", "MOM {P}", "{P} MONTHLY ALLOWANCE",
                  "DAD {P}", "{P} FAMILY"],
    "scholarship": ["{N} SCHOLARSHIP", "NSP SCHOLARSHIP {N}", "{N} FOUNDATION SCHOLARSHIP",
                    "{N} FELLOWSHIP", "{N} MERIT SCHOLARSHIP"],
    "client_payment": ["{N} INVOICE", "UPWORK {N}", "{N} CONSULTING PAYMENT", "{N} DIGITAL CLIENT",
                       "{N} PROJECT PAYMENT", "{N} STUDIOS INVOICE"],
    "refund": ["REFUND {N}", "{N} CASHBACK", "REVERSAL {N}", "{N} REFUND CREDIT", "REWARD {N}"],
    "interest": ["SB INTEREST {N}", "INTEREST CREDIT {N}", "{N} DIVIDEND", "INT CR {N}"],
    "transfer_in": ["{P}", "{P}", "FROM {P}", "{P} RETURNED", "{P} SPLIT"],
}

EXPENSE_TEMPLATES = [
    "UPI/DR/{ref}/{M}/{bank}/{vpa}@{psp}/{note}",
    "UPI-{M}-{vpa}@{psp}-{ifsc}-{ref}-{note}",
    "POS {card} {M} {city}",
    "ECOM PUR {M} {ref}",
    "{M}",
    "{M} {city}",
    "BIL/ONL/{ref}/{M}",
    "ACH D- {M}-{ref}",
    "IMPS/P2A/{ref}/{M}",
]
INCOME_TEMPLATES = [
    "NEFT CR-{ifsc}-{M}-{note}",
    "UPI/CR/{ref}/{M}/{bank}/{vpa}@{psp}",
    "IMPS/P2A/{ref}/{M}",
    "{M}",
    "BY TRANSFER-{M}",
    "UPI-{M}-{vpa}@{psp}-{ifsc}-{ref}-UPI",
]
BANKS = ["YESB", "HDFC", "ICIC", "SBIN", "UTIB", "KKBK", "PUNB", "BARB"]
PSPS = ["ybl", "okaxis", "okhdfcbank", "paytm", "oksbi", "ibl", "axl"]
CITIES = ["DELHI", "NEW DELHI", "MUMBAI", "BANGALORE", "PUNE", "NOIDA", "GURGAON", "HYDERABAD", "IN"]
NOTES = ["Payment", "UPI", "Pay", "NA", "Sent via app", "Paid", ""]


def _fill(template: str, merchant: str, rng: random.Random) -> str:
    vpa = merchant.lower().replace(" ", "")[:12]
    return template.format(
        M=merchant, ref=rng.randint(10**11, 10**12 - 1), bank=rng.choice(BANKS),
        vpa=vpa, psp=rng.choice(PSPS), note=rng.choice(NOTES),
        ifsc=f"{rng.choice(BANKS)}0{rng.randint(100000, 999999)}",
        card=f"{rng.randint(4000, 5999)}XXXXXXXX{rng.randint(1000, 9999)}",
        city=rng.choice(CITIES),
    )


def _person(rng: random.Random) -> str:
    return f"{rng.choice(FIRST)} {rng.choice(LAST)}"


def build_dataset(seed: int = 42, generic_per_pattern: int = 6, variants: int = 3):
    """Returns list of (merchant_id, narration, concept)."""
    rng = random.Random(seed)
    rows = []
    for concept in GENERIC:
        templates = INCOME_TEMPLATES if concept in INCOME_CONCEPTS else EXPENSE_TEMPLATES
        merchants = []
        for brand in KEYWORDS.get(concept, []):
            merchants.append(brand)
        for pattern in GENERIC[concept]:
            for _ in range(generic_per_pattern):
                if "{P}" in pattern:
                    merchants.append(pattern.format(P=_person(rng)))
                else:
                    merchants.append(pattern.format(N=rng.choice(NAMES)))
        for m in set(merchants):
            for _ in range(variants):
                rows.append((m, _fill(rng.choice(templates), m, rng), concept))
    rng.shuffle(rows)
    return rows
