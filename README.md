# docs-to-markdown 🚀 | Convert online documentation into Markdown by simply providing a URL

Perfect for converting APIs docs, libraries docs, SDKs docs, and any other type of tech documentation for use with LLMs, AI Agents, Cursor, Tailwind, Cline, etc.

## What is docs-to-markdown?  
docs-to-markdown is a simple and fast tool that crawls online documentation from a given URL and converts it into Markdown files. 
Just provide the URL of the documentation you want to convert, and the tool will handle the rest. 
Whether you need a single consolidated file or multiple files, it streamlines your workflow for feeding content into your LLM and optimizing your AI prompts.

## Features ✨  
- **Flexible Conversion:** Convert documentation into one file or split into multiple files based on your needs.
- **Intelligent Filtering:** Extract only the sections you need to include in your LLM's context.
- **AI-Optimized:** Tailored for seamless integration with LLMs, AI Agents, and other AI systems.
- **User-Friendly:** Easy-to-use commands and a straightforward interface for quick results.

## Installation 💻  
Install directly from PyPI:
```bash
pip install docs-to-markdown
```

## Usage 🚀  
The tool provides flexible options for converting online documentation to Markdown format:

### Basic Usage
```bash
docs-to-markdown https://example.com/docs --doc_name example_docs
```

### With LLM Filtering (using GPT-4)
```bash
docs-to-markdown https://example.com/docs --llm-filtering --doc_name example_docs
```
Note: When using `--llm-filtering`, you need to set your OpenAI API key via:
- Command line: `--openai-key "sk-..."`
- Environment variable: `OPENAI_API_KEY`
- `.env` file

### Output Options
Generate multiple files (preserving site structure):
```bash
docs-to-markdown https://example.com/docs --doc_name example_docs --output multiple
```

Generate a single consolidated file:
```bash
docs-to-markdown https://example.com/docs --doc_name example_docs --output single
```

### Additional Parameters
- `--max_depth`: Maximum crawling depth (default: 2)
- `--output_dir`: Output directory (default: current directory)
- `--llm-filtering`: Use GPT-4 to filter and clean content
- `--openai-key`: OpenAI API key for LLM filtering

The tool will create a directory named by your `doc_name` parameter containing the Markdown files.

## Development 🛠️

### Developer Setup
Clone the project from GitHub:
```bash
git clone https://github.com/fdagostino/docs-to-markdown.git
cd docs-to-markdown
```

Install the required dependencies:
```bash
pip install -r requirements.txt
```

(Optional) It's recommended to use a virtual environment for development:
```bash
python -m venv .venv
source .venv/bin/activate  # On macOS/Linux or `.venv\Scripts\activate` on Windows
```

To run and test the project locally, simply invoke:
```bash
python docs_to_markdown.py https://example.com/docs --doc_name example_docs
```
You can also use additional flags (e.g., `--llm-filtering`, `--output multiple`) as needed during development.

### Developed 100% with AI 🤖
This project was entirely developed using 🤖🤖🤖 and the amazing library [Crawl4AI](https://github.com/unclecode/crawl4ai).

## Contributing & Reporting Issues 🤝

We welcome contributions and feedback to help improve docs-to-markdown.

### How to Contribute
- **Fork the Repository:** Click the "Fork" button on GitHub to create your own copy.
- **Clone Your Fork:**  
  ```bash
  git clone https://github.com/YOUR_USERNAME/docs-to-markdown.git
  cd docs-to-markdown
  ```
- **Create a Feature Branch:**  
  ```bash
  git checkout -b feature/your-feature-name
  ```
- **Implement Your Changes** 
- **Submit a Pull Request:** Open a pull request against the main repository when your changes are ready.

### How to Report Issues
- **Visit the Issues Page:** Please report bugs or feature requests at [https://github.com/fdagostino/docs-to-markdown/issues](https://github.com/fdagostino/docs-to-markdown/issues).
- **Before Reporting:** Check if the issue has already been reported.
- **Provide Details:** When opening a new issue, include a clear description, steps to reproduce (if applicable), and any relevant error messages.

Your contributions and feedback are highly appreciated!

## Support Me ❤️ 
If you find this tool useful, please consider supporting me on ko‑fi:  
[![Donate](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/frandagostino) 

My 🤖 makes 🔧🔧🔧 for 🫵.
Help me buy some ⚡⚡⚡ to feed them!

## License 📄  
This project is licensed under the terms found in [LICENSE.md](LICENSE.md).
