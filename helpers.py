import logging
import voluptuous as vol
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from .const import SUPPORTED_DOMAINS

_LOGGER = logging.getLogger(__name__)

def validate_ai_response(response_data: dict) -> bool:
    """Validate the AI response against the expected schema."""
    try:
        # Базовая проверка структуры
        if not isinstance(response_data, dict):
            _LOGGER.error("Ответ AI не является словарем")
            return False
        
        if "reasoning" not in response_data:
            _LOGGER.error("Отсутствует поле 'reasoning' в ответе AI")
            return False
        
        if "commands" not in response_data:
            _LOGGER.error("Отсутствует поле 'commands' в ответе AI")
            return False
        
        # Проверка структуры команд
        if not isinstance(response_data["commands"], list):
            _LOGGER.error("Поле 'commands' не является списком")
            return False
        
        for cmd in response_data["commands"]:
            if not isinstance(cmd, dict):
                _LOGGER.error("Команда не является словарем")
                return False
            
            if "entity_id" not in cmd or "action" not in cmd:
                _LOGGER.error("Команда отсутствует обязательные поля")
                return False
            
            # Дополнительная проверка service_params
            if "service_params" in cmd and not isinstance(cmd["service_params"], dict):
                _LOGGER.error("service_params не является словарем")
                return False
        
        return True
        
    except Exception as e:
        _LOGGER.error("Ошибка валидации ответа AI: %s", str(e))
        return False

def validate_entity_domain(entity_id: str, action: str) -> bool:
    """Validate if the action is supported for the entity domain."""
    domain = entity_id.split(".")[0]
    
    if domain not in SUPPORTED_DOMAINS:
        _LOGGER.error("Domain %s is not supported", domain)
        return False
    
    if action not in SUPPORTED_DOMAINS[domain]:
        _LOGGER.error("Action %s is not supported for domain %s", action, domain)
        return False
    
    return True

async def get_entity_states(hass: HomeAssistant, entity_ids: list) -> dict:
    """Get current states for multiple entities."""
    states = {}
    for entity_id in entity_ids:
        state = hass.states.get(entity_id)
        if state:
            states[entity_id] = {
                "state": state.state,
                "attributes": dict(state.attributes)
            }
        else:
            _LOGGER.warning("Entity %s not found", entity_id)
    return states

def generate_ai_prompt(sensor_data: dict, actuator_entities: list, user_command: str) -> str:
    """Generate the prompt for the AI."""
    return f"""
ТЫ — СИСТЕМА УПРАВЛЕНИЯ УМНЫМ ДОМОМ. ТВОЯ ЗАДАЧА — ВЕРНУТЬ ОТВЕТ **ИСКЛЮЧИТЕЛЬНО В ФОРМАТЕ JSON** БЕЗ КАКИХ-ЛИБО ДОПОЛНИТЕЛЬНЫХ КОММЕНТАРИЕВ, ОБЪЯСНЕНИЙ ИЛИ ТЕКСТА.

Входные данные:
- Данные сенсоров: {sensor_data}
- Доступные устройства: {actuator_entities}
- Задача пользователя: {user_command}

Ты должен вернуть ответ **СТРОГО** в следующем формате JSON:

{{
    "reasoning": "Краткое объяснение решения",
    "commands": [
        {{
            "entity_id": "light.kitchen",
            "action": "turn_on",
            "service_params": {{"brightness": 200}}
        }}
    ]
}}

КРИТИЧЕСКИ ВАЖНЫЕ ПРАВИЛА:
1. Ответ должен быть ВАЛИДНЫМ JSON
2. НЕ добавляй никакой текст вне JSON-структуры
3. Используй только устройства из списка: {actuator_entities}
4. Поддерживай только следующие форматы действий: {SUPPORTED_DOMAINS}
5. Если команда невозможна, верни пустой массив "commands" и объясни причину в "reasoning"
6. Не используй markdown-форматирование (```json) - только чистый JSON
"""