"""
schema.py - Defines the AuditState TypedDict for the Sentinel-Vision agent.

This module contains all type definitions used throughout the agent workflow,
ensuring type safety and consistency across all nodes.
"""

from typing import TypedDict, Optional, List, Dict, Any


class AnalysisResult(TypedDict):
    """
    Individual frame analysis result.
    
    Attributes:
        timestamp: Time in seconds where this analysis applies
        description: Textual description of the analysis findings
    """
    timestamp: float
    description: str


class AuditState(TypedDict):
    """
    State object representing the complete audit workflow state.
    
    Represents the entire audit workflow pipeline, tracking video processing
    from extraction through analysis to final report generation.
    
    Attributes:
        video_path: Absolute path to the input video file for analysis
        frames: List of base64-encoded frame strings extracted from the video
        analysis_results: List of analysis dictionaries containing timestamp and description
        violations: List of detected violations or policy breaches during analysis
        report_path: File path where the final audit report is saved
        errors: List of error messages encountered during processing
    """
    video_path: str
    frames: List[str]
    analysis_results: List[AnalysisResult]
    violations: List[str]
    report_path: Optional[str]
    errors: List[str]
