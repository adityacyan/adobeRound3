# Azure OpenAI TTS Podcast Generation Setup Guide

## 🎯 Overview

This guide explains how to set up and use the podcast generation feature that uses **Azure OpenAI Text-to-Speech** to create AI-generated podcast audio from document content. Microsoft has consolidated their speech services, and Azure OpenAI TTS provides the most modern and integrated approach.

## ⚙️ Azure OpenAI TTS Configuration

### 1. Azure OpenAI Service Setup

1. **Create Azure OpenAI Service**:
   - Go to [Azure Portal](https://portal.azure.com)
   - Create a new "Azure OpenAI" resource
   - Choose your subscription and resource group
   - Select a region that supports TTS models
   - Choose pricing tier

2. **Deploy TTS Model**:
   - After creation, go to your Azure OpenAI resource
   - Navigate to "Model deployments" or use Azure OpenAI Studio
   - Deploy the `tts-1` model
   - Note your deployment name (default: "tts")

3. **Get Your Credentials**:
   - Navigate to "Keys and Endpoint"
   - Copy `Key 1` (this is your `AZURE_TTS_KEY`)
   - Copy the `Endpoint` URL (this is your `AZURE_TTS_ENDPOINT`)

### 2. Environment Configuration

Your `.env` file should include:

```bash
# Azure OpenAI TTS Configuration (REQUIRED)
AZURE_TTS_KEY=your_actual_azure_openai_key_here
AZURE_TTS_ENDPOINT=https://your-resource.openai.azure.com
AZURE_TTS_DEPLOYMENT=tts
AZURE_TTS_API_VERSION=2025-03-01-preview

# Optional: Custom voice configuration (Azure OpenAI voices)
AZURE_TTS_VOICE=alloy
AZURE_TTS_HOST_VOICE=alloy
AZURE_TTS_GUEST_VOICE=echo
```

### 3. Available Voices

**Azure OpenAI TTS Voices**:
- `alloy` - Clear, balanced voice (great for hosts)
- `echo` - Deep, resonant voice (good for guests)
- `fable` - Warm, expressive voice
- `onyx` - Strong, confident voice
- `nova` - Bright, energetic voice
- `shimmer` - Smooth, professional voice

These voices are designed to sound natural and work well for podcast-style content.

## 🚀 Using the Podcast Feature

### 1. Frontend Usage

1. **Upload Documents**: Upload your PDF documents to the session
2. **Select Content** (Optional): Highlight specific text you want to focus on
3. **Generate Podcast**: Click the "Generate Podcast" button in the right sidebar
4. **Wait for Generation**: Processing typically takes 20-60 seconds
5. **Play Audio**: Use the built-in HTML5 audio player when ready

### 2. API Usage

**Generate Podcast Endpoint**:
```bash
POST /session/{session_id}/podcast/generate
Content-Type: application/json

{
  "content": "Optional specific content to include",
  "document_id": "Optional specific document ID",
  "use_insights": true,
  "use_dual_speaker": true,
  "include_selection": false
}
```

**Response**:
```json
{
  "audio_url": "http://localhost:8000/audio/podcast_session123_20250820_abc123.mp3",
  "duration_estimate": "2-5 minutes",
  "format": "MP3",
  "speakers_used": ["Host", "Guest"],
  "processing_time": 32.1,
  "timestamp": "2025-08-20T10:30:00"
}
```

## 🎙️ Podcast Features

### Dual-Speaker Format

When `use_dual_speaker: true`, the system creates a conversation between:
- **Host** (alloy voice): Introduces topics and asks questions
- **Guest** (echo voice): Provides insights and explanations

### Content Integration

The podcast automatically includes:
- **Document Content**: Main text from uploaded PDFs
- **AI Insights**: Generated takeaways, contradictions, and examples
- **Selected Text**: Highlighted content (if `include_selection: true`)
- **Natural Flow**: Conversational structure with introductions and conclusions

### Single-Speaker Fallback

When dual-speaker fails or `use_dual_speaker: false`:
- Uses single narrator voice (alloy)
- Condensed content presentation
- Still includes insights and key points

## 🔧 Technical Details

### Audio Processing Pipeline

1. **Content Preparation**: Gather document text and generate insights using Gemini
2. **Script Generation**: Create conversational podcast script with host/guest dialogue
3. **Voice Assignment**: Assign different Azure OpenAI voices to roles
4. **TTS Processing**: Generate audio segments using Azure OpenAI TTS API
5. **Audio Assembly**: Combine segments into final MP3 file
6. **File Serving**: Make audio available via HTTP endpoint

### Performance Considerations

- **Generation Time**: 20-60 seconds for typical content
- **File Size**: ~300KB - 1.5MB for 2-5 minute podcasts
- **Caching**: Audio files cached for 24 hours
- **Cleanup**: Old files automatically removed
- **Quality**: High-quality MP3 output suitable for podcast distribution

### Error Handling

The system gracefully handles:
- Missing Azure OpenAI credentials (returns error)
- TTS API timeouts (retries with fallback)
- Large content (automatic truncation)
- Network issues (proper error messages)

## 🧪 Testing

Run the test script to verify your setup:

```bash
python test_podcast_generation.py
```

This will test:
- Session creation
- Podcast service status
- Audio generation with sample content
- Audio file accessibility
- Single-speaker fallback

## 🎯 Use Cases

### Document Analysis Podcasts
- Upload research papers or reports
- Generate podcast summaries for audio consumption
- Include AI-generated insights and contradictions

### Educational Content
- Convert textbooks or articles to audio format
- Create conversational explanations of complex topics
- Generate study materials in podcast format

### Content Repurposing
- Transform written content into audio format
- Create accessible versions of documents
- Generate engaging audio summaries

## 🔍 Troubleshooting

### Common Issues

**"Audio service not available"**:
- Check `AZURE_TTS_KEY` and `AZURE_TTS_ENDPOINT` are set correctly
- Verify Azure OpenAI resource is active and has TTS model deployed
- Ensure you have quota remaining

**"Podcast generation failed"**:
- Check backend logs for detailed error messages
- Verify content is not empty
- Try with smaller content first
- Check TTS model deployment name matches `AZURE_TTS_DEPLOYMENT`

**"Audio file not found"**:
- Audio files are temporary (24-hour cleanup)
- Check if generation actually completed
- Verify backend is serving `/audio/` endpoint

**Frontend not calling API**:
- Check browser console for errors
- Verify backend is running on correct port
- Check CORS configuration

### Azure OpenAI TTS Limits

**Pay-per-use Model**:
- Charged per character processed
- No monthly limits like traditional Speech Services
- Pricing varies by region and usage

**Rate Limits**:
- Standard tier: 300 requests per minute
- Concurrent requests: Varies by subscription

## 🎉 Success Metrics

When working correctly, you should see:
- ✅ Podcast generation completes in under 1 minute
- ✅ High-quality audio plays clearly in browser
- ✅ Different voices for host/guest (dual-speaker mode)
- ✅ Natural conversational flow
- ✅ Insights integrated into discussion
- ✅ Download functionality works

## 📞 Support

If you encounter issues:
1. Check Azure OpenAI service status and deployment
2. Verify environment variables are correctly set
3. Run the test script for diagnostics
4. Check backend logs for detailed errors
5. Ensure your Azure subscription has OpenAI access approved

## 🆕 Why Azure OpenAI TTS?

**Advantages over traditional Azure Speech Services**:
- **Better Integration**: Part of the unified Azure OpenAI platform
- **Higher Quality**: More natural-sounding voices
- **Easier Setup**: Single API key for all Azure OpenAI services
- **Future-Proof**: Microsoft's focus for AI-driven TTS
- **Consistent Billing**: Same pricing model as other OpenAI services

The podcast feature provides an innovative way to consume document content in audio format, making information more accessible and engaging for users who prefer auditory learning or need hands-free access to content.

## 🚀 Using the Podcast Feature

### 1. Frontend Usage

1. **Upload Documents**: Upload your PDF documents to the session
2. **Select Content** (Optional): Highlight specific text you want to focus on
3. **Generate Podcast**: Click the "Generate Podcast" button in the right sidebar
4. **Wait for Generation**: Processing typically takes 30-90 seconds
5. **Play Audio**: Use the built-in audio player when ready

### 2. API Usage

**Generate Podcast Endpoint**:
```bash
POST /session/{session_id}/podcast/generate
Content-Type: application/json

{
  "content": "Optional specific content to include",
  "document_id": "Optional specific document ID",
  "use_insights": true,
  "use_dual_speaker": true,
  "include_selection": false
}
```

**Response**:
```json
{
  "audio_url": "http://localhost:8000/audio/podcast_session123_20250820_abc123.mp3",
  "duration_estimate": "2-5 minutes",
  "format": "MP3",
  "speakers_used": ["Host", "Guest"],
  "processing_time": 45.2,
  "timestamp": "2025-08-20T10:30:00"
}
```

## 🎙️ Podcast Features

### Dual-Speaker Format

When `use_dual_speaker: true`, the system creates a conversation between:
- **Host**: Introduces topics and asks questions
- **Guest**: Provides insights and explanations

### Content Integration

The podcast automatically includes:
- **Document Content**: Main text from uploaded PDFs
- **AI Insights**: Generated takeaways, contradictions, and examples
- **Selected Text**: Highlighted content (if `include_selection: true`)
- **Natural Flow**: Conversational structure with introductions and conclusions

### Single-Speaker Fallback

When dual-speaker fails or `use_dual_speaker: false`:
- Uses single narrator voice
- Condensed content presentation
- Still includes insights and key points

## 🔧 Technical Details

### Audio Processing Pipeline

1. **Content Preparation**: Gather document text and generate insights
2. **Script Generation**: Create conversational podcast script
3. **Voice Assignment**: Assign different voices to host/guest roles
4. **TTS Processing**: Generate audio segments using Azure TTS
5. **Audio Assembly**: Combine segments into final MP3 file
6. **File Serving**: Make audio available via HTTP endpoint

### Performance Considerations

- **Generation Time**: 30-90 seconds for typical content
- **File Size**: ~500KB - 2MB for 2-5 minute podcasts
- **Caching**: Audio files cached for 24 hours
- **Cleanup**: Old files automatically removed

### Error Handling

The system gracefully handles:
- Missing Azure credentials (returns error)
- TTS service timeouts (retries with fallback)
- Large content (automatic truncation)
- Network issues (proper error messages)

## 🧪 Testing

Run the test script to verify your setup:

```bash
python test_podcast_generation.py
```

This will test:
- Session creation
- Podcast service status
- Audio generation with sample content
- Audio file accessibility
- Single-speaker fallback

## 🎯 Use Cases

### Document Analysis Podcasts
- Upload research papers or reports
- Generate podcast summaries for audio consumption
- Include AI-generated insights and contradictions

### Educational Content
- Convert textbooks or articles to audio format
- Create conversational explanations of complex topics
- Generate study materials in podcast format

### Content Repurposing
- Transform written content into audio format
- Create accessible versions of documents
- Generate engaging audio summaries

## 🔍 Troubleshooting

### Common Issues

**"Audio service not available"**:
- Check `AZURE_SPEECH_KEY` and `AZURE_SPEECH_REGION` are set
- Verify Azure Speech Service is active
- Ensure you have quota remaining

**"Podcast generation failed"**:
- Check backend logs for detailed error messages
- Verify content is not empty
- Try with smaller content first

**"Audio file not found"**:
- Audio files are temporary (24-hour cleanup)
- Check if generation actually completed
- Verify backend is serving `/audio/` endpoint

**Frontend not calling API**:
- Check browser console for errors
- Verify backend is running on correct port
- Check CORS configuration

### Azure TTS Limits

**Free Tier**:
- 5 audio hours per month
- 500,000 characters per month
- Standard voices only

**Standard Tier**:
- Pay per character
- Neural voices available
- Higher quality output

## 🎉 Success Metrics

When working correctly, you should see:
- ✅ Podcast generation completes in under 2 minutes
- ✅ Audio plays clearly in browser
- ✅ Different voices for host/guest (dual-speaker mode)
- ✅ Natural conversational flow
- ✅ Insights integrated into discussion
- ✅ Download functionality works

## 📞 Support

If you encounter issues:
1. Check Azure Speech Service status
2. Verify environment variables
3. Run the test script for diagnostics
4. Check backend logs for detailed errors
5. Ensure you have sufficient Azure quota

The podcast feature provides an innovative way to consume document content in audio format, making information more accessible and engaging for users who prefer auditory learning or need hands-free access to content.
