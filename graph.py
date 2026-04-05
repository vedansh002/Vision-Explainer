"""
graph.py - LangGraph StateGraph initialization with advanced agentic routing.

Defines the workflow graph for the Sentinel-Vision agent using LangGraph
with conditional edges for intelligent routing based on risk assessment.
"""

import logging
from typing import Optional, Any, Literal

try:
    from langgraph.graph import StateGraph, END
except ImportError:
    StateGraph = None  # type: ignore
    END = None  # type: ignore

from schema import AuditState
from nodes import extract_frames, analyze_frames, generate_report

logger = logging.getLogger(__name__)


def _count_high_risk_violations(violations: list) -> int:
    """
    Count high-risk violations in the violations list.
    
    Counts violations marked as CRITICAL or HIGH severity.
    
    Args:
        violations: List of violation strings
        
    Returns:
        Count of high-risk (CRITICAL or HIGH) violations
    """
    high_risk_count = 0
    for violation in violations:
        if "[CRITICAL]" in violation or "[HIGH]" in violation:
            high_risk_count += 1
    return high_risk_count


def alert_on_high_risk(state: AuditState) -> AuditState:
    """
    Alert node that triggers when high-risk violations are detected.
    
    This node logs a critical alert when more than 3 high-risk violations
    are found during analysis. In production, this could trigger webhooks,
    send emails, or escalate to management systems.
    
    Args:
        state: Current AuditState containing violations list
        
    Returns:
        Unchanged AuditState (pass-through node)
    """
    high_risk_violations = _count_high_risk_violations(state["violations"])
    
    alert_msg = (
        f"🚨 HIGH-RISK SAFETY ALERT 🚨\n"
        f"Detected {high_risk_violations} high-risk violations in video analysis!\n"
        f"Total violations: {len(state['violations'])}\n"
        f"Immediate investigation recommended."
    )
    
    logger.critical(alert_msg)
    
    # In production, you could:
    # - Send Slack/Teams notification
    # - Post to monitoring system
    # - Trigger escalation workflow
    # - Send email to safety manager
    
    return state


def route_to_alert_or_report(state: AuditState) -> Literal["alert", "report"]:
    """
    Conditional routing function for advanced agentic decision-making.
    
    Routes to alert node if more than 3 high-risk violations detected,
    otherwise routes directly to report generation.
    
    This demonstrates LangGraph's conditional edge capability for
    intelligent workflow routing based on state assessment.
    
    Args:
        state: Current AuditState containing violations list
        
    Returns:
        "alert" if high-risk violations > 3, else "report"
    """
    high_risk_count = _count_high_risk_violations(state["violations"])
    
    logger.debug(f"Conditional routing: high-risk violations = {high_risk_count}")
    
    if high_risk_count > 3:
        logger.info(
            f"Routing to alert node: {high_risk_count} high-risk violations detected "
            f"(threshold: 3)"
        )
        return "alert"
    else:
        logger.info(
            f"Routing to report node: {high_risk_count} high-risk violations "
            f"(within acceptable threshold)"
        )
        return "report"


def initialize_graph() -> Optional[StateGraph]:
    """
    Initialize the LangGraph StateGraph with advanced conditional routing.
    
    The workflow implements the following DAG:
    
    START -> extract -> analyze -> [conditional] -> alert -> report -> END
                                 \                         /
                                  \-> (if low risk) -> report
    
    Conditional routing:
    - If analyzer finds > 3 high-risk violations: route through alert node
    - Otherwise: proceed directly to report generation
    
    Returns:
        Initialized StateGraph or None if initialization fails
        
    Raises:
        ImportError: If langgraph is not installed
    """
    try:
        if not StateGraph or not END:
            logger.error("langgraph package is not installed")
            raise ImportError("langgraph not found - required for graph initialization")
        
        logger.info("Initializing LangGraph StateGraph with conditional routing")
        
        # Create state graph
        graph: StateGraph = StateGraph(AuditState)
        
        # ===== Add Nodes =====
        logger.debug("Adding workflow nodes to graph")
        
        graph.add_node("extract", extract_frames)
        logger.debug("  ✓ Added 'extract' node (frame extraction)")
        
        graph.add_node("analyze", analyze_frames)
        logger.debug("  ✓ Added 'analyze' node (safety analysis)")
        
        graph.add_node("alert", alert_on_high_risk)
        logger.debug("  ✓ Added 'alert' node (high-risk violation escalation)")
        
        graph.add_node("report", generate_report)
        logger.debug("  ✓ Added 'report' node (PDF report generation)")
        
        # ===== Define Edges =====
        logger.debug("Defining workflow edges and routing")
        
        # Linear edges
        graph.add_edge("extract", "analyze")
        logger.debug("  ✓ Edge: extract -> analyze")
        
        # Conditional edge (the advanced routing)
        graph.add_conditional_edges(
            "analyze",
            route_to_alert_or_report,
            {
                "alert": "alert",
                "report": "report"
            }
        )
        logger.debug("  ✓ Conditional edge: analyze -> [alert|report]")
        
        # Alert to report (always proceeds to report after alert)
        graph.add_edge("alert", "report")
        logger.debug("  ✓ Edge: alert -> report")
        
        # Report to end
        graph.add_edge("report", END)
        logger.debug("  ✓ Edge: report -> END")
        
        # ===== Set Entry/Exit Points =====
        graph.set_entry_point("extract")
        logger.debug("  ✓ Entry point: extract")
        
        logger.info("LangGraph StateGraph initialized successfully")
        logger.info(
            "Graph structure: START -> extract -> analyze -> [alert|report] -> END"
        )
        logger.info("Routing logic: High-risk violations (>3) trigger alert node")
        
        return graph
        
    except Exception as e:
        logger.error(f"Failed to initialize StateGraph: {str(e)}", exc_info=True)
        raise


def get_compiled_graph(graph: StateGraph) -> Optional[Any]:
    """
    Compile the StateGraph for execution.
    
    Compiling optimizes the graph structure and enables execution
    in the LangGraph runtime.
    
    Args:
        graph: The StateGraph to compile
        
    Returns:
        Compiled graph or None if compilation fails
    """
    try:
        logger.info("Compiling StateGraph for execution")
        compiled_graph = graph.compile()
        logger.info("StateGraph compiled successfully and ready for invocation")
        return compiled_graph
    except Exception as e:
        logger.error(f"Failed to compile StateGraph: {str(e)}", exc_info=True)
        return None
