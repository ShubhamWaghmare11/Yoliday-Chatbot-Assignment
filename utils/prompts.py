def build_prompt(query: str) -> str:
    return f"""
    You are an expert assistant.

    Given the topic: "{query}", respond with:
    1. A casual summary (as if explaining to a friend).
    2. A formal academic explanation (detailed, like a scholarly article).

    Respond exactly as a JSON dictionary with two keys:
    {{"casual_response": "...", "formal_response": "..."}}

    Make sure:
    - Use double quotes for keys and string values (valid JSON).
    - Escape any special characters properly.
    - Do NOT include markdown formatting or extra text.

    Output ONLY the JSON dictionary.
"""



def build_refine_prompt(input_json: str) -> str:
    return f"""
    You will receive a JSON dictionary with two fields. Refine and polish the texts for clarity and style, then return ONLY the refined JSON dictionary with the same keys.

    Input JSON:
    {input_json}

    Output only the refined JSON dictionary, no extra text.
    """
