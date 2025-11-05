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
        self.model_name = os.getenv("GEMINI_MODEL_NAME", "models/gemini-flash-latest")
        try:
            base_temperature = float(os.getenv("GEMINI_TEMPERATURE", "0.3"))
        except ValueError:
            base_temperature = 0.3
        # Generation config as dict (will convert to GenerationConfig when needed)
        # NOTE: JSON mode causes blocking even with NEGLIGIBLE ratings - disable it
        # We'll parse JSON from text response instead (like patchnote_featurizer)
        self.base_generation_config = {
            # "response_mime_type": "application/json",  # Disabled - causes blocking bug
            "temperature": base_temperature,
            "top_p": 0.95,
            "top_k": 40,
        }
        # Don't use safety settings - patchnote_featurizer doesn't use them and it works
        # Safety settings seem to trigger blocking even with NEGLIGIBLE ratings
        self.safety_settings = None
        # Removed safety context note - it might be triggering filters
        # The prompt itself should be clear enough
        self._safe_context_note = ""
        self._initialized = False
        
        if not HAS_GEMINI:
            logger.warning("google-generativeai not available")
            return
        
        if self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                # Match patchnote_featurizer: create model with NO generation_config
                # Let it use defaults - this avoids JSON mode blocking issues
                self.model = genai.GenerativeModel(self.model_name)
                self._initialized = True
                logger.info(f"Gemini client initialized with model={self.model_name} (no generation_config, matching patchnote_featurizer)")
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
            logger.info(
                "Gemini request: payload_chars=%s, user_payload_keys=%s",
                len(user_json_str),
                list(user_payload.keys())
            )
            
            # Build prompt (same style as patchnote_featurizer)
            # Match patchnote_featurizer format exactly: "{SYSTEM_PROMPT}\n\nMeta Comparison Data:\n{data}"
            if self._safe_context_note:
                full_prompt = f"{system_prompt}\n\n{self._safe_context_note}\n\nDraft Data:\n{user_json_str}"
            else:
                full_prompt = f"{system_prompt}\n\nDraft Data:\n{user_json_str}"
            
            # Increase timeout - patchnote_featurizer uses 30s, use 30s for draft analysis too
            effective_timeout = max(timeout_s, 30)
            
            logger.info(
                "Calling Gemini API with timeout=%ss, model=%s (no generation_config, no safety_settings, matching patchnote_featurizer exactly)",
                effective_timeout,
                self.model_name
            )
            
            # Match patchnote_featurizer exactly: call generate_content with just the prompt
            # No generation_config, no safety_settings - let model use defaults
            response = await asyncio.wait_for(
                self._call_gemini_async(
                    self.model,
                    prompt=full_prompt
                ),
                timeout=effective_timeout
            )
            logger.info("Gemini API call completed, processing response...")
            
            # Parse JSON response - GPT recommendation: Check candidate.content.parts FIRST
            # The response.text property raises ValueError if no content, so we check parts first
            try:
                logger.debug(f"Gemini response type: {type(response)}")
                
                if not response:
                    logger.error("Gemini returned None response")
                    raise GeminiError("Gemini returned None response")
                
                text = None
                content_exists = False
                
                # GPT recommendation: Check candidate.content.parts FIRST (before accessing response.text)
                # This avoids triggering ValueError from response.text property getter
                if hasattr(response, 'candidates') and len(response.candidates) > 0:
                    candidate = response.candidates[0]
                    finish_reason = getattr(candidate, 'finish_reason', None)
                    logger.debug(f"Gemini response finish_reason: {finish_reason}")
                    
                    # Check if content actually exists in candidate.content.parts (even if finish_reason=SAFETY)
                    if hasattr(candidate, 'content'):
                        if hasattr(candidate.content, 'parts'):
                            parts = candidate.content.parts
                            logger.debug(f"Gemini candidate.content.parts exists, length: {len(parts) if parts else 0}")
                            
                            parts_text = []
                            for i, part in enumerate(parts):
                                if hasattr(part, 'text'):
                                    part_text = getattr(part, 'text', None)
                                    if part_text:
                                        parts_text.append(part_text)
                                        logger.debug(f"Gemini part {i} has text ({len(part_text)} chars)")
                                    else:
                                        logger.debug(f"Gemini part {i} has text attr but is empty")
                                else:
                                    logger.debug(f"Gemini part {i} has no text attribute")
                            
                            if parts_text:
                                text = ' '.join(parts_text).strip()
                                content_exists = True
                                if finish_reason == 2:  # SAFETY
                                    logger.warning(f"Gemini finish_reason=SAFETY but content exists in parts - using it ({len(text)} chars)")
                                else:
                                    logger.debug(f"Gemini response text length: {len(text)} chars")
                            else:
                                logger.debug(f"Gemini candidate.content.parts exists but no text found in parts")
                        else:
                            logger.debug(f"Gemini candidate.content has no parts attribute")
                    else:
                        logger.debug(f"Gemini candidate has no content attribute")
                
                # If no content in parts, try response.text directly (patchnote_featurizer approach)
                # BUT: response.text property raises ValueError if no content, so wrap in try-except
                if not content_exists:
                    try:
                        # Access response.text - this will raise ValueError if no content
                        text = response.text.strip()
                        content_exists = True
                        logger.debug(f"Gemini response text length: {len(text)} chars")
                    except ValueError as e:
                        # ValueError means no content available (finish_reason=SAFETY with no parts)
                        logger.warning(f"Gemini response.text raised ValueError: {e}")
                        finish_reason_str = ""
                        if hasattr(response, 'candidates') and len(response.candidates) > 0:
                            candidate = response.candidates[0]
                            finish_reason = getattr(candidate, 'finish_reason', None)
                            finish_reason_str = f" (finish_reason: {finish_reason})"
                            
                            # Check safety ratings for debugging
                            if hasattr(candidate, 'safety_ratings') and len(candidate.safety_ratings) > 0:
                                all_negligible = True
                                for rating in candidate.safety_ratings:
                                    prob_value = rating.probability.value if hasattr(rating.probability, 'value') else 999
                                    if prob_value > 2:
                                        all_negligible = False
                                        break
                                if all_negligible:
                                    logger.warning(f"All safety ratings NEGLIGIBLE but no content available{finish_reason_str}")
                        
                        raise GeminiError(f"Gemini response blocked or empty: {str(e)}{finish_reason_str}")
                    except AttributeError as e:
                        logger.warning(f"Gemini response has no text attribute: {e}")
                        raise GeminiError(f"Gemini response has no text attribute: {str(e)}")
                
                # If we get here, we have text - continue with JSON extraction
                if not text:
                    raise GeminiError("Gemini returned empty response")
                    
                # Clean up any markdown code fences or extra whitespace
                # Gemini can sometimes wrap JSON in code fences even when JSON mode is requested
                if text.startswith("```json"):
                    text = text[7:]
                elif text.startswith("```"):
                    text = text[3:]
                if text.endswith("```"):
                    text = text[:-3]
                text = text.strip()
                
                # Try to find JSON object in the response (in case there's extra text before/after)
                # Models can sometimes prepend explanations even when JSON is requested
                import re
                json_match = re.search(r'\{.*\}', text, re.DOTALL)
                if json_match:
                    text = json_match.group(0)
                    logger.debug("Extracted JSON object from response text")
                else:
                    # If no JSON found, log the first 500 chars for debugging
                    logger.warning(f"No JSON object found in response. First 500 chars: {text[:500]}")
                    raise GeminiError("Gemini response does not contain valid JSON object. Response: " + text[:200])
                
                try:
                    result = json.loads(text)
                    logger.debug(f"Gemini returned JSON with {len(str(result))} chars")
                    return result
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse Gemini JSON: {e}")
                    logger.error(f"Response text length: {len(text)} chars")
                    logger.error(f"Response text (first 500 chars): {text[:500]}")
                    logger.error(f"Response text (last 500 chars): {text[-500:]}")
                    
                    # Check if JSON is truncated (common error patterns)
                    if "Expecting" in str(e) and ("delimiter" in str(e) or "value" in str(e)):
                        logger.warning("JSON appears to be truncated. Attempting to fix...")
                        # Try to fix common truncation issues
                        fixed_text = self._fix_truncated_json(text)
                        if fixed_text != text:
                            try:
                                result = json.loads(fixed_text)
                                logger.info("Successfully fixed truncated JSON")
                                return result
                            except json.JSONDecodeError:
                                logger.warning("Failed to fix truncated JSON")
                    
                    raise GeminiError(f"Invalid JSON response from Gemini: {e}")
                    
            except GeminiError:
                raise
            except Exception as e:
                logger.error(f"Gemini API call failed: {e}", exc_info=True)
                raise GeminiError(f"Gemini API error: {str(e)}")
        except asyncio.TimeoutError:
            raise GeminiError(f"Gemini API timeout after {effective_timeout}s")
        except GeminiError:
            raise
        except Exception as e:
            logger.error(f"Gemini API call failed: {e}", exc_info=True)
            raise GeminiError(f"Gemini API error: {str(e)}")
    
    async def _call_gemini_async(self, model, prompt=None, contents=None, safety_settings=None, generation_config=None):
        """Helper to run sync Gemini call in async context"""
        import asyncio
        
        # Run in executor since genai is sync
        loop = asyncio.get_running_loop()
        
        # Generate content - match patchnote_featurizer exactly
        # patchnote_featurizer calls: model.generate_content(prompt) with NO kwargs
        def _generate():
            # Match patchnote_featurizer: call generate_content with just the prompt, no kwargs
            if prompt:
                logger.info(
                    "Gemini calling generate_content with prompt only (matching patchnote_featurizer exactly)"
                )
                # NO kwargs - let model use defaults (no generation_config, no safety_settings)
                result = model.generate_content(prompt)
            elif contents:
                logger.info(
                    "Gemini calling generate_content with contents only"
                )
                result = model.generate_content(contents)
            else:
                raise ValueError("Either prompt or contents must be provided")
            
            logger.info(f"Gemini generate_content result type: {type(result)}")
            return result
        
        return await loop.run_in_executor(None, _generate)
    
    def _fix_truncated_json(self, text: str) -> str:
        """Attempt to fix truncated JSON by closing open structures"""
        # Remove trailing incomplete tokens
        text = text.strip()
        
        # Count open braces/brackets
        open_braces = text.count('{') - text.count('}')
        open_brackets = text.count('[') - text.count(']')
        
        # If JSON is incomplete, try to close it
        if open_braces > 0 or open_brackets > 0:
            # Remove incomplete last token (usually after a comma)
            # Look for patterns like: "key": "incomplete value
            # Or: "key": [incomplete
            import re
            
            # Remove trailing incomplete string (after last complete value)
            # Pattern: ends with incomplete quote or incomplete array/object
            if text.endswith('"') or text.endswith("'"):
                # Incomplete string, remove it
                text = re.sub(r',\s*"[^"]*"?\s*$', '', text)
            elif re.search(r',\s*"[^"]*$', text):
                # Incomplete string value, remove the incomplete entry
                text = re.sub(r',\s*"[^"]*$', '', text)
            
            # Close open structures
            text += '}' * open_braces
            text += ']' * open_brackets
        
        return text


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

