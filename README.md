# Sentinel-Vision: AI-Powered Video Audit Agent

A production-grade video analysis agent leveraging LangGraph, Google Gemini 1.5 Pro Vision API, and OpenCV for intelligent video auditing and reporting.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Sentinel-Vision Agent                 │
└─────────────────────────────────────────────────────────┘
                            │
              ┌─────────────┼─────────────┐
              │             │             │
          Extract       Analyze        Report
         (OpenCV)     (Gemini Vision)   (PDF)
```

### Project Structure

```
sentinel-vision/
├── main.py                 # Entry point
├── config.py              # Configuration management
├── schema.py              # Type definitions (AuditState)
├── graph.py               # LangGraph StateGraph setup
├── nodes/
│   ├── __init__.py
│   ├── extractor.py       # Video frame extraction (OpenCV)
│   ├── analyzer.py        # Frame analysis (Gemini Vision)
│   └── reporter.py        # PDF report generation
├── requirements.txt       # Python dependencies
├── .env.example          # Environment configuration template
└── README.md             # This file
```

## Features

- **Modular Architecture**: Clean separation of concerns with dedicated nodes for extraction, analysis, and reporting
- **Type Safety**: Full Python type hints across all modules
- **Production-Grade Logging**: Rotating file logs and console output using the standard logging module
- **LangGraph Integration**: Sophisticated workflow orchestration with StateGraph
- **Gemini Vision Analysis**: Leverages Google Gemini 1.5 Pro for advanced video understanding
- **PDF Reporting**: Automated generation of professional audit reports
- **Error Handling**: Comprehensive error tracking and logging throughout the workflow

## Installation

### Prerequisites

- Python 3.9+
- Google Cloud Gemini API key
- Virtual environment (recommended)

### Setup

1. **Clone or navigate to the project directory**:
   ```bash
   cd sentinel-vision
   ```

2. **Create and activate a virtual environment**:
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate
   
   # macOS/Linux
   python -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:
   ```bash
   # Copy the example configuration
   cp .env.example .env
   
   # Edit .env and add your Gemini API key
   # GEMINI_API_KEY=your_actual_api_key_here
   ```

## Usage

### Basic Usage

```bash
python main.py <path_to_video>
```

### Examples

```bash
# Analyze a single video
python main.py ./videos/sample.mp4

# With custom log level
python main.py --log-level DEBUG ./videos/sample.mp4

# Verbose processing
python main.py --log-level DEBUG ./path/to/video.mov
```

### Supported Video Formats

- MP4 (.mp4)
- AVI (.avi)
- MOV (.mov)
- Matroska (.mkv)
- Flash Video (.flv)
- Windows Media Video (.wmv)

## Configuration

Edit the `config.py` file or set environment variables to customize behavior:

| Setting | Default | Description |
|---------|---------|-------------|
| `GEMINI_API_KEY` | - | Google Gemini API key (required) |
| `GEMINI_MODEL` | gemini-1.5-pro-vision | Vision model to use |
| `FRAME_EXTRACTION_RATE` | 2 | Extract every Nth frame |
| `MAX_FRAMES_PER_VIDEO` | 300 | Maximum frames to process |
| `OUTPUT_DIR` | ./reports | Directory for PDF reports |
| `LOG_LEVEL` | INFO | Logging verbosity |

## Workflow

1. **Extract**: OpenCV extracts video frames at the configured rate
2. **Analyze**: Gemini Vision API analyzes representative frames
3. **Report**: Results are compiled into a professional PDF report

## Logging

Logs are written to:
- **File**: `./logs/sentinel_vision.log` (rotating, max 10MB per file)
- **Console**: Standard output with formatted messages

Log levels: DEBUG, INFO, WARNING, ERROR

## Output

Reports are generated in the configured output directory (`./reports` by default):
- Filename format: `audit_report_YYYYMMDD_HHMMSS.pdf`
- Includes metadata, analysis results, and any processing errors

## Output

Reports are generated in the configured output directory (`./outputs` by default):
- **Filename format**: `audit_report_YYYYMMDD_HHMMSS.pdf`
- **Contents**: Professional PDF with header, executive summary, violations table, analysis results, and footer
- **Includes**: Safety ratings, violation severity levels, frame-by-frame analysis, and processing errors

## Error Handling

The agent tracks and logs all errors during processing. Errors are:
1. Recorded in the AuditState
2. Written to rotating log files
3. Included in the final audit report

## Type Hints

All functions include complete type hints:
- Function parameters and return types
- TypedDict schemas for state management
- Optional types for nullable values

## Development

### Adding New Nodes

1. Create a new file in `nodes/`
2. Define a function with signature: `def my_node(state: AuditState) -> AuditState:`
3. Add it to the graph in `graph.py`: `graph.add_node("my_node", my_node)`
4. Connect it with `graph.add_edge()`

### Running Tests

(Add test configuration as needed)

## Troubleshooting

### "GEMINI_API_KEY not set" Error
- Ensure you've created a `.env` file with your API key
- Use `python-dotenv` to load the environment: `load_dotenv()`

### Video Processing Timeout
- Reduce `MAX_FRAMES_PER_VIDEO` in `config.py`
- Increase `FRAME_EXTRACTION_RATE` to skip more frames
- Increase `VIDEO_TIMEOUT_SECONDS`

### PDF Generation Errors
- Ensure `reportlab` is installed: `pip install reportlab`
- Check that `OUTPUT_DIR` directory is writable

## Performance

- **Frame Extraction**: ~5-10 frames/second (depends on resolution)
- **Analysis**: ~5-10 seconds per frame (API dependent)
- **Report Generation**: ~2-5 seconds
