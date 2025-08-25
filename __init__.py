import asyncio
import logging
import aiohttp
import re
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_time_interval

_LOGGER = logging.getLogger(__name__)

# Custom exceptions for better error handling
class OpenRouterAIError(Exception):
    """Base exception for OpenRouter AI errors."""
    pass

class RateLimitExceededError(OpenRouterAIError):
    """Exception for rate limit exceeded errors (429)."""
    pass

class OpenRouterAIAutomation:
    def __init__(self, hass, api_key, update_interval):
        self.hass = hass
        self.api_key = api_key
        self.update_interval = update_interval
        self._unsub_interval = None
        self._rate_limited = False  # Flag to track rate limit status
        self._retry_delay = 60  # Initial retry delay in seconds
        self._max_retry_delay = 3600  # Maximum retry delay (1 hour)

    async def async_start(self):
        """Start the periodic update interval."""
        self._unsub_interval = async_track_time_interval(
            self.hass, self._async_update, self.update_interval
        )

    async def _async_update(self, now=None):
        """Periodic update method with rate limit handling."""
        if self._rate_limited:
            _LOGGER.warning("Skipping update due to active rate limiting")
            return

        try:
            await self._execute_ai_rules()
        except RateLimitExceededError as e:
            await self._handle_rate_limit(e)
        except aiohttp.ClientError as e:
            _LOGGER.error("Network error communicating with OpenRouter: %s", e)
        except Exception as e:
            _LOGGER.error("Unexpected error during AI rule execution: %s", e)

    async def _execute_ai_rules(self):
        """Execute AI rules with proper API error handling."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "meta-llama/llama-3-70b-instruct:free",  # Default free model
            "messages": [
                {"role": "system", "content": "You are a home automation assistant..."},
                {"role": "user", "content": "Your prompt here..."}
            ],
            "temperature": 0.7
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=30
                ) as response:
                    # Handle rate limiting (429 error)
                    if response.status == 429:
                        error_data = await response.json()
                        retry_after = response.headers.get('Retry-After')
                        
                        raise RateLimitExceededError(
                            f"Rate limit exceeded. Retry-After: {retry_after}. "
                            f"Error details: {error_data}"
                        )
                    
                    # Raise for other HTTP errors
                    response.raise_for_status()
                    result = await response.json()
                    
                    # Process successful response
                    await self._process_ai_response(result)
                    
        except aiohttp.ClientResponseError as e:
            if e.status == 429:
                raise RateLimitExceededError(f"Rate limit exceeded: {e}") from e
            raise

    async def _handle_rate_limit(self, error):
        """Handle rate limit exceeded error with exponential backoff."""
        self._rate_limited = True
        
        # Extract retry time from error message if available
        retry_after = self._extract_retry_after(str(error))
        
        if retry_after:
            wait_time = retry_after
            _LOGGER.warning(
                "OpenRouter rate limit exceeded. Waiting for %s seconds as suggested by server",
                wait_time
            )
        else:
            # Apply exponential backoff strategy
            wait_time = self._retry_delay
            self._retry_delay = min(self._retry_delay * 2, self._max_retry_delay)
            _LOGGER.warning(
                "OpenRouter rate limit exceeded. Using exponential backoff: waiting %s seconds",
                wait_time
            )

        # Create notification for user
        await self._create_rate_limit_notification(wait_time)

        # Schedule recovery after wait period
        self.hass.loop.call_later(
            wait_time,
            lambda: self.hass.async_create_task(self._reset_rate_limit())
        )

    def _extract_retry_after(self, error_message):
        """Extract Retry-After time from error message."""
        match = re.search(r'Retry-After: (\d+)', error_message)
        if match:
            return int(match.group(1))
        return None

    async def _reset_rate_limit(self):
        """Reset rate limit status after waiting period."""
        self._rate_limited = False
        _LOGGER.info("Rate limit period ended. Resuming normal operation")
        
        # Notify user that service has resumed
        await self.hass.services.async_call(
            'persistent_notification',
            'create',
            {
                'title': 'OpenRouter Rate Limit Ended',
                'message': 'Rate limit period has ended. AI automation has resumed normal operation.'
            }
        )

    async def _create_rate_limit_notification(self, wait_time):
        """Create a persistent notification about rate limiting."""
        wait_time_minutes = wait_time // 60
        message = (
            f"OpenRouter API rate limit exceeded. "
            f"AI automation will resume in approximately {wait_time_minutes} minutes. "
            f"Free tier limits: 20 requests/minute, 50 requests/day (if <10 credits), "
            f"1000 requests/day (if ≥10 credits). "
            f"Consider upgrading at https://openrouter.ai/account"
        )

        await self.hass.services.async_call(
            'persistent_notification',
            'create',
            {
                'title': 'OpenRouter Rate Limit Exceeded',
                'message': message,
                'notification_id': 'openrouter_rate_limit'
            }
        )

    async def _process_ai_response(self, result):
        """Process successful AI response."""
        # Implementation for processing AI response
        pass

    async def get_rate_limit_status(self):
        """Check current rate limit status from OpenRouter."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://openrouter.ai/api/v1/key",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=10
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        await self._update_limit_sensors(data)
                        return data
                    else:
                        _LOGGER.warning("Failed to get rate limit status: %s", response.status)
        except Exception as e:
            _LOGGER.error("Error checking rate limit status: %s", e)

    async def _update_limit_sensors(self, status_data):
        """Update sensors with rate limit information."""
        # Implementation for updating sensors with rate limit data
        pass