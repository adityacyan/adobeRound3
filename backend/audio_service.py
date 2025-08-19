"""
Audio service for podcast generation using Azure OpenAI Text-to-Speech.
Implements podcast-style audio generation from document content and insights.
"""
import os
import asyncio
import logging
import tempfile
import uuid
import httpx
import base64
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class AudioService:
    """Service for generating podcast-style audio content using Azure OpenAI TTS."""
    
    def __init__(self):
        """Initialize the audio service with Azure OpenAI TTS configuration."""
        self.azure_tts_key = os.getenv("AZURE_TTS_KEY")
        self.azure_tts_endpoint = os.getenv("AZURE_TTS_ENDPOINT")
        self.azure_tts_deployment = os.getenv("AZURE_TTS_DEPLOYMENT", "tts")
        self.azure_tts_api_version = os.getenv("AZURE_TTS_API_VERSION", "2025-03-01-preview")
        
        # Voice configuration for podcast (dual-speaker setup using Azure OpenAI voices)
        self.voices = {
            "host": os.getenv("AZURE_TTS_HOST_VOICE", "nova"),
            "guest": os.getenv("AZURE_TTS_GUEST_VOICE", "onyx")
        }
        self.default_voice = os.getenv("AZURE_TTS_VOICE", "alloy")
        
        # Audio output directory
        self.audio_dir = Path(tempfile.gettempdir()) / "podcast_audio"
        self.audio_dir.mkdir(exist_ok=True)
        
        logger.info(f"AudioService initialized with Azure OpenAI TTS endpoint: {self.azure_tts_endpoint}")
        logger.info(f"Voices configured - Host: {self.voices['host']}, Guest: {self.voices['guest']}")
    
    def _validate_config(self) -> bool:
        """Validate Azure OpenAI TTS configuration."""
        if not self.azure_tts_key or not self.azure_tts_endpoint:
            logger.error("Missing Azure OpenAI TTS configuration. Check AZURE_TTS_KEY and AZURE_TTS_ENDPOINT")
            return False
        return True
    
    def _get_tts_url(self) -> str:
        """Construct the Azure OpenAI TTS API URL."""
        base_url = self.azure_tts_endpoint.rstrip('/')
        return f"{base_url}/openai/deployments/{self.azure_tts_deployment}/audio/speech?api-version={self.azure_tts_api_version}"
    
    def _generate_podcast_script(self, content: str, insights: Optional[Dict] = None) -> List[Tuple[str, str]]:
        """
        Generate a podcast-style script with dual speakers.
        Returns list of (speaker, text) tuples.
        """
        script = []
        
        # Introduction
        script.append(("host", "Welcome to today's document analysis podcast. I'm your host, and we're going to explore some fascinating insights from the content we've analyzed."))
        
        if insights and insights.get("takeaways"):
            script.append(("guest", "That's right! Let me start with the key takeaways from this document."))
            
            takeaways = insights["takeaways"][:3]  # Limit to top 3 takeaways
            for i, takeaway in enumerate(takeaways, 1):
                script.append(("guest", f"Takeaway number {i}: {takeaway}"))
                if i < len(takeaways):
                    script.append(("host", "Interesting point. What's next?"))
        
        # Main content discussion
        if content:
            content_preview = content[:500] + "..." if len(content) > 500 else content
            script.append(("host", "Now let's dive into the selected content itself."))
            script.append(("guest", f"Here's what the document tells us: {content_preview}"))
        
        # Contradictions (if any)
        if insights and insights.get("contradictions"):
            script.append(("host", "I noticed there might be some contradictions or areas that need clarification."))
            contradictions = insights["contradictions"][:2]  # Limit to top 2
            for contradiction in contradictions:
                script.append(("guest", f"You're right. Here's something worth noting: {contradiction}"))
        
        # Examples (if any)
        if insights and insights.get("examples"):
            script.append(("host", "Can you give us some concrete examples to illustrate these points?"))
            examples = insights["examples"][:2]  # Limit to top 2
            for example in examples:
                script.append(("guest", f"Absolutely. Here's a good example: {example}"))
        
        # Conclusion
        script.append(("host", "This has been a great analysis. Any final thoughts?"))
        script.append(("guest", "The key is to remember these insights when applying this knowledge in practice."))
        script.append(("host", "Thanks for joining us on this document analysis journey. Until next time!"))
        
        return script
    
    async def _synthesize_speech_segment(self, text: str, voice: str, output_file: str) -> bool:
        """Synthesize speech for a single segment using Azure OpenAI TTS."""
        try:
            url = self._get_tts_url()
            
            headers = {
                "api-key": self.azure_tts_key,
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "tts-1",  # Use the model name, not deployment name
                "input": text,
                "voice": voice,
                "response_format": "mp3"
            }
            
            logger.info(f"Making TTS request to: {url}")
            logger.info(f"Payload: {payload}")
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(url, headers=headers, json=payload)
                
                if response.status_code == 200:
                    with open(output_file, 'wb') as f:
                        f.write(response.content)
                    logger.info(f"Audio segment created: {output_file}")
                    return True
                else:
                    logger.error(f"TTS API error: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error synthesizing speech: {e}")
            return False
    
    def _combine_audio_segments(self, segment_files: List[str], output_file: str) -> bool:
        """
        Combine multiple audio segments into a single file.
        Simple concatenation approach.
        """
        try:
            import shutil
            
            with open(output_file, 'wb') as outfile:
                for segment_file in segment_files:
                    if os.path.exists(segment_file):
                        with open(segment_file, 'rb') as infile:
                            shutil.copyfileobj(infile, outfile)
                        # Clean up segment file
                        os.remove(segment_file)
            
            logger.info(f"Combined audio saved to: {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error combining audio segments: {e}")
            return False
    
    async def generate_podcast(
        self, 
        session_id: str, 
        content: str, 
        insights: Optional[Dict] = None,
        use_dual_speaker: bool = True
    ) -> Optional[str]:
        """
        Generate a podcast-style audio file from content and insights.
        
        Args:
            session_id: Session identifier
            content: Main content to include in podcast
            insights: Generated insights (takeaways, contradictions, examples)
            use_dual_speaker: Whether to use dual-speaker format
            
        Returns:
            Path to generated audio file, or None if generation failed
        """
        if not self._validate_config():
            return None
        
        try:
            # Generate unique filename
            podcast_id = str(uuid.uuid4())[:8]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"podcast_{session_id}_{timestamp}_{podcast_id}.mp3"
            output_path = self.audio_dir / output_filename
            
            if use_dual_speaker and len(self.voices) >= 2:
                # Generate dual-speaker podcast
                script = self._generate_podcast_script(content, insights)
                segment_files = []
                
                for i, (speaker, text) in enumerate(script):
                    voice = self.voices.get(speaker, self.default_voice)
                    segment_file = self.audio_dir / f"segment_{podcast_id}_{i}.mp3"
                    
                    success = await self._synthesize_speech_segment(
                        text, voice, str(segment_file)
                    )
                    
                    if success:
                        segment_files.append(str(segment_file))
                    else:
                        logger.error(f"Failed to generate segment {i}")
                
                # Combine segments
                if segment_files:
                    if self._combine_audio_segments(segment_files, str(output_path)):
                        logger.info(f"Dual-speaker podcast generated: {output_path}")
                        return str(output_path)
                else:
                    logger.error("No audio segments were successfully generated")
                    return None
                    
            else:
                # Single-speaker fallback
                logger.info("Using single-speaker format")
                
                # Create simplified single-speaker script
                full_text = f"Welcome to your document analysis podcast. "
                
                if insights and insights.get("takeaways"):
                    full_text += "Here are the key takeaways: "
                    full_text += " ".join(insights["takeaways"][:3])
                    full_text += " "
                
                if content:
                    content_preview = content[:800] + "..." if len(content) > 800 else content
                    full_text += f"The main content discusses: {content_preview} "
                
                if insights and insights.get("examples"):
                    full_text += "Some examples include: "
                    full_text += " ".join(insights["examples"][:2])
                
                full_text += " Thank you for listening to this analysis."
                
                success = await self._synthesize_speech_segment(
                    full_text, self.default_voice, str(output_path)
                )
                
                if success:
                    logger.info(f"Single-speaker podcast generated: {output_path}")
                    return str(output_path)
                else:
                    logger.error("Failed to generate single-speaker podcast")
                    return None
                    
        except Exception as e:
            logger.error(f"Error generating podcast: {e}")
            return None
    
    def get_audio_url(self, audio_path: str, base_url: str = "http://localhost:8000") -> str:
        """Generate a URL for accessing the audio file."""
        filename = os.path.basename(audio_path)
        return f"{base_url}/audio/{filename}"
    
    def cleanup_old_audio_files(self, max_age_hours: int = 24):
        """Clean up old audio files to save space."""
        try:
            current_time = datetime.now()
            for audio_file in self.audio_dir.glob("*.mp3"):
                file_time = datetime.fromtimestamp(audio_file.stat().st_mtime)
                if (current_time - file_time).total_seconds() > max_age_hours * 3600:
                    audio_file.unlink()
                    logger.info(f"Cleaned up old audio file: {audio_file}")
        except Exception as e:
            logger.error(f"Error cleaning up audio files: {e}")

# Global audio service instance
audio_service = AudioService()
