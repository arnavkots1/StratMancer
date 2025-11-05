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
            # Format user payload as JSON string for the prompt (same style as patchnote_featurizer)
            user_json_str = json.dumps(user_payload, indent=2)
            # Match patchnote_featurizer prompt structure exactly
            full_prompt = f"{system_prompt}\n\nDraft Data:\n{user_json_str}"
            
            logger.info(f"Gemini request: prompt_length={len(full_prompt)}, user_payload_keys={list(user_payload.keys())}")
            
            # Don't pass safety_settings - match patchnote_featurizer exactly which works
            # The default safety settings should be fine for game analysis
            safety_settings = None
            logger.info("Not passing safety_settings (using defaults, same as patchnote_featurizer)")
            
            # Disable JSON mode - patchnote_featurizer doesn't use it and it might be causing blocks
            # We'll ask for JSON in the prompt and parse it manually (like patchnote_featurizer)
            generation_config = genai.GenerationConfig(
                max_output_tokens=max_output_tokens,
                temperature=0.3,  # Lower temperature for more consistent output
            )
            
            logger.info(f"Gemini generation config: NO JSON mode (matching patchnote_featurizer), max_output_tokens={max_output_tokens}, temperature=0.3")
            
            # Use the same model name and setup as patchnote_featurizer which works
            model_name = 'models/gemini-flash-latest'
            logger.info(f"Using model: {model_name}")
            
            # Create model WITHOUT JSON mode (same as patchnote_featurizer)
            model = genai.GenerativeModel(
                model_name,
                generation_config=generation_config
            )
            
            logger.info(f"Gemini model created (NO JSON mode, matching patchnote_featurizer)")
            
            # Call API with timeout (no safety settings, same as patchnote_featurizer)
            try:
                logger.info(f"Calling Gemini API with timeout={timeout_s}s (no safety_settings, matching patchnote_featurizer)...")
                response = await asyncio.wait_for(
                    self._call_gemini_async(model, full_prompt, safety_settings=None),
                    timeout=timeout_s
                )
                logger.info("Gemini API call completed, processing response...")
            except asyncio.TimeoutError:
                raise GeminiError(f"Gemini API timeout after {timeout_s}s")
            
            # Parse JSON response - handle safety blocks and empty responses
            try:
                logger.debug(f"Gemini response type: {type(response)}")
                logger.debug(f"Gemini response attributes: {dir(response)}")
                
                # Check finish_reason first to see if response was blocked
                if hasattr(response, 'candidates') and len(response.candidates) > 0:
                    candidate = response.candidates[0]
                    finish_reason = getattr(candidate, 'finish_reason', None)
                    finish_reason_name = getattr(candidate, 'finish_reason', None)
                    
                    logger.info(f"Gemini response finish_reason: {finish_reason} (type: {type(finish_reason)})")
                    
                    # Log safety ratings if available
                    if hasattr(candidate, 'safety_ratings'):
                        logger.info(f"Gemini safety ratings: {candidate.safety_ratings}")
                        for rating in candidate.safety_ratings:
                            # Log both enum name and numeric value for debugging
                            prob_name = rating.probability.name if hasattr(rating.probability, 'name') else str(rating.probability)
                            prob_value = rating.probability.value if hasattr(rating.probability, 'value') else str(rating.probability)
                            cat_name = rating.category.name if hasattr(rating.category, 'name') else str(rating.category)
                            cat_value = rating.category.value if hasattr(rating.category, 'value') else str(rating.category)
                            logger.info(f"  - {cat_name} ({cat_value}): {prob_name} ({prob_value})")
                    
                    if finish_reason == 2:  # SAFETY
                        logger.warning(f"Gemini response has finish_reason SAFETY")
                        
                        # Check safety ratings if available
                        all_negligible = True
                        safety_ratings_empty = True
                        if hasattr(candidate, 'safety_ratings') and len(candidate.safety_ratings) > 0:
                            safety_ratings_empty = False
                            for rating in candidate.safety_ratings:
                                prob_name = rating.probability.name if hasattr(rating.probability, 'name') else str(rating.probability)
                                prob_value = rating.probability.value if hasattr(rating.probability, 'value') else str(rating.probability)
                                cat_name = rating.category.name if hasattr(rating.category, 'name') else str(rating.category)
                                logger.warning(f"  Safety rating: {cat_name}: {prob_name} ({prob_value})")
                                # Check if probability is NEGLIGIBLE (value 1) or LOW (value 2)
                                if prob_value > 2:  # MEDIUM (3) or HIGH (4)
                                    all_negligible = False
                                    logger.error(f"    ^ High risk detected in {cat_name}")
                        else:
                            logger.warning("  No safety ratings available (empty array)")
                            # If ratings are empty, assume it's not a high-risk block
                            all_negligible = True
                        
                        # Force extract content even if blocked - try ALL possible methods
                        content_extracted = False
                        text = None
                        
                        # Method 1: Try candidate.content.parts
                        if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                            parts_text = []
                            for part in candidate.content.parts:
                                if hasattr(part, 'text') and part.text:
                                    parts_text.append(part.text)
                                # Also try accessing part directly
                                try:
                                    part_str = str(part)
                                    if part_str and part_str not in parts_text:
                                        parts_text.append(part_str)
                                except:
                                    pass
                            if parts_text:
                                text = ' '.join(parts_text).strip()
                                content_extracted = True
                                logger.info(f"Extracted content via candidate.content.parts ({len(text)} chars)")
                        
                        # Method 2: Force access response.text (catch ValueError and try anyway)
                        if not content_extracted:
                            try:
                                if hasattr(response, 'text'):
                                    text = response.text.strip()
                                    if text:
                                        content_extracted = True
                                        logger.info(f"Extracted content via response.text ({len(text)} chars)")
                            except ValueError as e:
                                # Even if it raises ValueError, try to get the text anyway
                                logger.warning(f"response.text raised ValueError, but trying to force access: {e}")
                                try:
                                    # Try to access the underlying text via _raw_response
                                    if hasattr(response, '_raw_response'):
                                        raw = response._raw_response
                                        if hasattr(raw, 'candidates') and len(raw.candidates) > 0:
                                            cand = raw.candidates[0]
                                            if hasattr(cand, 'content') and hasattr(cand.content, 'parts'):
                                                for part in cand.content.parts:
                                                    if hasattr(part, 'text'):
                                                        text = part.text.strip()
                                                        if text:
                                                            content_extracted = True
                                                            logger.info(f"Force extracted content via _raw_response ({len(text)} chars)")
                                                            break
                                    # Also try accessing candidate directly
                                    if not content_extracted and hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                                        for part in candidate.content.parts:
                                            # Try to get text even if it says it's blocked
                                            try:
                                                part_text = part.text
                                                if part_text:
                                                    text = part_text.strip()
                                                    content_extracted = True
                                                    logger.info(f"Force extracted via direct part.text access ({len(text)} chars)")
                                                    break
                                            except:
                                                # Try alternative access
                                                try:
                                                    part_dict = part.to_dict() if hasattr(part, 'to_dict') else {}
                                                    if 'text' in part_dict:
                                                        text = part_dict['text'].strip()
                                                        content_extracted = True
                                                        logger.info(f"Force extracted via part.to_dict() ({len(text)} chars)")
                                                        break
                                                except:
                                                    pass
                                except Exception as e2:
                                    logger.debug(f"Force extraction failed: {e2}")
                            except Exception as e:
                                logger.debug(f"Could not access response.text: {e}")
                        
                        # Method 3: Try to get text from response object directly
                        if not content_extracted:
                            try:
                                # Try accessing response.parts directly
                                if hasattr(response, 'parts'):
                                    parts_text = []
                                    for part in response.parts:
                                        if hasattr(part, 'text'):
                                            parts_text.append(part.text)
                                    if parts_text:
                                        text = ' '.join(parts_text).strip()
                                        content_extracted = True
                                        logger.info(f"Extracted content via response.parts ({len(text)} chars)")
                            except Exception as e:
                                logger.debug(f"Could not access response.parts: {e}")
                        
                        # If we still couldn't extract, try to bypass the safety check entirely
                        if not content_extracted:
                            # Last resort: try to get ANY text from the response object
                            logger.warning("All extraction methods failed, trying final bypass attempt...")
                            try:
                                # Try to serialize the response and extract text from it
                                import json as json_module
                                response_str = str(response)
                                response_dict = response.__dict__ if hasattr(response, '__dict__') else {}
                                
                                # Try to find text in the response structure
                                def find_text_in_obj(obj, depth=0):
                                    if depth > 5:  # Limit recursion
                                        return None
                                    if isinstance(obj, str) and len(obj) > 50:
                                        # Looks like content
                                        if '{' in obj and '}' in obj:  # Might be JSON
                                            return obj
                                    if isinstance(obj, dict):
                                        for v in obj.values():
                                            result = find_text_in_obj(v, depth+1)
                                            if result:
                                                return result
                                    if isinstance(obj, (list, tuple)):
                                        for item in obj:
                                            result = find_text_in_obj(item, depth+1)
                                            if result:
                                                return result
                                    return None
                                
                                found_text = find_text_in_obj(response_dict)
                                if found_text:
                                    text = found_text
                                    content_extracted = True
                                    logger.info(f"Found text via deep search ({len(text)} chars)")
                            except Exception as e:
                                logger.debug(f"Deep search failed: {e}")
                        
                        # Final check - if still no content, check if it's a prompt issue
                        if not content_extracted:
                            logger.error("CRITICAL: Gemini blocked response but no content available")
                            logger.error(f"finish_reason: SAFETY, safety_ratings_empty: {safety_ratings_empty}, all_negligible: {all_negligible}")
                            
                            # If no safety ratings, the prompt itself might be triggering filters
                            if safety_ratings_empty:
                                logger.error("Empty safety ratings suggest the prompt content may be triggering safety filters")
                                logger.error("This might be due to champion names, game terminology, or prompt structure")
                                raise GeminiError("Gemini blocked response - prompt content may be triggering safety filters. Try simplifying the prompt or checking if specific champion names are causing issues.")
                            elif all_negligible:
                                logger.error("All ratings NEGLIGIBLE but still blocked - this is a Gemini API limitation")
                                raise GeminiError("Gemini API is blocking responses despite NEGLIGIBLE safety ratings. This is a known Gemini API limitation with JSON mode.")
                            else:
                                raise GeminiError("Gemini response blocked by safety filters (finish_reason: SAFETY) - high-risk content detected")
                        else:
                            # Successfully extracted content
                            logger.info(f"Successfully extracted content from blocked response ({len(text)} chars)")
                    elif finish_reason == 1:  # STOP (normal completion)
                        logger.info("Gemini response completed normally (STOP)")
                        # Normal completion, proceed with text extraction
                        text = response.text.strip()
                        logger.debug(f"Gemini response text length: {len(text)}")
                    else:
                        logger.warning(f"Gemini response has finish_reason: {finish_reason}")
                        # Other finish reasons (RECITATION, MAX_TOKENS, etc.)
                        if hasattr(response, 'text'):
                            text = response.text.strip()
                            logger.debug(f"Gemini response text length: {len(text)}")
                        else:
                            raise GeminiError(f"Gemini response has unexpected finish_reason: {finish_reason}, no text available")
                else:
                    logger.warning("Gemini response has no candidates, trying text attribute")
                    # Fallback to text attribute
                    if not hasattr(response, 'text'):
                        raise GeminiError("Gemini response has no text attribute or candidates")
                    
                    # Try to access text (will raise ValueError if blocked)
                    text = response.text.strip()
                    logger.debug(f"Gemini response text length: {len(text)}")
            except ValueError as e:
                # Safety block or empty response
                logger.error(f"Gemini ValueError: {e}")
                if "finish_reason" in str(e) or "no valid Part" in str(e):
                    raise GeminiError(f"Gemini response blocked or empty: {str(e)}")
                raise GeminiError(f"Gemini response error: {str(e)}")
            
            if not text:
                raise GeminiError("Gemini returned empty response")
            
            # Clean up any markdown code fences or extra whitespace
            # Since we're not using JSON mode, Gemini might wrap the response in code fences
            if text.startswith("```json"):
                text = text[7:]
            elif text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()
            
            # Try to find JSON object in the response (in case there's extra text before/after)
            # This is important since we're not using JSON mode
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
                logger.error(f"Response text (first 500 chars): {text[:500]}")
                raise GeminiError(f"Invalid JSON response from Gemini: {e}")
                
        except GeminiError:
            raise
        except Exception as e:
            logger.error(f"Gemini API call failed: {e}", exc_info=True)
            raise GeminiError(f"Gemini API error: {str(e)}")
    
    async def _call_gemini_async(self, model, prompt: str, safety_settings=None):
        """Helper to run sync Gemini call in async context (same as patchnote_featurizer)"""
        import asyncio
        
        # Run in executor since genai is sync
        loop = asyncio.get_event_loop()
        
        # Generate content (same as patchnote_featurizer - no safety_settings parameter)
        def _generate():
            logger.info("Gemini calling generate_content (no safety_settings, matching patchnote_featurizer)")
            result = model.generate_content(prompt)
            logger.info(f"Gemini generate_content result type: {type(result)}")
            return result
        
        return await loop.run_in_executor(None, _generate)


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

