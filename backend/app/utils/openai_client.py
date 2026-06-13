from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_weekly_insight(stats: dict, transactions: list[dict]) -> str:
    summary_lines = [
        f"- {cat}: ₹{round(amt, 2)}" for cat, amt in stats["by_category"].items()
    ]
    prompt = f"""You are a friendly personal finance advisor. 
Analyze this week's spending and give 3-4 actionable, specific insights.
Be encouraging but honest. Keep it under 200 words.

Spending summary:
{chr(10).join(summary_lines)}

Total spent: ₹{round(stats['total_spent'], 2)}
Total income: ₹{round(stats['total_income'], 2)}
Transactions: {stats['transaction_count']}

Give insights in bullet points. Start with what they did well."""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=300,
        temperature=0.7,
    )
    return response.choices[0].message.content