import json
import os
from openai import OpenAI

from app.services.ai_data_service import get_monthly_ai_context
from app.utils.errors import AppError
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


SYSTEM_PROMPT = """
You are a personal finance assistant.

Rules:
- Use ONLY the provided data
- Do NOT invent numbers
- Do NOT give generic advice
- Every suggestion must reference a specific category or amount
- Keep answers short and practical

Return strictly valid JSON.
"""



def build_prompt(data: dict) -> str:
    return f"""
User monthly financial data (JSON):

{json.dumps(data, indent=2)}

Tasks:
1. Identify overspending categories
2. Highlight positive spending behavior
3. Suggest concrete, actionable improvements
4. Summarize the month in ONE sentence

Return JSON with exactly these keys:
- alerts (array of strings)
- good_news (array of strings)
- suggestions (array of strings)
- summary (string)
"""


def generate_ai_insights(user_id: int, month: str):  
    if not os.getenv("OPENAI_API_KEY"):
        raise AppError("AI insights are disabled", 503)
    
    data = get_monthly_ai_context(user_id, month)

    if not data["categories"] or data["total_spent"] == 0:
        return {
            "alerts": [],
            "good_news": ["No spending recorded for this month"],
            "suggestions": [],
            "summary": "No financial activity recorded for this period."
        }


    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_prompt(data)},
        ],
        temperature=0.4,
    )

    try:
        content = response.choices[0].message.content
        return json.loads(content)
    except Exception:
        raise AppError("AI response parsing failed", 500)
