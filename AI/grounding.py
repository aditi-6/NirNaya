import os
from dotenv import load_dotenv

import json


def build_grounded_prompt(investigation_result, question=None):
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

FOLLOW-UP QUESTION TO ANSWER:
{question if question else "No follow-up question provided."}

IMPORTANT:
If a follow-up question is provided, you MUST answer that specific
question in the "follow_up_answer" field.

Return your response according to the required AI response structure.
"""