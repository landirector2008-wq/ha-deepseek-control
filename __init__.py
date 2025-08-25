import logging
import voluptuous as vol
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers import config_validation as cv
from .const import DOMAIN, CONF_API_KEY, CONF_SENSORS, CONF_ACTUATORS

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the integration from YAML."""
    hass.data.setdefault(DOMAIN, {})
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up from a config entry."""
    # Store config entry
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.data

    # Register services
    await _register_services(hass, entry)

    return True

async def _register_services(hass: HomeAssistant, entry: ConfigEntry):
    """Register custom services."""

    async def handle_send_command(call: ServiceCall):
        """Handle the service call to send a command to DeepSeek."""
        from .deepseek_logic import send_to_deepseek
        from .helpers import get_entity_states, validate_entity_domain, generate_ai_prompt

        # Check for required parameter
        if "command" not in call.data or not call.data["command"]:
            _LOGGER.error("Missing required parameter 'command'")
            return
            
        command_text = call.data["command"]
        if not isinstance(command_text, str) or not command_text.strip():
            _LOGGER.error("Parameter 'command' must be a non-empty string")
            return
            
        _LOGGER.debug("Received command: %s", command_text)
        
        # Get configuration
        config = entry.data
        
        # Check for required configuration parameters
        required_params = [CONF_API_KEY, CONF_SENSORS, CONF_ACTUATORS]
        for param in required_params:
            if param not in config or not config[param]:
                _LOGGER.error("Missing required configuration parameter: %s", param)
                return
        
        api_key = config[CONF_API_KEY]
        sensor_entities = config[CONF_SENSORS]
        actuator_entities = config[CONF_ACTUATORS]
        model = config.get("model", "deepseek/deepseek-chat")
        max_tokens = config.get("max_tokens", 500)
        temperature = config.get("temperature", 0.7)

        # Get states of all sensors
        sensor_data = await get_entity_states(hass, sensor_entities)

        # Generate AI prompt
        ai_prompt = generate_ai_prompt(sensor_data, actuator_entities, command_text)
        _LOGGER.debug("Generated AI prompt: %s", ai_prompt)

        # Send request to OpenRouter API
        result = await send_to_deepseek(hass, api_key, ai_prompt, model, max_tokens, temperature)
        
        if not result:
            _LOGGER.error("Failed to get valid response from AI")
            return

        # Execute commands returned by AI
        if "commands" in result:
            _LOGGER.info("AI reasoning: %s", result.get("reasoning", "No reasoning provided"))
            
            successful_commands = 0
            for cmd in result["commands"]:
                entity_id = cmd["entity_id"]
                action = cmd["action"]
                service_params = cmd.get("service_params", {})
                
                # Check if action is supported for this entity
                if not validate_entity_domain(entity_id, action):
                    _LOGGER.error("Skipping invalid command for entity %s: %s", entity_id, action)
                    continue
                
                # Call Home Assistant service
                domain = entity_id.split(".")[0]
                service_data = {"entity_id": entity_id, **service_params}

                _LOGGER.info("Calling service: %s.%s with data: %s", domain, action, service_data)
                
                try:
                    await hass.services.async_call(
                        domain, 
                        action, 
                        service_data, 
                        blocking=True
                    )
                    successful_commands += 1
                except Exception as e:
                    _LOGGER.error("Error calling service %s.%s: %s", domain, action, str(e))
            
            _LOGGER.info("Successfully executed %d out of %d commands", 
                        successful_commands, len(result["commands"]))

    # Register service
    hass.services.async_register(
        DOMAIN, 
        "send_command", 
        handle_send_command, 
        schema=vol.Schema({
            vol.Required("command"): cv.string,
        })
    )

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    # Remove service when integration is unloaded
    if hass.services.has_service(DOMAIN, "send_command"):
        hass.services.async_remove(DOMAIN, "send_command")
    
    if DOMAIN in hass.data:
        hass.data[DOMAIN].pop(entry.entry_id)
        
    return True