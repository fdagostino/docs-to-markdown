# Crawl4AI Documentation Extractor

A Python-based tool that uses Crawl4AI to extract documentation from websites and convert it to Markdown format. The tool performs a breadth-first search (BFS) traversal of documentation sites, maintaining the original structure while filtering out irrelevant content.

## Features

- **BFS Crawling**: Systematically traverses documentation sites level by level
- **Content Filtering**: Removes irrelevant content (menus, footers, sidebars)
  - Heuristic-based filtering (default)
  - LLM-based filtering (optional, requires OpenAI API key)
- **Directory Structure Preservation**: Replicates the source site's structure within named documentation folders
- **Real-time Progress**: Rich console output with progress bars and statistics
- **Configurable**: Environment variables for depth and output directory, command-line options for filtering

## Installation

1. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install "crawl4ai[all]" python-dotenv
```

3. Configure environment variables in .env:
```bash
# Required for LLM-based filtering
OPENAI_API_KEY=your-api-key-here

# Optional configurations (shown with defaults)
MAX_DEPTH=2
OUTPUT_DIR=docs_outputs
```

## Usage

Basic usage:
```bash
python docs-to-markdown.py https://example.com/docs --doc_name example_docs
```

With LLM filtering:
```bash
python docs-to-markdown.py https://example.com/docs --doc_name example_docs --llm
```

### Command Line Options

- `start_url`: Initial documentation URL (required)
- `--doc_name`: Name of the folder where documentation will be saved (required)
- `--llm`: Enable LLM-based content filtering (requires OpenAI API key)

### Environment Variables

- `MAX_DEPTH`: Maximum crawling depth (default: 2)
- `OUTPUT_DIR`: Base output directory for markdown files (default: docs_outputs)
- `OPENAI_API_KEY`: Required for LLM-based filtering

## Example Output Structure

```
docs_outputs/
├── project1_docs/           # --doc_name project1_docs
│   ├── section1/
│   │   ├── page1.md
│   │   └── subsection/
│   │       └── page2.md
│   └── section2/
│       └── page3.md
└── project2_docs/           # --doc_name project2_docs
    ├── intro/
    │   └── getting-started.md
    └── api/
        └── reference.md
```

## Features in Detail

### BFS Crawling
- Processes pages level by level
- Stays within the same domain
- Handles relative and absolute URLs
- Concurrent processing with batch size management

### Content Filtering
- **Heuristic Mode**: Uses structural analysis to identify main content
- **LLM Mode**: Uses GPT to extract relevant documentation content
- Preserves markdown formatting
- Removes navigation elements and advertisements

### Progress Tracking
- Real-time progress bars
- URL processing status indicators
- Crawling statistics (total URLs, success rate, timing)
- Error reporting for failed URLs

## Development

The project uses a memory bank system for documentation:

- `projectbrief.md`: Core requirements and goals
- `productContext.md`: Problem and solution context
- `systemPatterns.md`: Technical architecture
- `techContext.md`: Development setup
- `activeContext.md`: Current work status
- `progress.md`: Project progress tracking

## License

MIT License

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request
