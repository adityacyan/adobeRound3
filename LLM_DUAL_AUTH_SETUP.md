# LLM Service Dual Authentication Setup

This document explains how the LLM service supports both student/local development and evaluator/GCP modes.

## Overview

The `LLMService` class now supports two authentication modes:

1. **Student/Local Mode**: Uses `GEMINI_API_KEY` with the `google-generativeai` library
2. **Evaluator/GCP Mode**: Uses `GOOGLE_APPLICATION_CREDENTIALS` with Google's Gemini SDK

## Authentication Flow

The service automatically detects available credentials in this order:

1. **GCP Service Account** (Priority 1)
   - Checks for `GOOGLE_APPLICATION_CREDENTIALS` environment variable
   - Verifies the service account JSON file exists
   - Attempts to initialize GCP GenerativeService client
   
2. **API Key** (Fallback)
   - Uses `GEMINI_API_KEY` environment variable
   - Initializes with `google-generativeai` library

## Setup Instructions

### Student/Local Development

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables**:
   ```bash
   # Create .env file
   GEMINI_API_KEY=your_api_key_here
   GEMINI_MODEL=gemini-2.5-flash
   ```

3. **Run the application**:
   ```bash
   python -m backend.main
   ```

### Evaluator/GCP Mode

1. **Install dependencies** (includes GCP SDK):
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up service account**:
   ```bash
   # Set the service account JSON path
   export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
   
   # Optional: Set model name
   export GEMINI_MODEL=gemini-2.5-flash
   ```

3. **Run the application**:
   ```bash
   python -m backend.main
   ```

## Dependencies

### Required for Both Modes
- `google-generativeai==0.3.2`
- `pydantic==2.5.0`
- `python-dotenv==1.0.0`

### Additional for GCP Mode
- `google-ai-generativelanguage==0.4.0`
- `google-auth==2.25.0`

## API Compatibility

Both authentication modes provide the same API interface:

```python
from backend.llm_service import get_llm_service

llm = get_llm_service()

# All methods work the same regardless of auth mode
insights = llm.generate_insights(content)
summary = llm.generate_summary(content, mode="document")
takeaways = llm.generate_takeaways(content)

# Get authentication info
auth_info = llm.get_auth_info()
print(f"Using {auth_info['auth_mode']} authentication")
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | Student Mode | Personal API key for Gemini |
| `GOOGLE_APPLICATION_CREDENTIALS` | GCP Mode | Path to service account JSON |
| `GEMINI_MODEL` | Optional | Model name (default: gemini-2.5-flash) |

## Testing

Run the test script to verify both modes work:

```bash
python test_llm_dual_auth.py
```

This will:
- Test authentication mode detection
- Verify content generation works
- Check caching functionality
- Display authentication status

## Error Handling

The service gracefully handles authentication failures:

1. **GCP auth fails**: Falls back to API key mode
2. **API key missing**: Raises clear error message
3. **No credentials**: Provides helpful setup instructions

## Logging

The service logs authentication mode and key events:

```
INFO - Attempting GCP service account authentication...
INFO - GCP mode initialized successfully with model: gemini-2.5-flash
INFO - Sending request to Gemini API using gcp mode...
```

## Troubleshooting

### Common Issues

1. **"No valid authentication credentials found"**
   - Ensure either `GEMINI_API_KEY` or `GOOGLE_APPLICATION_CREDENTIALS` is set
   - Verify service account JSON file exists and is readable

2. **"Google Cloud dependencies not available"**
   - Install missing dependencies: `pip install google-ai-generativelanguage google-auth`

3. **"GCP authentication failed"**
   - Check service account permissions
   - Verify JSON file format
   - Ensure Generative Language API is enabled

### Debug Mode

Enable debug logging to see detailed authentication flow:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

from backend.llm_service import LLMService
llm = LLMService()
```

## Security Notes

- API keys should never be committed to version control
- Service account JSON files should be stored securely
- Use environment variables for all sensitive credentials
- GCP mode provides better security for production environments

## Performance

Both modes support the same caching mechanism:
- 1-hour cache expiry
- Content-based cache keys
- Identical performance characteristics
- Same rate limiting considerations
