import aiohttp
import json
import logging
import re
from json import JSONDecodeError
from datetime import datetime
from .helpers import validate_ai_response

_LOGGER = logging.getLogger(__name__)

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

def extract_json_from_response(response_text: str) -> dict:
    """
    Извлекает JSON из текста ответа, даже если он окружен дополнительным текстом.
    """
    # Удаляем markdown-обрамление кода (если есть)
    cleaned_text = re.sub(r'```json|```', '', response_text).strip()
    
    # Попытка найти JSON-объект с помощью регулярного выражения
    json_match = re.search(r'\{[\s\S]*\}', cleaned_text)
    if json_match:
        json_str = json_match.group()
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            # Логируем ошибку для отладки
            _LOGGER.debug("JSON decode error: %s. Text: %s", str(e), json_str)
    
    # Если не найден объект, попробуем найти JSON-массив
    json_match = re.search(r'\[[\s\S]*\]', cleaned_text)
    if json_match:
        json_str = json_match.group()
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            _LOGGER.debug("JSON array decode error: %s. Text: %s", str(e), json_str)
    
    # Если ничего не найдено, вернем None
    return None

async def send_to_deepseek(
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

    # Добавляем response_format для моделей, которые поддерживают JSON mode
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

                # Извлекаем текст ответа
                reply_content = data["choices"][0]["message"]["content"]
                
                # Детальное логирование для отладки
                _LOGGER.debug("Полный ответ от нейросети: %s", reply_content)
                _LOGGER.info("Первые 500 символов ответа: %s", 
                            reply_content[:500] + ("..." if len(reply_content) > 500 else ""))
                
                # Сохраняем сырой ответ в файл для дальнейшего анализа
                try:
                    with open("/config/deepseek_raw_responses.log", "a") as f:
                        f.write(f"\n--- {datetime.now().isoformat()} ---\n")
                        f.write(f"Prompt: {prompt[:200]}...\n")
                        f.write(f"Response: {reply_content}\n")
                        f.write("--- END ---\n")
                except Exception as log_error:
                    _LOGGER.error("Ошибка при записи в лог-файл: %s", str(log_error))

                # Пытаемся извлечь JSON из ответа
                ai_response = extract_json_from_response(reply_content)
                
                if ai_response is not None:
                    # Валидируем ответ
                    if validate_ai_response(ai_response):
                        return ai_response
                    else:
                        _LOGGER.error("Валидация ответа AI не удалась. Сырой ответ: %s", reply_content)
                        return None
                else:
                    _LOGGER.error("JSON не найден в ответе AI. Полный ответ: %s", reply_content)
                    return None

    except (aiohttp.ClientError, JSONDecodeError, KeyError) as e:
        _LOGGER.error("Ошибка связи с OpenRouter: %s", str(e))
        return None