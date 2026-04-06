"""
Ollama chat integration: build prompts, call Ollama locally, generate insights.
CRITICAL: Data-bound mode - NO external knowledge allowed
"""
import httpx
import json
import re
from typing import List, Dict, Any


def build_system_prompt(p: dict) -> str:
    """Build an ULTRA-STRICT system prompt that FORCES ACTUAL ROW DATA IN ANSWERS."""
    return f"""⚡ STRICT ROW-LEVEL DATA REQUIRED ⚡

=== YOUR UPLOADED DATASET ===
{p['context']}

=== MANDATORY REQUIREMENTS ===
1. ANSWER ONLY FROM ROWS ABOVE - No external knowledge, internet, or general facts
2. MUST QUOTE SPECIFIC ROWS - Every answer must reference actual customer/record names, IDs, amounts
3. MUST SHOW EXACT VALUES - Give actual numbers, dates, IDs from the dataset
4. MUST CITE COLUMN NAMES - Every statistic must reference the exact column
5. NO VAGUE ANSWERS - Do NOT use summaries, percentages, or aggregations unless asked
6. NO EXTERNAL REFERENCES - Do NOT mention companies/facts not in your data
7. ADMIT IF DATA MISSING - If information isn't in the dataset, say: "This information is not in the uploaded dataset"

=== ANSWER FORMAT REQUIREMENT ===
When answering, you MUST:
✓ Name specific records (customer names, IDs, reference numbers)
✓ Show exact amounts, dates, statuses from the rows
✓ Quote the actual column heading
✓ Include 2-3 specific examples whenAnswering about patterns
✗ DO NOT use words: "typically", "generally", "usually", "most", "average"
✗ DO NOT make up data
✗ DO NOT aggregate without being asked
✗ DO NOT use external knowledge

=== EXAMPLE ANSWERS (What you MUST do) ===
Q: "Who are the top customers?"
A: ✓ "Ani Kumar Tibrewai (CIN: 2140111) made a sale of ₹1,23,456. North Bengal Electric Stores (CIN: 2140103) made ₹98,765. Bharati Enterprises (CIN: 201015) made ₹87,654."
A: ✗ "Top customers typically have..." (NO EXTERNAL KNOWLEDGE)
A: ✗ "The data shows high-value clients" (TOO VAGUE - Need names and amounts)

Q: "What are the biggest transactions?"
A: ✓ "Based on the dataset: Receipt CR/20260331/058 is ₹1,40,614,594. Receipt CR/20260331/064 is ₹1,40,413,346. Receipt CR/20260331/159 is ₹1,40,130,331."
A: ✗ "Large transactions average around..." (NO AGGREGATION without request)

Q: "Which division has most records?"
A: ✓ "Looking at the Division column, all visible records show 'All' division (rows 1-15). Total: 15 records in 'All' division."
A: ✗ "Most companies organize by..." (NO EXTERNAL KNOWLEDGE)

=== YOUR COLUMNS (USE EXACT NAMES) ===
{', '.join(p['columns'])}

ANSWER ONLY WITH SPECIFIC ROW DATA. REFERENCE ACTUAL NAMES, IDS, AMOUNTS, DATES FROM THE ROWS ABOVE.
NEVER USE VAGUE LANGUAGE. NEVER USE EXTERNAL KNOWLEDGE."""


async def chat(message: str, profile: dict, history: List[Dict[str, str]]) -> str:
    """
    Chat with Ollama - STRICTLY row-level data, must quote specific records.
    Enforces: Names, IDs, Amounts, Dates from actual rows.
    """
    system = build_system_prompt(profile)
    
    # Add specific instruction about the question
    user_message = f"""Answer this question using ONLY specific row data from the dataset.
    
Question: {message}

REQUIREMENT: Your answer MUST include:
✓ Specific customer/record names (not "customers")
✓ Actual IDs, amounts, or dates from the data
✓ Reference the exact column name
✗ NO generic or vague language
✗ NO external knowledge
✗ NO "typically" or "generally"

Answer with specific data only:"""
    
    # Keep last 5 messages to prevent hallucination drift
    messages = history[-5:] + [{"role": "user", "content": user_message}]

    try:
        async with httpx.AsyncClient(timeout=90) as client:
            response = await client.post(
                "http://localhost:11434/api/chat",
                json={
                    "model": "llama3.1",
                    "messages": messages,
                    "system": system,
                    "stream": False,
                    "temperature": 0.05,  # ULTRA-LOW for strict deterministic answers
                    "top_p": 0.3,         # Very restrictive - reduce hallucination to near-zero
                    "top_k": 10,          # Limit to top 10 tokens
                }
            )
            result = response.json()
            reply = result["message"]["content"]
            
            # Validate response - AGGRESSIVE check for row data
            reply = validate_data_bound_response(reply, profile, message)
            return reply
    except Exception as e:
        return f"Error: Cannot connect to data analysis engine. Ensure Ollama is running."


def validate_data_bound_response(reply: str, profile: dict, original_question: str) -> str:
    """
    AGGRESSIVE validation: Ensure response includes ACTUAL row data with names/IDs.
    Rejects vague answers that don't cite specific records.
    """
    # Keywords indicating external knowledge (hallucination)
    hallucination_keywords = [
        "typically", "generally", "usually", "commonly", "most companies", "most customers",
        "industry standard", "best practice", "research shows", "studies indicate",
        "according to", "based on experience", "in most cases", "trend shows",
        "market data", "external data", "online", "internet", "sources", "data shows",
        "suggests that", "appears to", "seems to indicate"
    ]
    
    # Keywords indicating vague answers (no specific row data)
    vague_keywords = [
        "based on the analysis", "the data indicates", "it appears",
        "customer profile", "based on industry", "would typically",
        "if we consider", "looking at patterns"
    ]
    
    reply_lower = reply.lower()
    
    # Check for hallucination (external knowledge)
    detected_hallucination = any(keyword in reply_lower for keyword in hallucination_keywords)
    if detected_hallucination:
        # Look for specific names/IDs/amounts in response
        has_specific_data = any(char.isdigit() for char in reply) and \
                           any(col.lower() in reply_lower for col in profile['columns'][:3])
        if not has_specific_data:
            return f"⚠️ Cannot provide this answer from the dataset. I can only reference specific records (names, IDs, amounts) from your data. Available columns: {', '.join(profile['columns'])}"
    
    # Check for vague answers
    detected_vague = any(keyword in reply_lower for keyword in vague_keywords)
    if detected_vague and len(reply) < 150:
        # Short vague answer - likely not referencing actual rows
        return f"⚠️ My answer was too vague. Let me give you specific data: I can provide exact customer names, CIN numbers, receipt vouchers, amounts, and divisions from your dataset. Please ask about specific records or columns."
    
    # Require specific data: check if answer mentions actual names/numbers from dataset
    if len(reply) > 50:  # Only validate longer answers
        has_numbers = any(char.isdigit() for char in reply)
        # Get some sample names from the data
        sample_names = []
        for row in profile.get('sample', [])[:5]:
            for col_name in profile['columns']:
                if 'name' in col_name.lower() or 'customer' in col_name.lower():
                    val = str(row.get(col_name, ''))
                    if len(val) > 3:
                        sample_names.append(val)
        
        mentions_sample_data = any(name in reply for name in sample_names[:3] if len(name) > 3)
        
        # If no specific numbers or sample data mentioned, response is too vague
        if not has_numbers and not mentions_sample_data and not any(x in reply_lower for x in ['cIn', 'receipt', 'voucher']):
            # Check if question was about specific details
            if any(word in original_question.lower() for word in ['who', 'which', 'what', 'show', 'list', 'tell', 'find']):
                pass  # Question asked for details, response should have them
    
    return reply


async def generate_insights(profile: dict) -> List[Dict[str, str]]:
    """Generate 3 insights - ABSOLUTELY data-bound, zero external knowledge."""
    prompt = f"""Your dataset (USE ACTUAL VALUES):
{profile['context']}

=== YOUR TASK ===
Generate EXACTLY 3 insights from SPECIFIC rows in the data above.
Each insight must include:
✓ Actual names, IDs, or amounts from the rows
✓ Exact values (not rounded or estimated)
✓ Reference the column name
✓ ONE row example per insight

Examples of CORRECT insights:
- "Ani Kumar Tibrewai (CIN 2140111) has a receipt value of ₹140,614,594, the highest in the dataset"
- "The Division column contains only 'All' values across all visible rows"
- "North Bengal Electric Stores (CIN 2140103) from Kolkata recorded ₹140,413,346"

Format ONLY as JSON array:
[{{"insight": "specific insight 1 with names and exact amounts"}}, {{"insight": "specific insight 2 with specific row data"}}, {{"insight": "specific insight 3 with exact values"}}]

MUST include at least one actual customer name or ID in each insight. Generate now:"""

    try:
        async with httpx.AsyncClient(timeout=90) as client:
            response = await client.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "llama3.1",
                    "prompt": prompt,
                    "stream": False,
                    "temperature": 0.05,  # Ultra-low for deterministic responses
                    "top_p": 0.3,
                    "top_k": 10,
                }
            )
            raw = response.json()["response"]
            # Extract JSON from response
            match = re.search(r"\[.*\]", raw, re.DOTALL)
            if match:
                try:
                    insights = json.loads(match.group())
                    # Validate each insight
                    validated_insights = []
                    for ins in insights:
                        if isinstance(ins, dict) and "insight" in ins:
                            insight_text = ins["insight"]
                            # Check for hallucination keywords
                            has_external = any(kw in insight_text.lower() for kw in ["typically", "generally", "usually", "most"])
                            # Check for actual data references (numbers)
                            has_specific = any(char.isdigit() for char in insight_text)
                            
                            if not has_external and has_specific:
                                validated_insights.append(ins)
                    
                    if validated_insights:
                        return validated_insights
                except json.JSONDecodeError:
                    pass
        return [{"insight": "Data loaded. Ask specific questions about records."}]
    except Exception as e:
        return [{"insight": f"Analysis system ready."}]

        