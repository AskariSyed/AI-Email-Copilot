import json

from openai import OpenAI

from app.core.config import settings

# Initialize client using existing configuration
client = OpenAI(api_key=settings.LLM_API_KEY, base_url=settings.LLM_BASE_URL)


def evaluate_generation(
    generated_text: str,
    context_text: str,
    input_text: str,
    expected_concepts: list[str],
) -> dict:
    """
    Uses LLM-as-a-judge to evaluate generation quality.
    This is isolated from the deterministic retrieval metrics.
    """

    prompt = f"""
    You are an impartial judge evaluating an AI-generated email or chat response.
    Evaluate the following response based on these metrics:
    
    1. Context Relevance (1-5): How much does the response rely on the provided context?
    2. Groundedness (1-5): Is the response fully supported by the context without hallucinating facts?
    3. Answer Relevance (1-5): Does the response actually address the original input/query?
    4. Concept Coverage (0-1): Does it cover the core ideas of these expected concepts: {expected_concepts}? (1 for Yes, 0 for No)

    Input/Query:
    {input_text}
    
    Provided Context:
    {context_text}
    
    Generated Response:
    {generated_text}
    
    Respond strictly in JSON format matching this exact schema:
    {{
        "context_relevance": int,
        "groundedness": int,
        "answer_relevance": int,
        "concept_coverage": int,
        "reasoning": "brief explanation"
    }}
    """

    try:
        completion = client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )
        result = json.loads(completion.choices[0].message.content)
        return result
    except Exception as e:
        print(f"Error during LLM evaluation: {e}")
        return {
            "context_relevance": 0,
            "groundedness": 0,
            "answer_relevance": 0,
            "concept_coverage": 0,
            "reasoning": f"Error: {e}",
        }
