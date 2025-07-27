# Option Screener API

A Python API for screening stock options.

## Setup

1. Create a virtual environment:
   ```bash
   python -m venv venv
   ```

2. Activate the virtual environment:
   ```bash
   # On macOS/Linux
   source venv/bin/activate
   
   # On Windows
   venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

```bash
python main.py
```

## Development

Install development dependencies:
```bash
pip install -r requirements-dev.txt
```

## Project Structure

```
option-screener-api/
├── main.py              # Entry point
├── requirements.txt     # Production dependencies
├── requirements-dev.txt # Development dependencies
├── .gitignore          # Git ignore rules
├── src/                # Source code
│   └── __init__.py
└── tests/              # Test files
    └── __init__.py
```
