"""
nodes/extractor.py - Video frame extraction node using OpenCV.

Handles extraction of frames from video files for subsequent analysis.
Converts frames to base64-encoded strings for API compatibility.
"""

import logging
import cv2
import base64
from pathlib import Path
from typing import List, Optional
from io import BytesIO
from config import Config
from schema import AuditState

logger = logging.getLogger(__name__)


def frame_to_base64(frame) -> str:
    """
    Convert an OpenCV frame to a base64-encoded JPEG string.
    
    Args:
        frame: OpenCV image frame (numpy array)
        
    Returns:
        Base64-encoded string of the frame
        
    Raises:
        cv2.error: If frame encoding fails
    """
    try:
        _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        frame_bytes = BytesIO(buffer).getvalue()
        return base64.b64encode(frame_bytes).decode("utf-8")
    except cv2.error as e:
        logger.error(f"OpenCV error converting frame to base64: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error converting frame to base64: {str(e)}")
        raise


class FrameExtractor:
    """
    Extracts frames from video files at specified time intervals.
    
    Encapsulates video processing logic with proper error handling for
    missing, corrupted, or inaccessible video files.
    """
    
    def __init__(self, video_path: str) -> None:
        """
        Initialize the FrameExtractor.
        
        Args:
            video_path: Path to the video file to extract frames from
        """
        self.video_path: str = video_path
        self.cap: Optional[cv2.VideoCapture] = None
        self.fps: float = 0.0
        self.frame_count: int = 0
        self.width: int = 0
        self.height: int = 0
    
    def open_video(self) -> bool:
        """
        Open and validate the video file.
        
        Returns:
            True if video opened successfully, False otherwise
            
        Logs specific error messages for missing vs corrupted files.
        """
        video_file = Path(self.video_path)
        
        # Check if file exists
        if not video_file.exists():
            logger.error(f"Video file not found at path: {self.video_path}")
            return False
        
        if not video_file.is_file():
            logger.error(f"Video path is not a file: {self.video_path}")
            return False
        
        try:
            # Attempt to open video with OpenCV
            self.cap = cv2.VideoCapture(self.video_path)
            
            # Check if video opened successfully
            if not self.cap.isOpened():
                logger.error(
                    f"Failed to open video file. The file may be corrupted, "
                    f"in an unsupported format, or inaccessible: {self.video_path}"
                )
                return False
            
            # Extract video properties
            try:
                self.frame_count = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
                self.fps = self.cap.get(cv2.CAP_PROP_FPS)
                self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                
                # Validate properties
                if self.frame_count <= 0 or self.fps <= 0:
                    logger.warning(
                        f"Video file has invalid properties: "
                        f"frame_count={self.frame_count}, fps={self.fps}"
                    )
                
                logger.info(
                    f"Video opened successfully - Frames: {self.frame_count}, "
                    f"FPS: {self.fps:.2f}, Resolution: {self.width}x{self.height}"
                )
                return True
                
            except cv2.error as e:
                logger.error(f"OpenCV error reading video properties: {str(e)}")
                self.cap.release()
                return False
        
        except cv2.error as e:
            logger.error(f"OpenCV error while opening video file: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error opening video file: {str(e)}")
            return False
    
    def extract_frames_at_intervals(self) -> List[str]:
        """
        Extract frames at specified time intervals from the video.
        
        Extracts one frame every config.FRAME_EXTRACTION_INTERVAL seconds
        until max frames limit is reached.
        
        Returns:
            List of base64-encoded frame strings
            
        Raises:
            ValueError: If video is not open
        """
        if not self.cap or not self.cap.isOpened():
            raise ValueError("Video file not opened. Call open_video() first.")
        
        frames: List[str] = []
        extraction_interval_sec: float = Config.FRAME_EXTRACTION_INTERVAL
        frames_to_skip: int = max(1, int(self.fps * extraction_interval_sec))
        
        logger.info(
            f"Extracting frames every {extraction_interval_sec}s "
            f"({frames_to_skip} frame(s) at {self.fps:.2f} FPS)"
        )
        
        frame_idx: int = 0
        extracted_count: int = 0
        
        try:
            while extracted_count < Config.MAX_FRAMES_PER_VIDEO:
                # Read frame
                ret: bool
                frame: any
                ret, frame = self.cap.read()
                
                # End of video
                if not ret:
                    logger.debug(f"End of video reached at frame index: {frame_idx}")
                    break
                
                # Extract frame at specified interval
                if frame_idx % frames_to_skip == 0:
                    try:
                        # Convert to RGB and encode as base64
                        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        frame_base64 = frame_to_base64(frame_rgb)
                        frames.append(frame_base64)
                        
                        timestamp_sec: float = (frame_idx / self.fps) if self.fps > 0 else 0
                        extracted_count += 1
                        
                        logger.debug(
                            f"Extracted frame {extracted_count}: "
                            f"index={frame_idx}, time={timestamp_sec:.2f}s, "
                            f"size={len(frame_base64)} bytes"
                        )
                    
                    except cv2.error as e:
                        error_msg = (
                            f"OpenCV error encoding frame {frame_idx}: {str(e)}. "
                            f"Frame may be corrupted or unreadable."
                        )
                        logger.warning(error_msg)
                        # Continue processing remaining frames
                        continue
                    
                    except Exception as e:
                        error_msg = f"Unexpected error encoding frame {frame_idx}: {str(e)}"
                        logger.warning(error_msg)
                        # Continue processing remaining frames
                        continue
                
                frame_idx += 1
        
        except cv2.error as e:
            logger.error(
                f"OpenCV error during frame extraction at index {frame_idx}: {str(e)}. "
                f"Video may be corrupted."
            )
            # Return frames extracted so far
        
        except Exception as e:
            logger.error(f"Unexpected error during frame extraction: {str(e)}")
            # Return frames extracted so far
        
        finally:
            # Release video capture
            if self.cap:
                self.cap.release()
                logger.debug("Video capture released")
        
        logger.info(f"Frame extraction complete: {extracted_count} frames extracted")
        return frames


def extract_frames(state: AuditState) -> AuditState:
    """
    Extract frames from a video file using OpenCV and encode as base64.
    
    This is the node function that processes the AuditState, extracting frames
    at specified time intervals and storing them as base64-encoded strings.
    
    Args:
        state: Current AuditState containing video_path
        
    Returns:
        Updated AuditState with extracted base64-encoded frames or errors
    """
    logger.info(f"Starting frame extraction from: {state['video_path']}")
    
    video_path: str = state["video_path"]
    extractor = FrameExtractor(video_path)
    
    try:
        # Open the video file
        if not extractor.open_video():
            error_msg = f"Failed to open video file: {video_path}"
            logger.error(error_msg)
            state["errors"].append(error_msg)
            return state
        
        # Extract frames at specified intervals
        frames = extractor.extract_frames_at_intervals()
        state["frames"] = frames
        
        if not frames:
            error_msg = f"No frames could be extracted from video: {video_path}"
            logger.warning(error_msg)
            state["errors"].append(error_msg)
        else:
            logger.info(f"Successfully extracted {len(frames)} frames from video")
    
    except cv2.error as e:
        error_msg = (
            f"OpenCV error during frame extraction from '{video_path}': {str(e)}. "
            f"The video file may be corrupted or in an unsupported format."
        )
        logger.error(error_msg, exc_info=True)
        state["errors"].append(error_msg)
    
    except Exception as e:
        error_msg = f"Unexpected error during frame extraction: {str(e)}"
        logger.error(error_msg, exc_info=True)
        state["errors"].append(error_msg)
    
    return state
