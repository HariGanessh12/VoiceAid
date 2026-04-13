import json
import logging
from openai import AsyncOpenAI
from app.config import settings

logger = logging.getLogger(__name__)

client = AsyncOpenAI(api_key=settings.openai_api_key)

async def generate_embeddings(text: str) -> list[float]:
    if not settings.openai_api_key:
        logger.warning("No OpenAI API key set. Returning dummy embeddings.")
        return [0.0] * 1536
        
    try:
        response = await client.embeddings.create(input=text, model="text-embedding-3-small")
        return response.data[0].embedding
    except Exception as e:
        logger.error(f"Error generating embeddings: {e}")
        return [0.0] * 1536

async def generate_conversational_response(transcript: str) -> str:
    """Fast, stateless text generation for synchronous voice interactions."""
    if not settings.openai_api_key:
        return "I received your message, but my AI is currently disconnected."
        
    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are VoiceAid, a helpful AI legal assistant. Respond conversationally, concisely, and naturally for a voice call."},
                {"role": "user", "content": transcript}
            ],
            max_tokens=150,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Error in conversational AI: {e}")
        return "I'm sorry, I'm having trouble processing that right now."

async def process_legal_issue(transcript: str, past_context: str) -> tuple[str, str, str]:
    if not settings.openai_api_key:
        logger.warning("No OpenAI API key set. Returning mock analysis.")
        return ("Mock Structured Issue", "This is a mock formal legal complaint text.", "Contact a lawyer.")

    system_prompt = (
        "You are VoiceAid, an expert AI legal assistant. Respond exclusively in JSON format. "
        "Handle multilingual input by translating and processing internally, but feel free to draft the 'complaint' in the user's original language. "
        "Convert user speech into:\n"
        "1. Legal issue type\n"
        "2. Key facts\n"
        "3. Suggested action\n"
        "4. Draft complaint (simple language)\n\n"
        "Be concise and practical. Your output MUST be valid JSON matching this schema:\n"
        "{\n"
        '  "issue": "...",\n'
        '  "facts": ["...", "..."],\n'
        '  "action": "...",\n'
        '  "complaint": "..."\n'
        "}"
    )
    
    user_prompt = f"Transcript:\n{transcript}\n\n"
    if past_context:
        user_prompt += f"Relevant Past Cases/Context:\n{past_context}\n\n"

    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={ "type": "json_object" },
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.0  # Deterministic output
        )
        
        result_text = response.choices[0].message.content
        
        # Robust parsing
        try:
            parsed = json.loads(result_text)
            issue = parsed.get("issue", "Unknown Issue")
            facts = parsed.get("facts", [])
            action = parsed.get("action", "")
            complaint = parsed.get("complaint", "Error drafting complaint.")
            
            # Combine issue and facts for the semantic memory "structured_issue" string
            facts_str = "; ".join(facts) if isinstance(facts, list) else str(facts)
            structured_summary = f"Issue: {issue} | Facts: {facts_str} | Action: {action}"
            
            
            return structured_summary, complaint, action
            
        except json.JSONDecodeError as decode_err:
            logger.error(f"Failed to parse JSON from LLM. Error: {decode_err} Output: {result_text}")
            return "Parsing error: Valid JSON not returned.", "Sorry, we encountered an error drafting your complaint.", "I'm having trouble providing an action step."

    except Exception as e:
        logger.error(f"Error in LLM service: {e}")
        return "Error analyzing case.", "Error generating complaint.", "We apologize, but an internal service error occurred."
