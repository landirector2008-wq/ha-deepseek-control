import aiofiles
import aiohttp
import json
import logging
import re
from json import JSONDecodeError
from datetime import datetime
from homeassistant.core import HomeAssistant
from .helpers import validate_ai_response

_LOGGER = logging.getLogger(__name__)

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

def extract_json_from_response(response_text: str) -> dict:
    """
    Extract JSON from response text, even if surrounded by additional text.
    """
    # Remove markdown code formatting (if present)
    cleaned_text = re.sub(r'```json|```', '', response_text).strip()
    
    # Try to find JSON object using regex
    json_match = re.search(r'\{[\s\S]*\}', cleaned_text)
    if json_match:
        json_str = json_match.group()
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            # Log error for debugging
            _LOGGER.debug("JSON decode error: %s. Text: %s", str(e), json_str)
    
    # If object not found, try to find JSON array
    json_match = re.search(r'\[[\s\S]*\]', cleaned_text)
    if json_match:
        json_str = json_match.group()
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            _LOGGER.debug("JSON array decode error: %s. Text: %s", str(e), json_str)
    
    # Return None if nothing found
    return None

async def send_to_deepseek(
    hass: HomeAssistant,
    api_key: str, 
    prompt: str, 
    model: str, 
    max_tokens: int, 
    temperature: float
) -> dict:
    """Send a prompt to DeepSeek via OpenRouter and return the parsed JSON response."""

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://www.home-assistant.io",
        "X-Title": "Home Assistant DeepSeek Integration"
    }

    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "You are a home automation system that responds ONLY with valid RFC8259 compliant JSON without any additional text, explanations, or comments. Your responses must be parseable by JSON.parse() without errors."
            },
            {
                "role": "user", 
                "content": prompt
            }
        ],
        "max_tokens": max_tokens,
        "temperature": temperature
    }

    # Add response_format for models that support JSON mode
    if "gpt-4" in model or "gpt-3.5" in model or "json" in model.lower():
        payload["response_format"] = {"type": "json_object"}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                OPENROUTER_API_URL, 
                headers=headers, 
                json=payload, 
                timeout=30
            ) as response:
                response.raise_for_status()
                data = await response.json()

                # Extract response text
                reply_content = data["choices"][0]["message"]["content"]
                
                # Detailed logging for debugging
                _LOGGER.debug("Full response from AI: %s", reply_content)
                
                # Asynchronous logging to file
                try:
                    log_entry = f"\n--- {datetime.now().isoformat()} ---\nPrompt: {prompt[:200]}...\nResponse: {reply_content}\n--- END ---\n"
                    async with aiofiles.open("/config/deepseek_raw_responses.log", "a") as f:
                        await f.write(log_entry)
                except Exception as log_error:
                    _LOGGER.error("Error writing to log file: %s", str(log_error))

                # Try to extract JSON from response
                ai_response = extract_json_from_response(reply_content)
                
                if ai_response is not None:
                    # Validate response
                    if validate_ai_response(ai_response):
                        return ai_response
                    else:
                        _LOGGER.error("AI response validation failed. Raw response: %s", reply_content)
                        return None
                else:
                    _LOGGER.error("JSON not found in AI response. Full response: %s", reply_content)
                    return None

    except (aiohttp.ClientError, JSONDecodeError, KeyError) as e:
        _LOGGER.error("OpenRouter communication error: %s", str(e))
        return None