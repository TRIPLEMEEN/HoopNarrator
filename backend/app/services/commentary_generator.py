from typing import List, Dict, Any, Optional
import openai
import json
import os
from pathlib import Path

from ...core.config import settings

class CommentaryGenerator:
    def __init__(self):
        # Set OpenAI API key
        openai.api_key = settings.OPENAI_API_KEY
        
        # Load personality templates
        self.personalities = self._load_personalities()
    
    def _load_personalities(self) -> Dict[str, Dict[str, str]]:
        """Load commentary personality templates"""
        return {
            "hype": {
                "system": """You are a hype basketball commentator known for your energetic and 
                over-the-top style. Use lots of excitement, exaggeration, and streetball slang. 
                Keep your commentary short, punchy, and engaging. Focus on the action and 
                make it sound like the most amazing play ever!""",
                "example": """
                [00:03] Player crosses half court
                [00:05] Player drives to the basket
                [00:07] Player makes a layup
                
                "OH MY GOODNESS! DID YOU SEE THAT MOVE?! HE JUST BROKE ANKLES AND FINISHED 
                WITH THE SMOOTH LAYUP! THE CROWD IS GOING WILD!"
                """
            },
            "analytical": {
                "system": """You are a professional basketball analyst. Provide insightful, 
                technical commentary about the plays. Focus on strategies, player movements, 
                and game situations. Be precise and knowledgeable.""",
                "example": """
                [00:03] Player receives the ball at the top of the key
                [00:05] Player uses a screen to create separation
                [00:07] Player makes a pull-up jump shot
                
                "Excellent use of the screen there. Notice how the player used the pick 
                to create just enough space for the pull-up jumper. Textbook execution 
                of the pick-and-roll play."
                """
            },
            # Other personalities can be added here
        }
    
    async def generate_commentary(
        self,
        events: List[Dict[str, Any]],
        personality: str = "hype",
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate commentary based on detected events and selected personality"""
        # Get personality template
        if personality not in self.personalities:
            personality = "hype"  # Default to hype
            
        personality_config = self.personalities[personality]
        
        # Format events as text
        events_text = self._format_events(events)
        
        # Prepare the prompt
        prompt = f"""Based on the following basketball play events, generate a short, engaging 
        commentary in the style of a {personality} basketball announcer. The commentary should 
        be exciting and match the intensity of the play.
        
        Events:
        {events_text}
        
        Commentary:"""
        
        try:
            # Call OpenAI API
            response = await openai.ChatCompletion.acreate(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": personality_config["system"]},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0.7,
                top_p=1.0,
                frequency_penalty=0.0,
                presence_penalty=0.0,
            )
            
            # Extract and clean the generated commentary
            commentary = response.choices[0].message.content.strip()
            
            return {
                "status": "success",
                "commentary": commentary,
                "personality": personality,
                "events_count": len(events)
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to generate commentary: {str(e)}",
                "personality": personality
            }
    
    def _format_events(self, events: List[Dict[str, Any]]) -> str:
        """Format events as a readable string"""
        if not events:
            return "No significant events detected."
            
        formatted = []
        for event in events:
            time_str = f"{event.get('time', 0):.1f}"
            event_type = event.get('event', 'unknown')
            confidence = event.get('confidence', 0) * 100
            
            formatted.append(
                f"[{time_str}s] {event_type} (confidence: {confidence:.1f}%)"
            )
            
        return "\n".join(formatted)
