# Technical Context: Documentation Crawler

## Development Environment
- Python 3.8+
- Virtual Environment (.venv)
- Git for version control
- VSCode as recommended editor

## Dependencies
1. **Core Libraries**
   ```
   crawl4ai[all]  # Main crawling functionality
   python-dotenv  # Environment variable management
   ```

2. **Browser Automation**
   - Playwright (installed via crawl4ai)
   - Chromium, Firefox, and WebKit browsers

3. **Content Processing**
   - BeautifulSoup4 (via crawl4ai)
   - LLM integration (optional, via OpenAI)

## Configuration
1. **Environment Variables** (.env)
   ```
   OPENAI_API_KEY=sk-...  # Required for LLM filtering
   MAX_DEPTH=2            # Crawl depth
   OUTPUT_DIR=docs_outputs # Base output directory
   ```

2. **Command Line Options**
   ```
   start_url   # Initial documentation URL
   --doc_name  # Name of the folder for this documentation
   --llm       # Enable LLM filtering
   ```

## Project Structure
```
/
├── .venv/                 # Virtual environment
├── .env                   # Environment variables
├── .gitignore            # Git ignore rules
├── memory-bank/          # Project documentation
├── docs_outputs/         # Base directory for all documentation
│   ├── project1_docs/    # Documentation for project 1
│   └── project2_docs/    # Documentation for project 2
└── docs-to-markdown.py   # Main script
```

## Development Setup
1. **Environment Setup**
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install "crawl4ai[all]" python-dotenv
   ```

2. **Browser Installation**
   ```bash
   playwright install
   ```

3. **Configuration**
   - Create .env file
   - Set required environment variables
   - Configure git

## Technical Constraints
1. **Memory Usage**
   - Batch processing for large sites
   - Adaptive dispatcher for resource management
   - Queue-based URL processing

2. **Network**
   - Respect rate limits
   - Handle connection errors
   - Support proxy configuration

3. **Processing**
   - Async operations for efficiency
   - Error handling and logging
   - Clean shutdown handling

## Monitoring and Logging
- Console progress updates
- Error logging to stderr
- Processing statistics
- URL crawl status tracking
