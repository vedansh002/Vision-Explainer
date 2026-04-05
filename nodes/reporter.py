"""
nodes/reporter.py - Professional PDF Report Generation using ReportLab.

Generates comprehensive industrial safety audit reports with professional
formatting, violation tables, summaries, and detailed non-conformances.
"""

import logging
from pathlib import Path
from typing import Optional, List, Tuple, Dict, Any
from datetime import datetime
import io

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak,
        KeepTogether
    )
    from reportlab.pdfgen import canvas
except ImportError:
    reportlab = None  # type: ignore

from config import Config
from schema import AuditState

logger = logging.getLogger(__name__)


class PDFReporter:
    """
    Professional PDF report generator for industrial safety audits.
    
    Creates comprehensive reports with headers, summaries, violation tables,
    analysis results, and professional footers.
    """
    
    # Color palette
    COLOR_BRAND_DARK = colors.HexColor("#1f4788")
    COLOR_BRAND_LIGHT = colors.HexColor("#2c5aa0")
    COLOR_CRITICAL = colors.HexColor("#d32f2f")
    COLOR_HIGH = colors.HexColor("#f57c00")
    COLOR_MEDIUM = colors.HexColor("#fbc02d")
    COLOR_LOW = colors.HexColor("#388e3c")
    COLOR_HEADER_BG = colors.HexColor("#1a237e")
    COLOR_HEADER_TEXT = colors.white
    
    def __init__(self, report_path: Path) -> None:
        """
        Initialize the PDF reporter.
        
        Args:
            report_path: Path where the PDF will be saved
        """
        self.report_path = report_path
        self.doc = SimpleDocTemplate(
            str(report_path),
            pagesize=letter,
            rightMargin=0.75 * inch,
            leftMargin=0.75 * inch,
            topMargin=1.0 * inch,
            bottomMargin=0.75 * inch,
            title="Sentinel-Vision Industrial Safety Audit Report"
        )
        self.elements = []
        self.styles = self._create_styles()
    
    def _create_styles(self) -> dict:
        """Create custom paragraph styles for the report."""
        base_styles = getSampleStyleSheet()
        
        custom_styles = {
            "title": ParagraphStyle(
                "CustomTitle",
                parent=base_styles["Heading1"],
                fontSize=28,
                textColor=self.COLOR_BRAND_DARK,
                spaceAfter=6,
                alignment=1,  # Center
                fontName="Helvetica-Bold"
            ),
            "subtitle": ParagraphStyle(
                "CustomSubtitle",
                parent=base_styles["Heading2"],
                fontSize=12,
                textColor=colors.grey,
                spaceAfter=12,
                alignment=1,  # Center
                fontName="Helvetica"
            ),
            "heading": ParagraphStyle(
                "CustomHeading",
                parent=base_styles["Heading2"],
                fontSize=14,
                textColor=self.COLOR_BRAND_LIGHT,
                spaceAfter=10,
                spaceBefore=12,
                fontName="Helvetica-Bold",
                borderColor=self.COLOR_BRAND_LIGHT,
                borderWidth=0.5,
                borderPadding=5
            ),
            "subheading": ParagraphStyle(
                "CustomSubheading",
                parent=base_styles["Heading3"],
                fontSize=11,
                textColor=self.COLOR_BRAND_LIGHT,
                spaceAfter=8,
                spaceBefore=8,
                fontName="Helvetica-Bold"
            ),
            "normal": ParagraphStyle(
                "CustomNormal",
                parent=base_styles["Normal"],
                fontSize=10,
                alignment=4  # Justify
            ),
            "small": ParagraphStyle(
                "CustomSmall",
                parent=base_styles["Normal"],
                fontSize=8,
                alignment=0  # Left
            ),
            "critical": ParagraphStyle(
                "CriticalViolation",
                parent=base_styles["Normal"],
                fontSize=9,
                textColor=self.COLOR_CRITICAL,
                fontName="Helvetica-Bold"
            ),
            "high": ParagraphStyle(
                "HighViolation",
                parent=base_styles["Normal"],
                fontSize=9,
                textColor=self.COLOR_HIGH,
                fontName="Helvetica-Bold"
            ),
            "medium": ParagraphStyle(
                "MediumViolation",
                parent=base_styles["Normal"],
                fontSize=9,
                textColor=self.COLOR_MEDIUM,
                fontName="Helvetica-Bold"
            ),
            "low": ParagraphStyle(
                "LowViolation",
                parent=base_styles["Normal"],
                fontSize=9,
                textColor=self.COLOR_LOW,
                fontName="Helvetica-Bold"
            ),
        }
        return custom_styles
    
    def add_header(self, video_path: str) -> None:
        """Add professional header with title and metadata."""
        # Title
        title = Paragraph("Sentinel-Vision: Industrial Audit Report", self.styles["title"])
        self.elements.append(title)
        
        # Subtitle
        timestamp = datetime.now().strftime("%B %d, %Y at %H:%M:%S")
        subtitle = Paragraph(f"Generated: {timestamp}", self.styles["subtitle"])
        self.elements.append(subtitle)
        
        self.elements.append(Spacer(1, 0.2 * inch))
        
        # Quick info section
        quick_info_data = [
            [
                Paragraph("<b>Video File:</b>", self.styles["small"]),
                Paragraph(str(Path(video_path).name), self.styles["small"])
            ]
        ]
        quick_info_table = Table(quick_info_data, colWidths=[1.5 * inch, 4.5 * inch])
        quick_info_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#eceff1")),
            ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey)
        ]))
        self.elements.append(quick_info_table)
        self.elements.append(Spacer(1, 0.3 * inch))
    
    def add_summary_section(
        self,
        total_frames: int,
        violations_count: int,
        errors_count: int,
        safety_rating: float
    ) -> None:
        """
        Add executive summary section with key metrics.
        
        Args:
            total_frames: Total frames analyzed
            violations_count: Number of violations found
            errors_count: Number of processing errors
            safety_rating: Overall safety rating (0-100)
        """
        heading = Paragraph("Executive Summary", self.styles["heading"])
        self.elements.append(heading)
        
        # Color code the safety rating
        if safety_rating >= 75:
            rating_color = self.COLOR_LOW
            rating_text = "SAFE"
        elif safety_rating >= 50:
            rating_color = self.COLOR_MEDIUM
            rating_text = "CAUTION"
        elif safety_rating >= 25:
            rating_color = self.COLOR_HIGH
            rating_text = "WARNING"
        else:
            rating_color = self.COLOR_CRITICAL
            rating_text = "CRITICAL"
        
        # Summary metrics table
        summary_data = [
            [
                Paragraph("<b>Frames Analyzed</b>", self.styles["small"]),
                Paragraph(str(total_frames), self.styles["small"]),
                Paragraph("<b>Violations Found</b>", self.styles["small"]),
                Paragraph(str(violations_count), self.styles["small"]),
            ],
            [
                Paragraph("<b>Processing Errors</b>", self.styles["small"]),
                Paragraph(str(errors_count), self.styles["small"]),
                Paragraph("<b>Safety Rating</b>", self.styles["small"]),
                Paragraph(
                    f"<font color='#{rating_color.hexval()}'><b>{safety_rating:.0f}%</b></font>",
                    self.styles["small"]
                ),
            ]
        ]
        
        summary_table = Table(summary_data, colWidths=[1.5 * inch, 1.2 * inch, 1.5 * inch, 1.2 * inch])
        summary_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f5f5f5")),
            ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 10),
            ("GRID", (0, 0), (-1, -1), 1, colors.grey)
        ]))
        self.elements.append(summary_table)
        self.elements.append(Spacer(1, 0.3 * inch))
    
    def add_violations_table(self, violations: List[str]) -> None:
        """
        Add structured table of violations with severity and timestamps.
        
        Args:
            violations: List of violation strings
        """
        if not violations:
            heading = Paragraph("Violations", self.styles["heading"])
            self.elements.append(heading)
            no_violations = Paragraph(
                "✓ No safety violations detected during audit.",
                self.styles["normal"]
            )
            self.elements.append(no_violations)
            self.elements.append(Spacer(1, 0.3 * inch))
            return
        
        heading = Paragraph("Identified Violations", self.styles["heading"])
        self.elements.append(heading)
        
        # Parse violations and create table
        table_data = [
            [
                Paragraph("<b>#</b>", self.styles["small"]),
                Paragraph("<b>Severity</b>", self.styles["small"]),
                Paragraph("<b>Type</b>", self.styles["small"]),
                Paragraph("<b>Description</b>", self.styles["small"]),
            ]
        ]
        
        for idx, violation in enumerate(violations, 1):
            # Extract severity from violation string
            severity = "MEDIUM"
            violation_text = violation
            
            if "[CRITICAL]" in violation:
                severity = "CRITICAL"
                violation_text = violation.replace("[CRITICAL] ", "")
            elif "[HIGH]" in violation:
                severity = "HIGH"
                violation_text = violation.replace("[HIGH] ", "")
            elif "[MEDIUM]" in violation:
                severity = "MEDIUM"
                violation_text = violation.replace("[MEDIUM] ", "")
            elif "[LOW]" in violation:
                severity = "LOW"
                violation_text = violation.replace("[LOW] ", "")
            
            # Extract violation type
            violation_type = "Other"
            if "PPE" in violation_text:
                violation_type = "PPE"
            elif "TOOL_HANDLING" in violation_text:
                violation_type = "Tool Handling"
            elif "WORKSPACE_HAZARD" in violation_text:
                violation_type = "Workspace Hazard"
            elif "WORK_PRACTICE" in violation_text:
                violation_type = "Work Practice"
            
            # Truncate long descriptions
            desc = violation_text.split(":", 1)[-1].strip() if ":" in violation_text else violation_text
            if len(desc) > 80:
                desc = desc[:77] + "..."
            
            # Color code severity
            severity_color = self.COLOR_LOW
            if severity == "CRITICAL":
                severity_color = self.COLOR_CRITICAL
            elif severity == "HIGH":
                severity_color = self.COLOR_HIGH
            elif severity == "MEDIUM":
                severity_color = self.COLOR_MEDIUM
            
            table_data.append([
                Paragraph(f"<b>{idx}</b>", self.styles["small"]),
                Paragraph(
                    f"<font color='#{severity_color.hexval()}'><b>{severity}</b></font>",
                    self.styles["small"]
                ),
                Paragraph(violation_type, self.styles["small"]),
                Paragraph(desc, self.styles["small"]),
            ])
        
        violations_table = Table(table_data, colWidths=[0.4 * inch, 1.0 * inch, 1.2 * inch, 3.4 * inch])
        violations_table.setStyle(TableStyle([
            # Header row
            ("BACKGROUND", (0, 0), (-1, 0), self.COLOR_HEADER_BG),
            ("TEXTCOLOR", (0, 0), (-1, 0), self.COLOR_HEADER_TEXT),
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
            ("TOPPADDING", (0, 0), (-1, 0), 12),
            
            # Data rows
            ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#fafafa")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f5f5")]),
            ("TEXTCOLOR", (0, 1), (-1, -1), colors.black),
            ("ALIGN", (0, 1), (0, -1), "CENTER"),
            ("ALIGN", (1, 1), (2, -1), "CENTER"),
            ("ALIGN", (3, 1), (3, -1), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("FONTSIZE", (0, 1), (-1, -1), 8),
            ("TOPPADDING", (0, 1), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 1), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey)
        ]))
        self.elements.append(violations_table)
        self.elements.append(Spacer(1, 0.3 * inch))
    
    def add_analysis_results(self, analysis_results: List[Dict[str, Any]]) -> None:
        """
        Add detailed analysis results section.
        
        Args:
            analysis_results: List of analysis result dictionaries
        """
        if not analysis_results:
            return
        
        heading = Paragraph("Detailed Analysis Results", self.styles["heading"])
        self.elements.append(heading)
        
        for idx, result in enumerate(analysis_results, 1):
            timestamp = result.get("timestamp", 0)
            description = result.get("description", "No description available")
            
            # Truncate if needed
            if len(description) > 300:
                description = description[:297] + "..."
            
            result_para = Paragraph(
                f"<b>Frame {idx} (Position: {timestamp:.1f}% through video):</b><br/>{description}",
                self.styles["normal"]
            )
            self.elements.append(result_para)
            self.elements.append(Spacer(1, 0.15 * inch))
    
    def add_error_section(self, errors: List[str]) -> None:
        """
        Add processing errors section.
        
        Args:
            errors: List of error messages
        """
        if not errors:
            return
        
        self.elements.append(PageBreak())
        
        heading = Paragraph("Processing Errors & Warnings", self.styles["heading"])
        self.elements.append(heading)
        
        for error in errors:
            error_para = Paragraph(f"⚠ {error}", self.styles["small"])
            self.elements.append(error_para)
            self.elements.append(Spacer(1, 0.1 * inch))
    
    def add_footer(self) -> None:
        """Add professional footer to the report."""
        self.elements.append(Spacer(1, 0.4 * inch))
        
        footer_line = Paragraph(
            "<hr width='100%' color='#cccccc'/>",
            self.styles["normal"]
        )
        self.elements.append(footer_line)
        
        self.elements.append(Spacer(1, 0.15 * inch))
        
        footer_text = Paragraph(
            "<i>Generated by Sentinel-Vision AI Agent</i><br/>"
            f"<i>Report saved: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>",
            self.styles["small"]
        )
        self.elements.append(footer_text)
    
    def build(self) -> bool:
        """
        Build and save the PDF report.
        
        Returns:
            True if report generated successfully, False otherwise
        """
        try:
            self.doc.build(self.elements)
            logger.info(f"PDF report successfully generated: {self.report_path}")
            return True
        except Exception as e:
            logger.error(f"Error building PDF report: {str(e)}")
            return False


def generate_report(state: AuditState) -> AuditState:
    """
    Generate a professional PDF report from the audit analysis results.
    
    Creates a comprehensive report including header, summary, violations table,
    analysis results, and footer, then saves it to the outputs directory.
    
    Args:
        state: Current AuditState containing analysis results and violations
        
    Returns:
        Updated AuditState with report_path set
    """
    logger.info("Starting PDF report generation")
    
    try:
        # Check if reportlab is available
        if not reportlab:
            error_msg = "reportlab package not installed - required for PDF generation"
            logger.error(error_msg)
            state["errors"].append(error_msg)
            return state
        
        # Create output directory
        output_dir = Path(Config.OUTPUT_DIR)
        output_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Output directory created/verified: {output_dir}")
        
        # Generate report filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"audit_report_{timestamp}.pdf"
        report_path = output_dir / report_filename
        
        logger.info(f"Generating report: {report_path}")
        
        # Create reporter instance
        reporter = PDFReporter(report_path)
        
        # Add header
        reporter.add_header(state["video_path"])
        
        # Calculate safety rating from violations
        max_safety_rating = 100.0
        violation_penalty = 5.0  # Each violation reduces rating by 5
        safety_rating = max(0, max_safety_rating - (len(state["violations"]) * violation_penalty))
        
        # Add summary section
        reporter.add_summary_section(
            total_frames=len(state["frames"]),
            violations_count=len(state["violations"]),
            errors_count=len(state["errors"]),
            safety_rating=safety_rating
        )
        
        # Add violations table
        reporter.add_violations_table(state["violations"])
        
        # Add detailed analysis results
        reporter.add_analysis_results(state["analysis_results"])
        
        # Add error section if any
        if state["errors"]:
            reporter.add_error_section(state["errors"])
        
        # Add footer
        reporter.add_footer()
        
        # Build PDF
        if not reporter.build():
            error_msg = "Failed to build PDF report"
            logger.error(error_msg)
            state["errors"].append(error_msg)
            state["report_path"] = None
            return state
        
        # Update state with report path
        state["report_path"] = str(report_path)
        logger.info(f"Report successfully saved to: {report_path}")
        
    except Exception as e:
        error_msg = f"Error during PDF report generation: {str(e)}"
        logger.error(error_msg, exc_info=True)
        state["errors"].append(error_msg)
        state["report_path"] = None
    
    return state
