import json
import asyncio
import os
import google.generativeai as genai
from typing import List, Dict

# Assuming run from faith-compass/backend
try:
    from app.services.llm_service import generate_response
    from app.services.scripture_service import ground_message
    from app.services.safety_guardian import check_text
except ImportError:
    print("Please run this script from the backend/ directory using `python -m eval.evaluate`")
    exit(1)

async def evaluate_test_case(tc: Dict):
    print(f"Running TC: {tc['id']} - {tc['label']}")
    input_text = tc['input']
    expected = tc['expected']
    
    # 1. Safety Check
    safety = check_text(input_text)
    if expected.get('should_block'):
        if safety and safety.category == expected.get('safety_category'):
            return {"id": tc['id'], "pass": True, "reason": "Correctly blocked"}
        else:
            return {"id": tc['id'], "pass": False, "reason": f"Expected block for {expected.get('safety_category')}, got {safety}"}
    elif safety and safety.severity == "blocked":
        return {"id": tc['id'], "pass": False, "reason": "Falsely blocked"}

    # 2. Grounding
    verified_verses, corrections = await ground_message(input_text)
    
    if expected.get('correction_expected'):
        if not corrections:
            return {"id": tc['id'], "pass": False, "reason": "Expected a correction (hallucination prevention) but got none"}
    
    if expected.get('verse_verified'):
        found = any(v.reference == expected['verse_verified'] for v in verified_verses)
        if not found:
            return {"id": tc['id'], "pass": False, "reason": f"Expected to verify {expected['verse_verified']} but didn't find it"}

    # 3. LLM Response
    verified_dicts = [v.model_dump() for v in verified_verses]
    response = await generate_response(
        user_message=input_text,
        conversation_history=[],
        denomination=tc.get('denomination', 'nondenominational'),
        verified_verses=verified_dicts,
        semantic_verses=[],
        corrections=corrections
    )

    for phrase in expected.get('response_must_contain', []):
        if phrase.lower() not in response.lower():
            return {"id": tc['id'], "pass": False, "reason": f"Response missing expected phrase: {phrase}"}

    return {"id": tc['id'], "pass": True, "reason": "All assertions passed"}

async def main():
    with open('eval/test_cases.json', 'r') as f:
        data = json.load(f)
    
    results = []
    passed = 0
    total = len(data['test_cases'])
    
    print(f"Starting evaluation of {total} test cases...\n")
    for tc in data['test_cases']:
        if tc['category'] == 'image': 
            continue # skip image generation in unit tests
            
        res = await evaluate_test_case(tc)
        results.append(res)
        if res['pass']:
            passed += 1
            print(f"✅ {tc['id']} PASSED")
        else:
            print(f"❌ {tc['id']} FAILED: {res['reason']}")
            
        # To avoid hitting the 5 Requests Per Minute free-tier quota, wait 13 seconds
        await asyncio.sleep(13)
            
    print(f"\nEvaluation Complete: {passed}/{len(results)} passed.")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    asyncio.run(main())
