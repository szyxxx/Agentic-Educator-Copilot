"""
Educator Copilot — Quiz Generator
=================================
Tool for generating quiz questions from uploaded materials using LLM.
Supports Multiple Choice (with distractors) and Essay questions.
"""

import json
from lib.llm_router import call_llm_with_fallback

def generate_quiz_from_material(material_text: str, num_questions: int, quiz_type: str) -> list[dict]:
    """
    Generate quiz questions based on the provided material text.
    Returns a list of dictionaries containing the question details.
    """
    
    # Truncate material text if it's too long to save context window (approx 6k chars is usually safe for most models)
    max_chars = 15000
    if len(material_text) > max_chars:
        material_text = material_text[:max_chars] + "... [TRUNCATED]"

    prompt = f"""You are an expert university lecturer creating a quiz for your students based strictly on the provided course material.

MATERIAL:
{material_text}

TASK:
Create exactly {num_questions} questions of type: "{quiz_type}".

REQUIREMENTS:
1. Ensure questions directly test knowledge found in the material.
2. Provide the correct answer and map it to a specific topic/concept.
"""
    
    if quiz_type == "Pilihan Ganda":
        prompt += """
3. For "Pilihan Ganda" (Multiple Choice), you MUST provide exactly 4 options (A, B, C, D) where only one is correct and the other three are plausible distractors.

FORMAT: Return the output strictly as a JSON array of objects. Do not include any other text, markdown formatting, or explanations outside the JSON array.
[
  {
    "question_number": 1,
    "question": "What is...",
    "option_a": "First option",
    "option_b": "Second option",
    "option_c": "Third option",
    "option_d": "Fourth option",
    "correct_answer": "A",
    "topic": "Specific Topic Name"
  }
]
"""
    elif quiz_type == "Esai":
        prompt += """
3. For "Esai" (Essay), provide the question and a brief grading rubric or key points expected in the answer.

FORMAT: Return the output strictly as a JSON array of objects. Do not include any other text, markdown formatting, or explanations outside the JSON array.
[
  {
    "question_number": 1,
    "question": "Explain how...",
    "correct_answer": "Expected key points: 1..., 2..., 3...",
    "topic": "Specific Topic Name"
  }
]
"""
    else: # Campuran
        prompt += """
3. For "Campuran" (Mixed), provide a mix of Multiple Choice (with 4 options and correct answer A/B/C/D) and Essay questions. 
If it is an Essay question, leave the options empty and provide expected key points in the correct_answer.

FORMAT: Return the output strictly as a JSON array of objects. Do not include any other text, markdown formatting, or explanations outside the JSON array.
[
  {
    "question_number": 1,
    "type": "Pilihan Ganda",
    "question": "What is...",
    "option_a": "First option",
    "option_b": "Second option",
    "option_c": "Third option",
    "option_d": "Fourth option",
    "correct_answer": "A",
    "topic": "Specific Topic Name"
  },
  {
    "question_number": 2,
    "type": "Esai",
    "question": "Explain how...",
    "option_a": "",
    "option_b": "",
    "option_c": "",
    "option_d": "",
    "correct_answer": "Expected key points...",
    "topic": "Specific Topic Name"
  }
]
"""

    response = call_llm_with_fallback("quiz_generation", prompt)
    
    # Attempt to parse JSON safely
    try:
        # Strip potential markdown formatting block
        clean_resp = response.strip()
        if clean_resp.startswith("```json"):
            clean_resp = clean_resp[7:]
        if clean_resp.startswith("```"):
            clean_resp = clean_resp[3:]
        if clean_resp.endswith("```"):
            clean_resp = clean_resp[:-3]
            
        return json.loads(clean_resp.strip())
    except Exception as e:
        print(f"[Quiz Generator] Failed to parse JSON: {e}\nResponse was: {response}")
        return []
