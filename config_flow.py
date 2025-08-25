from homeassistant import config_entries
from homeassistant.core import callback
from .const import (
    DOMAIN, CONF_API_KEY, CONF_SENSORS, CONF_ACTUATORS,
    CONF_MAX_TOKENS, CONF_TEMPERATURE, CONF_MODEL,
    DEFAULT_MAX_TOKENS, DEFAULT_TEMPERATURE, DEFAULT_MODEL
)

class DeepSeekControlConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for DeepSeek Control."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        # Отложенный импорт для избежания блокировки
        import voluptuous as vol
        from homeassistant.helpers import selector

        errors = {}

        if user_input is not None:
            # Валидация API ключа
            if not user_input[CONF_API_KEY].startswith("sk-"):
                errors[CONF_API_KEY] = "invalid_api_key_format"
            else:
                # Сохраняем конфигурацию
                return self.async_create_entry(
                    title="DeepSeek Control",
                    data=user_input
                )

        # Схема формы с использованием селекторов
        data_schema = vol.Schema({
            vol.Required(CONF_API_KEY): str,
            vol.Required(CONF_SENSORS): selector.EntitySelector(
                selector.EntitySelectorConfig(
                    domain=["sensor", "binary_sensor", "climate"],
                    multiple=True
                )
            ),
            vol.Required(CONF_ACTUATORS): selector.EntitySelector(
                selector.EntitySelectorConfig(
                    domain=["light", "switch", "climate", "cover", "media_player"],
                    multiple=True
                )
            ),
            vol.Optional(CONF_MODEL, default=DEFAULT_MODEL): str,
            vol.Optional(CONF_MAX_TOKENS, default=DEFAULT_MAX_TOKENS): vol.All(
                vol.Coerce(int), vol.Range(min=1, max=1000)
            ),
            vol.Optional(CONF_TEMPERATURE, default=DEFAULT_TEMPERATURE): vol.All(
                vol.Coerce(float), vol.Range(min=0.0, max=1.0)
            )
        })

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return DeepSeekControlOptionsFlow(config_entry)

class DeepSeekControlOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for DeepSeek Control."""

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        # Отложенный импорт для избежания блокировки
        import voluptuous as vol
        from homeassistant.helpers import selector

        errors = {}

        # Используем self._config_entry вместо self.config_entry
        config_entry = self._config_entry

        if user_input is not None:
            # Валидация
            if not user_input[CONF_API_KEY].startswith("sk-"):
                errors[CONF_API_KEY] = "invalid_api_key_format"
            else:
                # Обновляем конфигурацию
                return self.async_create_entry(title="", data=user_input)

        # Заполняем форму текущими значениями
        options_schema = vol.Schema({
            vol.Required(
                CONF_API_KEY,
                default=config_entry.options.get(CONF_API_KEY, config_entry.data.get(CONF_API_KEY))
            ): str,
            vol.Required(
                CONF_SENSORS,
                default=config_entry.options.get(CONF_SENSORS, config_entry.data.get(CONF_SENSORS))
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(
                    domain=["sensor", "binary_sensor", "climate"],
                    multiple=True
                )
            ),
            vol.Required(
                CONF_ACTUATORS,
                default=config_entry.options.get(CONF_ACTUATORS, config_entry.data.get(CONF_ACTUATORS))
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(
                    domain=["light", "switch", "climate", "cover", "media_player"],
                    multiple=True
                )
            ),
            vol.Optional(
                CONF_MODEL,
                default=config_entry.options.get(CONF_MODEL, config_entry.data.get(CONF_MODEL, DEFAULT_MODEL))
            ): str,
            vol.Optional(
                CONF_MAX_TOKENS,
                default=config_entry.options.get(CONF_MAX_TOKENS, config_entry.data.get(CONF_MAX_TOKENS, DEFAULT_MAX_TOKENS))
            ): vol.All(vol.Coerce(int), vol.Range(min=1, max=1000)),
            vol.Optional(
                CONF_TEMPERATURE,
                default=config_entry.options.get(CONF_TEMPERATURE, config_entry.data.get(CONF_TEMPERATURE, DEFAULT_TEMPERATURE))
            ): vol.All(vol.Coerce(float), vol.Range(min=0.0, max=1.0))
        })

        return self.async_show_form(
            step_id="init", data_schema=options_schema, errors=errors
        )