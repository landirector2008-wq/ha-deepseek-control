DOMAIN = "deepseek_control"
DEFAULT_NAME = "DeepSeek Smart Controller"

CONF_API_KEY = "api_key"
CONF_SENSORS = "sensors"
CONF_ACTUATORS = "actuators"
CONF_MAX_TOKENS = "max_tokens"
CONF_TEMPERATURE = "temperature"
CONF_MODEL = "model"

DEFAULT_MAX_TOKENS = 500
DEFAULT_TEMPERATURE = 0.7
DEFAULT_MODEL = "deepseek/deepseek-chat"

# Поддерживаемые домены для действий
SUPPORTED_DOMAINS = {
    "light": ["turn_on", "turn_off", "toggle"],
    "switch": ["turn_on", "turn_off", "toggle"],
    "climate": ["set_temperature", "set_hvac_mode", "set_fan_mode"],
    "cover": ["open_cover", "close_cover", "set_cover_position"],
    "media_player": ["play_media", "volume_set", "media_play", "media_pause"]
}