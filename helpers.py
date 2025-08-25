import logging
from homeassistant.core import HomeAssistant
from .const import SUPPORTED_DOMAINS

_LOGGER = logging.getLogger(__name__)

def validate_ai_response(response_data: dict) -> bool:
    """Validate the AI response against the expected schema."""
    try:
        # Basic structure validation
        if not isinstance(response_data, dict):
            _LOGGER.error("AI response is not a dictionary")
            return False
        
        if "reasoning" not in response_data:
            _LOGGER.error("Missing 'reasoning' field in AI response")
            return False
        
        if "commands" not in response_data:
            _LOGGER.error("Missing 'commands' field in AI response")
            return False
        
        # Validate commands structure
        if not isinstance(response_data["commands"], list):
            _LOGGER.error("'commands' field is not a list")
            return False
        
        for cmd in response_data["commands"]:
            if not isinstance(cmd, dict):
                _LOGGER.error("Command is not a dictionary")
                return False
            
            if "entity_id" not in cmd or "action" not in cmd:
                _LOGGER.error("Command missing required fields")
                return False
            
            # Additional validation for service_params
            if "service_params" in cmd and not isinstance(cmd["service_params"], dict):
                _LOGGER.error("service_params is not a dictionary")
                return False
        
        return True
        
    except Exception as e:
        _LOGGER.error("AI response validation error: %s", str(e))
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
YOU ARE A SMART HOME CONTROL SYSTEM. YOUR TASK IS TO RETURN A RESPONSE **EXCLUSIVELY IN JSON FORMAT** WITHOUT ANY ADDITIONAL COMMENTS, EXPLANATIONS, OR TEXT.

Input data:
- Sensor data: {sensor_data}
- Available devices: {actuator_entities}
- User command: {user_command}

You must return the response **STRICTLY** in the following JSON format:

{{
    "reasoning": "Brief explanation of the decision",
    "commands": [
        {{
            "entity_id": "light.kitchen",
            "action": "turn_on",
            "service_params": {{"brightness": 200}}
        }}
    ]
}}

CRITICAL RULES:
1. The response must be VALID JSON
2. DO NOT add any text outside the JSON structure
3. Use only devices from the list: {actuator_entities}
4. Support only the following action formats: {SUPPORTED_DOMAINS}
5. If the command is not possible, return an empty "commands" array and explain the reason in "reasoning"
6. Do not use markdown formatting (```json) - only pure JSON
"""