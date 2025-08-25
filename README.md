# Home Assistant AI Automation Integrator

🤖 **Natural Language Controlled Home Automation via OpenRouter.ai API**

This integration allows you to control your Home Assistant entities using natural language commands processed by large language models through OpenRouter.ai's unified API. Define your sensors and actuators in the configuration wizard, describe what you want to happen in plain language, and let AI handle the logic!

## ✨ Features

- **Natural Language Automation**: Describe behaviors using simple English phrases
- **Multi-LLM Support**: Access various AI models through OpenRouter's unified API
- **Flexible Triggering**: Time-based periodic execution or event-based triggering
- **Secure Configuration**: API key management through OpenRouter's platform
- **Free Tier Friendly**: Works with OpenRouter's free models with clear rate limit indicators
- **Smart Rate Limit Handling**: Automatic pause and recovery when API limits are exceeded

## 🚀 Getting Started

### Prerequisites

- Home Assistant installation (version 2023.0 or newer)
- OpenRouter.ai account ([sign up here](https://openrouter.ai))
- Network connectivity from your Home Assistant instance to OpenRouter API

### Installation

1. **Download the integration**:
   - Option 1: Install via HACS (recommended)
   - Option 2: Manual installation by copying files to your `custom_components` directory

2. **Restart Home Assistant** after installation

3. **Configure OpenRouter API Key**:
   - Visit [OpenRouter Keys](https://openrouter.ai/keys) to create your API key 
   - Click "Create Key" and name it (e.g., "Home Assistant Integration")
   - ⚠️ **Copy and save your key immediately** - you won't be able to see it again! 
   - Consider setting a credit limit if sharing this key 

4. **Add Integration in Home Assistant**:
   - Navigate to Settings → Devices & Services → Add Integration
   - Search for "AI Automation Integrator"
   - Enter your OpenRouter API key when prompted
   - Follow the configuration wizard to select sensors and actuators

## ⚙️ Configuration

### OpenRouter API Setup

The integration uses OpenRouter's API which provides:
- Unified access to multiple LLM providers (Anthropic, OpenAI, Google, Meta, etc.) 
- Transparent pricing (no markup on model costs) 
- Flexible authentication using Bearer tokens 

### Rate Limits and Quotas

**Important**: Be aware of OpenRouter's rate limits: 

- **Free models** (with IDs ending in `:free`):
  - 20 requests per minute
  - Daily limits:
    - 50 requests/day if account has purchased <10 credits
    - 1,000 requests/day if account has ≥10 credits 

- **Paid models**: Have separate limits based on your account balance

Check your current limits and credit status:
```bash
curl -H "Authorization: Bearer YOUR_OPENROUTER_API_KEY" \
  "https://openrouter.ai/api/v1/key"
```

### Integration Settings

In the configuration wizard, you'll:

1. **Select input sensors** (temperature, motion, light sensors, etc.)
2. **Choose output devices** (switches, automations, scripts, etc.)
3. **Define natural language rules** describing behaviors
4. **Set execution frequency** (how often the AI evaluates conditions)

Example natural language rule:
> "If it's after sunset and the living room motion sensor detects movement for more than 5 minutes, turn on the hallway light and set it to 30% brightness."

## 💡 Usage Examples

### Basic Automation
```yaml
# Example configuration.yaml entry
ai_automator:
  api_key: !secret openrouter_api_key
  update_interval: 300  # Check every 5 minutes
  rules:
    - name: "Evening Lighting"
      sensors:
        - sensor.outside_light_level
        - binary_sensor.living_room_motion
      actuators:
        - light.hallway
        - switch.entryway_lamp
      prompt: >
        When outside light level is below 50 lux and it's after 6 PM,
        and motion is detected in the living room, turn on the hallway
        light to 70% and switch on the entryway lamp.
```

### Advanced Configuration
```yaml
ai_automator:
  api_key: !secret openrouter_api_key
  model: "meta-llama/llama-3.1-70b-instruct:free"  # Free model 
  # model: "anthropic/claude-2.1"  # Paid model option
  temperature: 0.7  # Control creativity vs. predictability 
  max_tokens: 500   # Limit response length
  update_interval: 60  # Check every minute
  rules: []
```

## 📊 Monitoring and Troubleshooting

### Viewing API Usage
- Monitor your OpenRouter usage in the [Activity tab](https://openrouter.ai/activity) 
- Check the integration's log for execution details
- Home Assistant's logbook will show AI-triggered actions

### Rate Limit Handling

This integration automatically handles OpenRouter's rate limits:

1. **Automatic Pause**: When rate limits are exceeded, the integration pauses automatically
2. **Smart Retry**: Uses exponential backoff or server-suggested wait times
3. **Notifications**: Creates persistent notifications in Home Assistant
4. **Self-Recovery**: Automatically resumes operation after rate limit periods

### Common Issues

1. **Rate limiting errors**:
   - Reduce update frequency if using free models
   - Consider upgrading to paid OpenRouter credits 

2. **API key errors**:
   - Verify your key at [OpenRouter Keys](https://openrouter.ai/keys)
   - Regenerate if compromised 

3. **Unexpected behaviors**:
   - Refine your natural language prompts
   - Adjust temperature setting for more/less predictable responses 

## 🔒 Privacy and Security

- OpenRouter has a **zero-logging default** for prompts/completions 
- You can opt-in to logging for a 1% discount on usage costs 
- API keys should be stored securely using Home Assistant's secrets feature
- The integration only sends necessary sensor data to OpenRouter

## 💰 Cost Management

### Free Usage
- OpenRouter offers several free models (look for `:free` suffix) 
- Free models have limited capabilities and stricter rate limits 
- Perfect for testing and low-volume applications

### Paid Options
- Add credits to your OpenRouter account for access to premium models 
- OpenRouter passes through provider pricing without markup 
- Set credit limits on your API keys to control spending 

## ❤️ Supporting This Project

If you find this integration useful and would like to support its continued development, consider making a contribution:

- **Bitcoin**: bc1qfekxxztsl4ega778v2y9pe5ftrstdswsedrjw2
- **Ethereum**: 0xc076819D30D2277d067dE434CCCFD90BeE1A667c

Your support helps maintain and improve this integration for the entire Home Assistant community!

## 🛠 Development

This integration uses OpenRouter's API which is compatible with OpenAI's API format:
```python
# Example request format 
headers = {
  "Authorization": f"Bearer {api_key}",
  "HTTP-Referer": "https://home-assistant.io",  # Optional
  "X-Title": "Home Assistant AI Integration",   # Optional
  "Content-Type": "application/json"
}
```

## ❓ Support

- **OpenRouter API issues**: Check [OpenRouter documentation](https://openrouter.ai/docs) 
- **Integration problems**: Create an issue in this GitHub repository
- **Community support**: Ask in the [Home Assistant forums](https://community.home-assistant.io)

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Thanks to [OpenRouter.ai](https://openrouter.ai) for providing unified access to multiple LLM APIs
- Home Assistant community for integration guidance and support
- All contributors and users who help improve this integration