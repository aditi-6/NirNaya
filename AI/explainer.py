import os
import json
from dotenv import load_dotenv
from groq import Groq

from AI.grounding import build_grounded_prompt
from AI.prompts import SYSTEM_PROMPT

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def explain_investigation(investigation_result):
    """
    Sends verified backend facts to the LLM
    and returns a grounded AI explanation.
    """

    user_prompt = build_grounded_prompt(investigation_result)

    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ],
            temperature=0.2,
            response_format={"type": "json_object"}
        )

        content = response.choices[0].message.content

        return json.loads(content)

    except Exception as e:
        return {
            "summary": "AI explanation is currently unavailable.",
            "explanation": "The verified investigation result is still available from the backend.",
            "delay_reason": None,
            "customer_reply": None,
            "follow_up_answer": None,
            "what_if_explanation": None
        }

   