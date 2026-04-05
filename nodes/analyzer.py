"""
nodes/analyzer.py - Industrial Safety Video Analysis using Gemini 1.5 Pro Vision.

Analyzes extracted frames using the Gemini vision model to detect safety violations,
PPE compliance issues, and hazardous work practices in industrial environments.
"""

import logging
import json
import time
from typing import Dict, Any, Optional, List

try:
    import google.generativeai as genai
    from google.api_core.exceptions import ResourceExhausted, ServiceUnavailable
except ImportError:
    genai = None  # type: ignore
    ResourceExhausted = None  # type: ignore
    ServiceUnavailable = None  # type: ignore

from config import Config
from schema import AuditState, AnalysisResult

logger = logging.getLogger(__name__)

# Rate limit retry configuration
MAX_RETRIES = 3
INITIAL_RETRY_DELAY_SEC = 2
BACKOFF_MULTIPLIER = 2.0


INDUSTRIAL_SAFETY_SYSTEM_PROMPT = """
You are an expert Industrial Safety Auditor with 20+ years of experience in OSHA compliance,
workplace safety standards, and hazard assessment. Your role is to analyze video frames
from industrial work environments and identify potential safety violations and risks.

SAFETY FOCUS AREAS:
1. **Personal Protective Equipment (PPE):**
   - Hard hats/safety helmets (required in most facilities)
   - Safety glasses or face shields
   - High-visibility vests or clothing
   - Gloves (chemical resistant, cut resistant, etc.)
   - Safety footwear (steel-toed boots)
   - Respirators or breathing protection where applicable
   - Hearing protection

2. **Dangerous Tool & Equipment Handling:**
   - Improper use of power tools
   - Missing machine guards
   - Unsafe ladder positioning or use
   - Improper lifting techniques
   - Unsecured heavy equipment or materials
   - Inadequate tool storage

3. **Workspace Hazards:**
   - Cluttered or messy work areas
   - Trip hazards (cables, debris, liquids)
   - Poor lighting conditions
   - Lack of proper signage or barriers
   - Blocked emergency exits
   - Chemical or material spills

4. **Work Practices:**
   - Workers working alone in hazardous areas
   - Improper scaffolding or elevated work setup
   - Confined space entries without safety protocols
   - Non-compliance with lockout/tagout procedures

ANALYSIS REQUIREMENTS:
- Be specific about what safety violations or risks you observe
- Rate severity as 'CRITICAL', 'HIGH', 'MEDIUM', or 'LOW'
- Confidence scores should reflect your certainty (0-100%)
- Provide actionable recommendations for each violation
- If no violations are found, clearly state that

RESPONSE FORMAT (STRICT JSON):
{
  "frame_analysis": {
    "safety_violations": [
      {
        "violation_type": "PPE|TOOL_HANDLING|WORKSPACE_HAZARD|WORK_PRACTICE|OTHER",
        "description": "Specific violation description",
        "severity": "CRITICAL|HIGH|MEDIUM|LOW",
        "confidence": 0-100,
        "recommendation": "Action to remediate this violation"
      }
    ],
    "ppe_compliance": {
      "helmet": "present|missing|uncertain",
      "eyewear": "present|missing|uncertain",
      "gloves": "present|missing|uncertain",
      "footwear": "safe|unsafe|uncertain",
      "other_ppe": "description or none"
    },
    "overall_safety_rating": 0-100,
    "safety_assessment": "Safe|Minor Issues|Significant Issues|Critical Issues",
    "summary": "2-3 sentence summary of overall safety status"
  }
}

Respond ONLY with valid JSON. No preamble or explanation.
"""


def initialize_genai() -> bool:
    """
    Initialize Google Generative AI client.
    
    Returns:
        True if initialization successful, False otherwise
    """
    try:
        if not genai:
            logger.error("google-generativeai package is not installed")
            return False
        
        genai.configure(api_key=Config.GEMINI_API_KEY)
        logger.info("Google Generative AI client initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize Google Generative AI: {str(e)}")
        return False


class VisionAnalyzer:
    """
    Industrial safety analyzer using Gemini 1.5 Pro Vision API.
    
    Analyzes video frames for safety violations, PPE compliance, and hazardous
    work practices with built-in retry logic for API rate limits.
    """
    
    def __init__(self) -> None:
        """Initialize the VisionAnalyzer."""
        self.model = genai.GenerativeModel(
            model_name=Config.GEMINI_MODEL,
            system_instruction=INDUSTRIAL_SAFETY_SYSTEM_PROMPT
        )
        self.max_retries = MAX_RETRIES
        self.initial_delay = INITIAL_RETRY_DELAY_SEC
    
    def analyze_frame_with_retry(
        self,
        frame_base64: str,
        frame_index: int,
        max_attempts: int = MAX_RETRIES
    ) -> Optional[Dict[str, Any]]:
        """
        Analyze a single base64-encoded frame with automatic retry on rate limits.
        
        Implements exponential backoff retry mechanism for API rate limiting scenarios.
        
        Args:
            frame_base64: Base64-encoded JPEG frame
            frame_index: Index of the frame (for logging)
            max_attempts: Maximum number of retry attempts
            
        Returns:
            Parsed JSON analysis result or None if all attempts fail
        """
        retry_delay = self.initial_delay
        last_error = None
        
        for attempt in range(max_attempts):
            try:
                logger.debug(f"Analyzing frame {frame_index} (attempt {attempt + 1}/{max_attempts})")
                
                # Create request with base64 frame
                response = self.model.generate_content(
                    [
                        {
                            "mime_type": "image/jpeg",
                            "data": frame_base64
                        }
                    ]
                )
                
                # Parse response text as JSON
                analysis_text = response.text.strip()
                
                # Try to parse JSON response
                try:
                    analysis_json = json.loads(analysis_text)
                    logger.debug(f"Successfully analyzed frame {frame_index}")
                    return analysis_json
                
                except json.JSONDecodeError as e:
                    logger.warning(
                        f"Response for frame {frame_index} was not valid JSON: {str(e)[:100]}"
                    )
                    # Try to extract JSON from response if it contains extra text
                    try:
                        json_start = analysis_text.find("{")
                        json_end = analysis_text.rfind("}") + 1
                        if json_start >= 0 and json_end > json_start:
                            extracted_json = analysis_text[json_start:json_end]
                            analysis_json = json.loads(extracted_json)
                            logger.debug(f"Extracted JSON from frame {frame_index}")
                            return analysis_json
                    except (ValueError, json.JSONDecodeError):
                        pass
                    
                    # Create fallback response
                    logger.warning(f"Using fallback response for frame {frame_index}")
                    return {
                        "frame_analysis": {
                            "safety_violations": [],
                            "ppe_compliance": {
                                "helmet": "uncertain",
                                "eyewear": "uncertain",
                                "gloves": "uncertain",
                                "footwear": "uncertain",
                                "other_ppe": "Analysis unavailable"
                            },
                            "overall_safety_rating": 0,
                            "safety_assessment": "Analysis Error",
                            "summary": f"Unable to parse structured response for frame {frame_index}"
                        }
                    }
            
            except Exception as e:
                last_error = e
                error_type = type(e).__name__
                
                # Check if this is a rate limit error
                is_rate_limit = (
                    "429" in str(e) or 
                    "rate" in str(e).lower() or
                    "quota" in str(e).lower() or
                    (ResourceExhausted and isinstance(e, ResourceExhausted))
                )
                
                if is_rate_limit and attempt < max_attempts - 1:
                    logger.warning(
                        f"Rate limit hit on frame {frame_index} (attempt {attempt + 1}). "
                        f"Retrying in {retry_delay:.1f}s..."
                    )
                    time.sleep(retry_delay)
                    retry_delay *= BACKOFF_MULTIPLIER
                    continue
                
                elif error_type == "ServiceUnavailable" and attempt < max_attempts - 1:
                    logger.warning(
                        f"Service unavailable for frame {frame_index} (attempt {attempt + 1}). "
                        f"Retrying in {retry_delay:.1f}s..."
                    )
                    time.sleep(retry_delay)
                    retry_delay *= BACKOFF_MULTIPLIER
                    continue
                
                else:
                    logger.error(
                        f"Error analyzing frame {frame_index} on attempt {attempt + 1}: {str(e)}"
                    )
                    if attempt == max_attempts - 1:
                        logger.error(f"All {max_attempts} attempts failed for frame {frame_index}")
                    continue
        
        logger.error(
            f"Failed to analyze frame {frame_index} after {max_attempts} attempts: {str(last_error)}"
        )
        return None
    
    def extract_violations_from_analysis(self, analysis: Dict[str, Any]) -> List[str]:
        """
        Extract violation descriptions from analysis result.
        
        Args:
            analysis: Parsed analysis JSON result
            
        Returns:
            List of violation descriptions
        """
        violations = []
        
        try:
            frame_analysis = analysis.get("frame_analysis", {})
            safety_violations = frame_analysis.get("safety_violations", [])
            
            for violation in safety_violations:
                violation_type = violation.get("violation_type", "UNKNOWN")
                description = violation.get("description", "No description")
                severity = violation.get("severity", "UNKNOWN")
                
                violation_msg = f"[{severity}] {violation_type}: {description}"
                violations.append(violation_msg)
        
        except (KeyError, TypeError) as e:
            logger.warning(f"Error extracting violations from analysis: {str(e)}")
        
        return violations


def analyze_frames(state: AuditState) -> AuditState:
    """
    Analyze extracted frames for industrial safety violations.
    
    Uses Gemini 1.5 Pro vision with industrial safety system prompt to detect
    PPE violations, dangerous tool handling, and workspace hazards.
    
    Args:
        state: Current AuditState containing base64-encoded frames
        
    Returns:
        Updated AuditState with analysis results and detected violations
    """
    logger.info(f"Starting industrial safety analysis of {len(state['frames'])} frames")
    
    if not state["frames"]:
        logger.warning("No frames available for analysis")
        state["analysis_results"] = []
        state["violations"] = []
        return state
    
    if not initialize_genai():
        error_msg = "Failed to initialize Gemini API client"
        logger.error(error_msg)
        state["errors"].append(error_msg)
        return state
    
    try:
        analyzer = VisionAnalyzer()
        analysis_results: List[AnalysisResult] = []
        violations: List[str] = []
        
        # Analyze sample frames (first, middle, last, plus evenly spaced frames)
        sample_indices = get_representative_frames(len(state["frames"]))
        
        logger.info(
            f"Analyzing {len(sample_indices)} representative frames "
            f"from {len(state['frames'])} total frames"
        )
        
        for frame_count, frame_idx in enumerate(sample_indices, 1):
            frame_b64 = state["frames"][frame_idx]
            
            # Analyze frame with retry logic
            analysis = analyzer.analyze_frame_with_retry(frame_b64, frame_idx)
            
            if analysis is None:
                error_msg = f"Failed to analyze frame {frame_idx} after retries"
                logger.warning(error_msg)
                state["errors"].append(error_msg)
                continue
            
            # Extract timestamp estimate (0-100% through video)
            timestamp_estimate = (frame_idx / max(len(state["frames"]), 1)) * 100.0
            
            # Create analysis result
            try:
                frame_analysis = analysis.get("frame_analysis", {})
                summary = frame_analysis.get("summary", "No summary available")
                
                result: AnalysisResult = AnalysisResult(
                    timestamp=timestamp_estimate,
                    description=summary
                )
                analysis_results.append(result)
                
                # Extract violations
                frame_violations = analyzer.extract_violations_from_analysis(analysis)
                violations.extend(frame_violations)
                
                safety_rating = frame_analysis.get("overall_safety_rating", 0)
                assessment = frame_analysis.get("safety_assessment", "Unknown")
                
                logger.info(
                    f"Frame {frame_idx} ({frame_count}/{len(sample_indices)}) - "
                    f"Safety: {assessment} (rating: {safety_rating}/100), "
                    f"Violations: {len(frame_violations)}"
                )
            
            except (KeyError, TypeError) as e:
                logger.warning(f"Error processing analysis for frame {frame_idx}: {str(e)}")
                continue
        
        state["analysis_results"] = analysis_results
        state["violations"] = violations
        
        logger.info(
            f"Analysis complete: {len(analysis_results)} frames analyzed, "
            f"{len(violations)} safety violations detected"
        )
    
    except Exception as e:
        error_msg = f"Error during industrial safety analysis: {str(e)}"
        logger.error(error_msg, exc_info=True)
        state["errors"].append(error_msg)
    
    return state


def get_representative_frames(total_frames: int, target_count: int = 5) -> List[int]:
    """
    Select representative frames for analysis.
    
    Uses a stratified sampling approach to ensure good video coverage.
    
    Args:
        total_frames: Total number of frames available
        target_count: Target number of frames to analyze
        
    Returns:
        List of frame indices to analyze
    """
    if total_frames == 0:
        return []
    
    if total_frames <= target_count:
        return list(range(total_frames))
    
    # Start with first, middle, and last
    indices = set([0, total_frames // 2, total_frames - 1])
    
    # Add evenly spaced frames to reach target_count
    if len(indices) < target_count:
        step = total_frames // (target_count - 1)
        for i in range(target_count):
            indices.add(min(i * step, total_frames - 1))
    
    return sorted(list(indices))[:target_count]
