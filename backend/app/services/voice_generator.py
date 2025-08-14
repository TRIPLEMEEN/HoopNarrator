import os
import requests
import json
from typing import Dict, Any, Optional, Union
from pathlib import Path
import openai
from elevenlabs.client import ElevenLabs

from app.core.config import settings

class VoiceGenerator:
    def __init__(self):
        # Set API keys
        openai.api_key = settings.OPENAI_API_KEY
        if settings.ELEVENLABS_API_KEY:
            self.client = ElevenLabs(api_key=settings.ELEVENLABS_API_KEY)
        
        # Voice profiles for different personalities
        self.voice_profiles = {
            "hype": {
                "provider": "elevenlabs",
                "voice_id": "21m00Tcm4TlvDq8ikWAM",  # Young male energetic voice
                "stability": 0.5,
                "similarity_boost": 0.75,
                "style": 0.8,
                "use_speaker_boost": True
            },
            "analytical": {
                "provider": "openai",
                "voice": "onyx",  # Professional male voice
                "speed": 1.0
            },
            "trash_talk": {
                "provider": "elevenlabs",
                "voice_id": "AZnzlk1XvdvUeBnXmlld",  # Confident, slightly aggressive voice
                "stability": 0.4,
                "similarity_boost": 0.8,
                "style": 0.9,
                "use_speaker_boost": True
            },
            "classic": {
                "provider": "openai",
                "voice": "shimmer",  # Clear, professional voice
                "speed": 1.0
            },
            "shakespeare": {
                "provider": "elevenlabs",
                "voice_id": "ErXwobaYiN019PkySvjV",  # Deep, theatrical voice
                "stability": 0.6,
                "similarity_boost": 0.8,
                "style": 0.7,
                "use_speaker_boost": True
            }
        }
    
    async def generate_voiceover(
        self,
        text: str,
        personality: str = "hype",
        output_path: str = "output"
    ) -> Dict[str, Any]:
        """Generate voiceover from text using the specified personality"""
        # Ensure output directory exists
        os.makedirs(output_path, exist_ok=True)
        
        # Get voice profile
        if personality not in self.voice_profiles:
            personality = "hype"  # Default to hype
        
        voice_profile = self.voice_profiles[personality]
        output_file = os.path.join(output_path, f"voiceover_{personality}.mp3")
        
        try:
            if voice_profile["provider"] == "elevenlabs":
                return await self._generate_with_elevenlabs(
                    text=text,
                    voice_profile=voice_profile,
                    output_file=output_file
                )
            else:  # Default to OpenAI
                return await self._generate_with_openai(
                    text=text,
                    voice_profile=voice_profile,
                    output_file=output_file
                )
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to generate voiceover: {str(e)}",
                "personality": personality,
                "output_file": None
            }
    
    async def _generate_with_elevenlabs(
        self,
        text: str,
        voice_profile: Dict[str, Any],
        output_file: str
    ) -> Dict[str, Any]:
        """Generate voiceover using ElevenLabs API"""
        # Generate audio using ElevenLabs
        audio = self.client.generate(
            text=text,
            voice=voice_profile["voice_id"],
            model="eleven_monolingual_v1",
            stability=voice_profile.get("stability", 0.5),
            similarity_boost=voice_profile.get("similarity_boost", 0.75),
            style=voice_profile.get("style", 0.5),
            use_speaker_boost=voice_profile.get("use_speaker_boost", True)
        )
        
        # Save audio file
        with open(output_file, "wb") as f:
            f.write(audio)
        
        return {
            "status": "success",
            "provider": "elevenlabs",
            "voice_id": voice_profile["voice_id"],
            "output_file": output_file
        }
    
    async def _generate_with_openai(
        self,
        text: str,
        voice_profile: Dict[str, Any],
        output_file: str
    ) -> Dict[str, Any]:
        """Generate voiceover using OpenAI's TTS API"""
        response = await openai.audio.speech.create(
            model="tts-1",
            voice=voice_profile.get("voice", "alloy"),
            input=text,
            speed=voice_profile.get("speed", 1.0)
        )
        
        # Save audio file
        response.stream_to_file(output_file)
        
        return {
            "status": "success",
            "provider": "openai",
            "voice": voice_profile.get("voice", "alloy"),
            "output_file": output_file
        }
