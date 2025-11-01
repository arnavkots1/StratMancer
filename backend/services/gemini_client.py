"""
Thin adapter around google-generativeai for Draft IQ v2.
Handles JSON-only responses with proper error handling and timeouts.
"""

import logging
import os
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

try:
    import google.generativeai as genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False
    logger.warning("google-generativeai not installed")


class GeminiError(Exception):
    """Raised when Gemini API calls fail"""
    pass


class GeminiClient:
    """Thin wrapper around Google Gemini API for JSON responses"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Gemini client.
        
        Args:
            api_key: Gemini API key (defaults to GEMINI_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model = None
        self._initialized = False
        
        if not HAS_GEMINI:
            logger.warning("google-generativeai not available")
            return
        
        if self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel(
                    'models/gemini-flash-latest',
                    generation_config={
                        'response_mime_type': 'application/json',
                    }
                )
                self._initialized = True
                logger.info("Gemini client initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini client: {e}")
        else:
            logger.warning("GEMINI_API_KEY not set")
    
    def available(self) -> bool:
        """Check if Gemini is available and configured"""
        return HAS_GEMINI and self._initialized and self.model is not None
    
    async def complete_json(
        self,
        system_prompt: str,
        user_payload: Dict[str, Any],
        *,
        timeout_s: int = 8,
        max_output_tokens: int = 700
    ) -> Dict[str, Any]:
        """
        Call Gemini API with JSON-only response.
        
        Args:
            system_prompt: System prompt string
            user_payload: User payload dict (will be JSON-serialized)
            timeout_s: Timeout in seconds (default: 8)
            max_output_tokens: Max output tokens (default: 700)
            
        Returns:
            Parsed JSON dict
            
        Raises:
            GeminiError: If API call fails or returns invalid JSON
        """
        if not self.available():
            raise GeminiError("Gemini client not available")
        
        import json
        import asyncio
        
        try:
            # Format user payload as JSON string for the prompt
            user_json_str = json.dumps(user_payload, indent=2)
            full_prompt = f"{system_prompt}\n\nUser Data:\n{user_json_str}\n\nOutput JSON only:"
            
            # Configure generation with JSON mode
            generation_config = {
                'response_mime_type': 'application/json',
                'max_output_tokens': max_output_tokens,
                'temperature': 0.3,  # Lower temperature for more consistent JSON
            }
            
            # Create model with config (need to recreate for each call with custom config)
            model = genai.GenerativeModel(
                'models/gemini-flash-latest',
                generation_config=generation_config
            )
            
            # Call API with timeout
            try:
                response = await asyncio.wait_for(
                    self._call_gemini_async(model, full_prompt),
                    timeout=timeout_s
                )
            except asyncio.TimeoutError:
                raise GeminiError(f"Gemini API timeout after {timeout_s}s")
            
            # Parse JSON response
            if not hasattr(response, 'text'):
                raise GeminiError("Gemini response has no text attribute")
            
            text = response.text.strip()
            
            # Clean up any markdown code fences
            if text.startswith("```json"):
                text = text[7:]
            elif text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()
            
            try:
                result = json.loads(text)
                logger.debug(f"Gemini returned JSON with {len(str(result))} chars")
                return result
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse Gemini JSON: {e}")
                logger.error(f"Response text (first 500 chars): {text[:500]}")
                raise GeminiError(f"Invalid JSON response from Gemini: {e}")
                
        except GeminiError:
            raise
        except Exception as e:
            logger.error(f"Gemini API call failed: {e}", exc_info=True)
            raise GeminiError(f"Gemini API error: {str(e)}")
    
    async def _call_gemini_async(self, model, prompt: str):
        """Helper to run sync Gemini call in async context"""
        import asyncio
        
        # Run in executor since genai is sync
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: model.generate_content(prompt)
        )


# Global instance
_gemini_client: Optional[GeminiClient] = None


def get_gemini_client() -> GeminiClient:
    """Get or create global Gemini client instance"""
    global _gemini_client
    if _gemini_client is None:
        from backend.config import settings
        api_key = settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY")
        _gemini_client = GeminiClient(api_key)
    return _gemini_client

