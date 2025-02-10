# Crawl4AI Documentation Extractor

A Python-based tool that uses Crawl4AI to extract documentation from websites and convert it to Markdown format. The tool performs a breadth-first search (BFS) traversal of documentation sites, maintaining the original structure while filtering out irrelevant content.

## Features

- **BFS Crawling**: Systematically traverses documentation sites level by level
- **Content Filtering**: Removes irrelevant content (menus, footers, sidebars)
  - Heuristic-based filtering (default)
  - LLM-based filtering (optional, requires OpenAI API key)
- **Directory Structure Preservation**: Replicates the source site's structure
- **Real-time Progress**: Rich console output with progress bars and statistics
- **Configurable**: Command-line options for depth, output directory, and filtering

## Installation

1. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install "crawl4ai[all]"
```

3. (Optional) For LLM-based filtering, set up your OpenAI API key:
```bash
echo "OPENAI_API_KEY=your-api-key-here" > .env
```

## Usage

Basic usage:
```bash
python multi_doc_extract.py https://example.com/docs --depth 2 --out docs_outputs
```

With LLM filtering:
```bash
python multi_doc_extract.py https://example.com/docs --depth 2 --out docs_outputs --llm
```

### Command Line Options

- `start_url`: Initial documentation URL (required)
- `--depth`: Maximum crawling depth (default: 2)
- `--out`: Output directory for markdown files (default: docs_outputs)
- `--llm`: Enable LLM-based content filtering (requires OpenAI API key)

## Example Output Structure

```
docs_outputs/
├── section1/
│   ├── page1.md
│   └── subsection/
│       └── page2.md
└── section2/
    └── page3.md
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
