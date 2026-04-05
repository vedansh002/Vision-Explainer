"""
main.py - Entry point for the Sentinel-Vision audit agent.

Usage:
    python main.py <video_path>
    
Example:
    python main.py ./videos/sample.mp4
"""

import logging
import logging.handlers
import sys
import argparse
from pathlib import Path
from typing import Optional, Dict, Any

from config import Config
from schema import AuditState
from graph import initialize_graph, get_compiled_graph

# Configure logging
def setup_logging() -> None:
    """Setup logging configuration for the application."""
    log_dir = Path(Config.LOG_DIR)
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Create logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, Config.LOG_LEVEL))
    
    # File handler
    file_handler = logging.handlers.RotatingFileHandler(
        log_dir / "sentinel_vision.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_formatter = logging.Formatter(
        "%(levelname)s - %(name)s - %(message)s"
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    logging.getLogger(__name__).info("Logging configured successfully")


def create_initial_state(video_path: str) -> AuditState:
    """
    Create the initial AuditState for workflow execution.
    
    Args:
        video_path: Path to the video file to audit
        
    Returns:
        Initial AuditState dictionary
    """
    return AuditState(
        video_path=video_path,
        frames=[],
        analysis_results=[],
        violations=[],
        report_path=None,
        errors=[]
    )


def validate_inputs(video_path: str) -> bool:
    """
    Validate input parameters.
    
    Args:
        video_path: Path to video file
        
    Returns:
        True if inputs are valid
        
    Raises:
        ValueError: If inputs are invalid
    """
    if not video_path:
        raise ValueError("Video path cannot be empty")
    
    video_file = Path(video_path)
    if not video_file.exists():
        raise ValueError(f"Video file not found: {video_path}")
    
    if not video_file.is_file():
        raise ValueError(f"Video path is not a file: {video_path}")
    
    # Check file extension
    valid_extensions = {".mp4", ".avi", ".mov", ".mkv", ".flv", ".wmv"}
    if video_file.suffix.lower() not in valid_extensions:
        raise ValueError(
            f"Invalid video format: {video_file.suffix}. "
            f"Supported formats: {', '.join(valid_extensions)}"
        )
    
    return True


def run_agent(video_path: str) -> Optional[Dict[str, Any]]:
    """
    Run the Sentinel-Vision audit agent on a video file.
    
    Args:
        video_path: Path to the video file to audit
        
    Returns:
        Final AuditState if successful, None otherwise
    """
    logger = logging.getLogger(__name__)
    
    try:
        # Validate inputs
        logger.info(f"Validating input video: {video_path}")
        validate_inputs(video_path)
        logger.info("Input validation passed")
        
        # Load and validate configuration
        logger.info("Loading configuration from environment")
        config = Config.from_env()
        logger.info("Configuration loaded and validated successfully")
        logger.debug(f"Active config: {config.to_dict()}")
        
        # Initialize graph
        logger.info("Initializing workflow graph")
        graph = initialize_graph()
        if not graph:
            logger.error("Failed to initialize workflow graph")
            return None
        
        # Compile graph
        compiled_graph = get_compiled_graph(graph)
        if not compiled_graph:
            logger.error("Failed to compile workflow graph")
            return None
        
        # Create initial state
        logger.info(f"Creating initial state for video: {video_path}")
        initial_state = create_initial_state(video_path)
        
        # Execute graph
        logger.info("Starting workflow execution")
        final_state = compiled_graph.invoke(initial_state)
        
        # Check for errors
        if final_state.get("errors"):
            logger.warning(f"Workflow completed with {len(final_state['errors'])} error(s):")
            for error in final_state["errors"]:
                logger.warning(f"  - {error}")
        else:
            logger.info("Workflow completed successfully")
        
        # Log results
        if final_state.get("report_path"):
            logger.info(f"Report generated: {final_state['report_path']}")
        
        return final_state
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Workflow execution failed: {str(e)}", exc_info=True)
        return None


def main() -> int:
    """
    Main entry point for the Sentinel-Vision agent.
    
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    # Setup logging first
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 80)
    logger.info("Sentinel-Vision Audit Agent Starting")
    logger.info("=" * 80)
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Sentinel-Vision: AI-powered video audit agent using LangGraph and Gemini"
    )
    parser.add_argument(
        "video_path",
        type=str,
        help="Path to the video file to audit"
    )
    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level (default: INFO)"
    )
    
    try:
        args = parser.parse_args()
    except SystemExit as e:
        return 1
    
    # Update log level if specified
    if args.log_level:
        logging.getLogger().setLevel(getattr(logging, args.log_level))
        logger.info(f"Log level set to: {args.log_level}")
    
    # Run agent
    logger.info(f"Processing video: {args.video_path}")
    result = run_agent(args.video_path)
    
    if result:
        logger.info("Agent execution completed successfully")
        return 0
    else:
        logger.error("Agent execution failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
