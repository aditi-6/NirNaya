import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

response = client.chat.completions.create(
    model="openai/gpt-oss-20b",
    messages=[
        {
            "role": "user",
            "content": "Reply with exactly: NirNaya AI CONNECTED"
        }
    ]
)

print(response.choices[0].message.content)

import json


def build_grounded_prompt(investigation_result):
    """
    Creates a prompt containing only verified backend facts.
    """

    return f"""
Analyze the following verified transaction investigation result.

IMPORTANT:
- These facts come from the deterministic backend.
- Do not change the backend's determination.
- Do not invent missing information.
- If information is unavailable, explicitly say it is unavailable.

VERIFIED INVESTIGATION RESULT:

{json.dumps(investigation_result, indent=2)}

Return your response according to the required AI response structure.
"""