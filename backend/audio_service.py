"""
Audio service for podcast generation using Gemini Text-to-Speech.
Implements podcast-style audio generation from document content and insights
using the Gemini TTS Interactions API (supports multi-speaker dialogue).
"""
import os
import asyncio
import logging
import tempfile
import uuid
import base64
import wave
from datetime import datetime
from typing import Dict, Optional
from pathlib import Path
from dotenv import load_dotenv

import google.genai as genai

load_dotenv()

logger = logging.getLogger(__name__)

# Default Gemini TTS model (latest 3.1 Flash, overridable via env)
GEMINI_TTS_MODEL = os.getenv("GEMINI_TTS_MODEL", "gemini-3.1-flash-tts-preview")

# Map legacy voice names to Gemini prebuilt voices
GEMINI_VOICE_MAP = {
    "host": "Kore",
    "guest": "Puck",
    "default": "Puck",
    "nova": "Kore",
    "onyx": "Puck",
    "alloy": "Charon",
}


class AudioService:
    """Service for generating podcast-style audio content using Gemini TTS."""

    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.model_name = os.getenv("GEMINI_TTS_MODEL", GEMINI_TTS_MODEL)

        # Voice mapping
        self.voices = {
            "host": os.getenv("GEMINI_TTS_HOST_VOICE", GEMINI_VOICE_MAP["host"]),
            "guest": os.getenv("GEMINI_TTS_GUEST_VOICE", GEMINI_VOICE_MAP["guest"]),
        }
        self.default_voice = os.getenv("GEMINI_TTS_VOICE", GEMINI_VOICE_MAP["default"])

        # Audio output directory
        self.audio_dir = Path(tempfile.gettempdir()) / "podcast_audio"
        self.audio_dir.mkdir(exist_ok=True)

        self.client = genai.Client(api_key=self.api_key) if self.api_key else None

        logger.info(
            f"AudioService initialized with Gemini TTS model: {self.model_name}"
        )
        logger.info(
            f"Voices configured - Host: {self.voices['host']}, Guest: {self.voices['guest']}"
        )

    def _validate_config(self) -> bool:
        """Validate Gemini TTS configuration."""
        if not self.api_key:
            logger.error(
                "Missing GEMINI_API_KEY. Gemini TTS requires a valid API key."
            )
            return False
        if not self.client:
            logger.error("Gemini client not initialized.")
            return False
        return True

    @staticmethod
    def _save_wav(filename: str, pcm: bytes, channels: int = 1, rate: int = 24000, sample_width: int = 2):
        """Write raw PCM bytes to a WAV file."""
        with wave.open(filename, "wb") as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(sample_width)
            wf.setframerate(rate)
            wf.writeframes(pcm)

    def _generate_podcast_script(self, content: str, insights: Optional[Dict] = None) -> str:
        """
        Generate a podcast-style script with dual speakers as a conversation prompt
        suitable for Gemini TTS multi-speaker mode.
        """
        lines = []

        # Scene directive for better expressiveness
        lines.append(
            "TTS the following conversation between Host and Guest in a "
            "lively, engaging podcast style. The Host leads the discussion "
            "and the Guest provides analysis."
        )
        lines.append("")

        # Introduction
        lines.append(
            "Host: Welcome to today's document analysis podcast. "
            "I'm your host, and we're going to explore some fascinating "
            "insights from the content we've analyzed."
        )

        if insights and insights.get("takeaways"):
            lines.append(
                "Guest: That's right! Let me start with the key takeaways "
                "from this document."
            )

            takeaways = insights["takeaways"][:3]
            for i, takeaway in enumerate(takeaways, 1):
                if i == 1:
                    lines.append(f"Guest: Takeaway number {i}: {takeaway}")
                else:
                    lines.append(f"Guest: Another key point: {takeaway}")

        # Main content discussion
        if content:
            content_preview = content[:500] + "..." if len(content) > 500 else content
            lines.append("Host: Now let's dive into the selected content itself.")
            lines.append(f"Guest: Here's what the document tells us: {content_preview}")

        # Contradictions
        if insights and insights.get("contradictions"):
            lines.append(
                "Host: I noticed there might be some contradictions or "
                "areas that need clarification."
            )
            contradictions = insights["contradictions"][:2]
            for c in contradictions:
                lines.append(f"Guest: Here's something worth noting: {c}")

        # Examples
        if insights and insights.get("examples"):
            lines.append(
                "Host: Can you give us some concrete examples to illustrate "
                "these points?"
            )
            examples = insights["examples"][:2]
            for e in examples:
                lines.append(f"Guest: Absolutely. Here's a good example: {e}")

        # Conclusion
        lines.append(
            "Host: This has been a great analysis. Any final thoughts?"
        )
        lines.append(
            "Guest: The key is to remember these insights when applying "
            "this knowledge in practice."
        )
        lines.append(
            "Host: Thanks for joining us on this document analysis journey. "
            "Until next time!"
        )

        return "\n".join(lines)

    async def _generate_with_gemini(
        self,
        prompt: str,
        use_dual_speaker: bool,
        output_path: str,
    ) -> bool:
        """
        Send a TTS request to Gemini and save the output audio.

        Uses the Interactions API for multi-speaker or single-speaker audio.
        Runs the synchronous SDK call in a thread executor to avoid blocking.
        """
        try:

            def _call():
                if use_dual_speaker:
                    return self.client.interactions.create(
                        model=self.model_name,
                        input=prompt,
                        response_format={"type": "audio"},
                        generation_config={
                            "speech_config": [
                                {"speaker": "Host", "voice": self.voices["host"]},
                                {"speaker": "Guest", "voice": self.voices["guest"]},
                            ]
                        },
                    )
                else:
                    return self.client.interactions.create(
                        model=self.model_name,
                        input=prompt,
                        response_format={"type": "audio"},
                        generation_config={
                            "speech_config": [{"voice": self.default_voice}]
                        },
                    )

            loop = asyncio.get_event_loop()
            interaction = await loop.run_in_executor(None, _call)

            audio_data = base64.b64decode(interaction.output_audio.data)
            self._save_wav(output_path, audio_data)
            logger.info(f"Audio generated successfully: {output_path}")
            return True

        except Exception as e:
            logger.error(f"Gemini TTS request failed: {e}")
            return False

    async def generate_podcast(
        self,
        session_id: str,
        content: str,
        insights: Optional[Dict] = None,
        use_dual_speaker: bool = True,
    ) -> Optional[str]:
        """
        Generate a podcast-style audio file from content and insights using Gemini TTS.

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
            podcast_id = str(uuid.uuid4())[:8]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"podcast_{session_id}_{timestamp}_{podcast_id}.wav"
            output_path = str(self.audio_dir / output_filename)

            # Build the prompt
            if use_dual_speaker:
                prompt = self._generate_podcast_script(content, insights)
            else:
                full_text = "Read the following content in a clear, engaging podcast style. "
                if insights and insights.get("takeaways"):
                    full_text += "Here are the key takeaways: "
                    full_text += " ".join(insights["takeaways"][:3])
                    full_text += " "
                if content:
                    cp = content[:800] + "..." if len(content) > 800 else content
                    full_text += f"The main content: {cp} "
                if insights and insights.get("examples"):
                    full_text += "Some examples: "
                    full_text += " ".join(insights["examples"][:2])
                full_text += " Thank you for listening."
                prompt = full_text

            logger.info(
                f"Generating {'dual' if use_dual_speaker else 'single'}-speaker "
                f"podcast with model {self.model_name}"
            )
            logger.info(f"Host voice: {self.voices['host']}, Guest voice: {self.voices['guest']}")

            success = await self._generate_with_gemini(
                prompt, use_dual_speaker, output_path
            )

            if success:
                logger.info(f"Podcast generated successfully: {output_path}")
                return output_path
            else:
                logger.error("Failed to generate podcast audio")
                return None

        except Exception as e:
            logger.error(f"Error generating podcast: {e}")
            return None

    def get_audio_url(self, audio_path: str, base_url: str = None) -> str:
        """Generate a URL for accessing the audio file."""
        filename = os.path.basename(audio_path)
        # Return relative URL that works with nginx proxy
        return f"/audio/{filename}"

    def cleanup_old_audio_files(self, max_age_hours: int = 24):
        """Clean up old audio files to save space."""
        try:
            current_time = datetime.now()
            for audio_file in self.audio_dir.glob("*.wav"):
                file_time = datetime.fromtimestamp(audio_file.stat().st_mtime)
                if (current_time - file_time).total_seconds() > max_age_hours * 3600:
                    audio_file.unlink()
                    logger.info(f"Cleaned up old audio file: {audio_file}")
        except Exception as e:
            logger.error(f"Error cleaning up audio files: {e}")


# Global audio service instance
audio_service = AudioService()
