# ha-deepseek-control
A custom Home Assistant integration that enables natural language control of smart home devices via DeepSeek AI models through the OpenRouter API. Supports lights, switches, climate devices, covers, and media players.
Atention.
The following API request limits apply to the free OpenRouter.ai plan:

🕒 20 requests per minute for free models (with an ID ending in :free)1.

📅 Daily limits:

Up to 50 requests per day if the account has purchased less than 10 credits.

Up to 1000 requests per day if the account has purchased 10 or more credits1.

These limits apply to free models only. Paid models have separate limits depending on the plan and account balance. To check the current status of limits and credits, you can use a GET request to https:
