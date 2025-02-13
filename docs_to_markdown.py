#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
docs-to-markdown

Implementation of a BFS Multi-URL crawler with Crawl4AI to extract documentation.
- Follows internal links within the same domain, avoiding loops (visited)
- Option to filter irrelevant content using LLM (LLMContentFilter) or heuristic (PruningContentFilter)
- Replicates the website's directory structure in the output .md folder

Usage examples:
  docs-to-markdown https://example.com/docs --llm-filtering --doc_name example_docs
  docs-to-markdown https://example.com/docs --llm-filtering --openai-key "sk-..." --doc_name example_docs
  docs-to-markdown https://example.com/docs --doc_name example_docs
  docs-to-markdown https://example.com/docs --doc_name example_docs --output multiple

Installation:
  pip install docs-to-markdown

Requirements:
  # If using GPT/OpenAI => set OPENAI_API_KEY via command line (--openai-key), in .env, or as an environment variable
"""

import os
import sys
import asyncio
import time
import shutil
from urllib.parse import urlparse, urljoin
import requests
from packaging.version import parse as parse_version
try:
    from importlib import metadata
except ImportError:
    import importlib_metadata as metadata

from dotenv import load_dotenv
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.panel import Panel
from rich.table import Table

# Load environment variables
load_dotenv()

# Setup rich console
console = Console()

# Main import for Crawl4AI
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
# Dispatcher to handle concurrency
from crawl4ai.async_dispatcher import MemoryAdaptiveDispatcher

# Filters (LLM vs heuristic)
try:
    from crawl4ai.content_filter_strategy import LLMContentFilter, PruningContentFilter
except ImportError:
    console.print("[red]Error:[/] You need to install crawl4ai[all] to use content_filter_strategy.")
    sys.exit(1)

PACKAGE_NAME = "docs-to-markdown"

def get_current_version():
    """Gets the currently installed version of the package."""
    try:
        return metadata.version(PACKAGE_NAME)
    except metadata.PackageNotFoundError:
        return "0.1.0"  # Default version in development

def check_for_update():
    """Checks if there is a newer version available on PyPI."""
    current_version = get_current_version()
    try:
        response = requests.get(f"https://pypi.org/pypi/{PACKAGE_NAME}/json", timeout=3)
        if response.status_code == 200:
            data = response.json()
            latest_version = data["info"]["version"]
            if parse_version(latest_version) > parse_version(current_version):
                console.print(Panel.fit(
                f"[yellow]New version available![/]\n"
                f"Current version: [cyan]{current_version}[/]\n"
                f"Latest version: [green]{latest_version}[/]\n"
                f"Update with: [bold]pip install -U {PACKAGE_NAME}[/]"
                ))
    except Exception:
        # Silently ignore network errors or timeouts
        pass

class CrawlStats:
    def __init__(self):
        self.total_urls = 0
        self.processed_urls = 0
        self.success_urls = 0
        self.failed_urls = 0
        self.start_time = time.time()
    
    def add_url(self):
        self.total_urls += 1
    
    def url_processed(self, success: bool):
        self.processed_urls += 1
        if success:
            self.success_urls += 1
        else:
            self.failed_urls += 1
    
    def get_elapsed_time(self):
        return time.time() - self.start_time
    
    def display(self):
        table = Table(title="Crawling Statistics")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Total URLs", str(self.total_urls))
        table.add_row("Processed URLs", str(self.processed_urls))
        table.add_row("Successful", str(self.success_urls))
        table.add_row("Failed", str(self.failed_urls))
        table.add_row("Elapsed Time", f"{self.get_elapsed_time():.2f}s")
        
        console.print(table)

def is_same_domain(base_domain: str, link: str) -> bool:
    """
    Checks if 'link' belongs to the same domain (or subdomain) as base_domain.
    """
    parsed = urlparse(link)
    if not parsed.netloc:
        return False
    return (parsed.netloc == base_domain) or parsed.netloc.endswith(f".{base_domain}")

def build_local_filepath(output_dir: str, doc_name: str, url: str) -> str:
    """
    Generates the local path by replicating the subdirectory structure
    based on the URL path. E.g.:
      URL: https://example.com/docs/intro/getting-started
      => docs/example_docs/docs/intro/getting-started.md
    """
    parsed = urlparse(url)
    # Path without the leading '/'
    subpath = parsed.path.lstrip("/")
    if not subpath:
        subpath = "index"  # Base URL case => index

    dirname = os.path.dirname(subpath)      # e.g. "docs/intro"
    filename = os.path.basename(subpath)    # e.g. "getting-started"
    if not filename:
        filename = "index"             # If path ended with '/'

    local_dir = os.path.join(output_dir, doc_name, dirname)
    os.makedirs(local_dir, exist_ok=True)

    final_name = filename + ".md"
    return os.path.join(local_dir, final_name)

async def crawl_all_docs(
    start_url: str,
    doc_name: str,
    use_llm: bool = False,
    output_mode: str = "single",
    max_depth: int = 1,
    output_dir: str = "."
) -> None:
    """
    BFS: Crawls the documentation and extracts Markdown while preserving folder structure.
    - start_url: Starting URL (documentation)
    - doc_name: Folder name for this documentation
    - use_llm: True => use LLMContentFilter, False => use PruningContentFilter
    - output_mode: Output mode ("single" or "multiple")
      * single: generates a single file (index.md) containing all sections
      * multiple: generates multiple files replicating the site's structure
    - max_depth: Maximum crawling depth
    - output_dir: Output directory where files will be saved
    """
    # Display initial configuration
    console.print(Panel.fit(
        f"[bold green]Starting crawler[/]\n"
        f"URL: [cyan]{start_url}[/]\n"
        f"Depth: [cyan]{max_depth}[/]\n"
        f"Output: [cyan]{output_dir}/{doc_name}[/]\n"
        f"Filter: [cyan]{'LLM' if use_llm else 'Heuristic'}[/]\n"
        f"Output Mode: [cyan]{output_mode}[/]"
    ))

    parsed = urlparse(start_url)
    base_domain = parsed.netloc

    visited = set()
    to_crawl = [(start_url, 0)]
    
    # Initialize statistics
    stats = CrawlStats()
    stats.add_url()  # Initial URL

    browser_cfg = BrowserConfig(headless=True, verbose=False)
    console.print("[bold blue]Initializing browser...[/]")

    # Define content filter
    if use_llm:
        instruction = (
            "Extract the essential content of the documentation in Markdown format, "
            "omitting menus, sidebars, footers, and any irrelevant sections."
        )
        content_filter = LLMContentFilter(
            provider="openai/gpt-4",
            api_token=os.getenv("OPENAI_API_KEY", ""),
            instruction=instruction,
            chunk_token_threshold=1500,
            overlap_rate=0.0,
            verbose=True
        )
    else:
        content_filter = PruningContentFilter(
            threshold=0.5,
            min_word_threshold=30
        )

    run_cfg = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        content_filter=content_filter
    )

    # We could switch to SemaphoreDispatcher if we want a fixed limit
    dispatcher = MemoryAdaptiveDispatcher(
        max_session_permit=5
    )

    os.makedirs(os.path.join(output_dir, doc_name), exist_ok=True)
    
    # For single mode, we'll store all content here
    all_content = []
    
    async with AsyncWebCrawler(config=browser_cfg) as crawler:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console
        ) as progress:
            task_crawl = progress.add_task("[cyan]Crawling...", total=None)
            
            while to_crawl:
                # Taking a batch of 5
                batch = []
                while to_crawl and len(batch) < 5:
                    url, depth = to_crawl.pop(0)
                    if url in visited:
                        continue
                    visited.add(url)
                    batch.append((url, depth))

                if not batch:
                    break

                batch_urls = [b[0] for b in batch]
                progress.update(task_crawl, description=f"[cyan]Processing {len(batch)} URLs...")

                results = await crawler.arun_many(
                    urls=batch_urls,
                    config=run_cfg,
                    dispatcher=dispatcher
                )
                for result in results:
                    if result.success:
                        console.print(f"[green]✓[/] {result.url}")
                        stats.url_processed(True)
                        
                        # Identify depth
                        idx = batch_urls.index(result.url)
                        current_depth = batch[idx][1]

                        # Final Markdown (fit_markdown or raw)
                        if use_llm:
                            md = result.markdown_v2.fit_markdown or result.markdown
                        else:
                            md = result.markdown or ""

                        # Handle content according to the mode
                        if output_mode == "multiple":
                            # Generate local path replicating the URL path
                            local_md_file = build_local_filepath(output_dir, doc_name, result.url)
                            with open(local_md_file, "w", encoding="utf-8") as f:
                                f.write(md)
                        else:  # single
                            # Add title based on the URL
                            parsed_url = urlparse(result.url)
                            path = parsed_url.path.strip("/")
                            if not path:
                                path = "index"
                            title = path.replace("/", " > ").replace("-", " ").replace(".html", "").title()
                            section = f"# {title}\n\n{md}\n\n---\n\n"
                            all_content.append(section)

                        if current_depth < max_depth:
                            # Explore more internal links
                            in_links = result.links.get("internal", [])
                            next_depth = current_depth + 1
                            for link_obj in in_links:
                                href = link_obj["href"]
                                abs_url = urljoin(result.url, href)
                                if is_same_domain(base_domain, abs_url) and abs_url not in visited:
                                    to_crawl.append((abs_url, next_depth))
                                    stats.add_url()
                    else:
                        console.print(f"[red]✗[/] {result.url} => {result.error_message}")
                        stats.url_processed(False)

    # Display final statistics
    console.print("\n[bold green]Crawling completed![/]")
    stats.display()
    
    # Write content and show index.md location
    index_file = os.path.join(output_dir, doc_name, "index.md")
    
    if output_mode == "single":
        # Single mode: write all content to index.md
        with open(index_file, "w", encoding="utf-8") as f:
            f.write("".join(all_content))
    else:
        # Multiple mode: create index.md as entrypoint
        index_content = []
        for url in visited:
            parsed_url = urlparse(url)
            path = parsed_url.path.strip("/")
            if not path:
                path = "index"
            relative_path = path + ".md"
            title = path.replace("/", " > ").replace("-", " ").replace(".html", "").title()
            index_content.append(f"- [{title}]({relative_path})\n")
        
        with open(index_file, "w", encoding="utf-8") as f:
            f.write("# Documentation Index\n\n")
            f.write("".join(index_content))
    
    console.print(f"\n\n[bold green]🚀 Generated Markdown file at:[/] {index_file}\n")
    
    # Display donation message at the end
    donation_message = (
        "\nIf you find this tool useful, please consider supporting me on ko-fi:\n"
        "[link=https://ko-fi.com/frandagostino][blue bold]https://ko-fi.com/frandagostino[/][/link]\n\n"
        "My 🤖 makes 🔧🔧🔧 for 🫵\n"
        "Help me buy some [yellow]⚡⚡⚡[/] to feed them!\n\n"
        "👉 Issues / Feedback / Help:\n"
        "[link=https://github.com/fdagostino/docs-to-markdown][blue bold]https://github.com/fdagostino/docs-to-markdown[/][/link]\n"
    )
    console.print(Panel(donation_message, title="[bold]Support Me [red]❤️[/][/]"))

def parse_args():
    import argparse
    parser = argparse.ArgumentParser(description="docs-to-markdown: Transform online documentation into Markdown by simply providing a URL. Perfect for converting libraries, SDKs, and other documentation for use with LLMs and AI Agents.")
    parser.add_argument("start_url", help="Starting URL (documentation)")
    parser.add_argument("--doc_name", required=True, help="Folder name for this documentation")
    parser.add_argument("--llm-filtering", action="store_true", help="Enable filtering with LLMContentFilter")
    parser.add_argument("--openai-key", help="OpenAI API Key (optional, higher priority than .env or environment variable)")
    parser.add_argument("--output", choices=["single", "multiple"], default="single",
                       help="Output mode: single file (single) or multiple files (multiple). Default: single")
    parser.add_argument("--max_depth", type=int, default=1,
                       help="Maximum crawling depth. Default: 1")
    parser.add_argument("--output_dir", default=os.getcwd(),
                       help="Output directory. Default: current directory")
    return parser.parse_args()

async def main_cli():
    """Main entry point for the CLI."""
    # Display current version
    current_version = get_current_version()
    console.print(f"[bold blue]docs-to-markdown v{current_version}[/]")
    
    # Check for updates at startup
    check_for_update()
    
    args = parse_args()
    
    # Check if output folder exists
    folder_path = os.path.join(args.output_dir, args.doc_name)
    if os.path.exists(folder_path):
        # Ask for confirmation using rich
        response = console.input(f"[yellow]Warning:[/] The folder [cyan]{folder_path}[/] already exists. Do you want to continue and overwrite it? (Y/n): ")
        if not response.lower() in ['n', 'no']:
            console.print(f"[yellow]Deleting existing folder:[/] {folder_path}")
            shutil.rmtree(folder_path)
        else:
            console.print("[red]Operation cancelled by user.[/]")
            sys.exit(0)
    
    # Configure OPENAI_API_KEY if using --llm-filtering
    if args.llm_filtering:
        # Priority: 1. Command-line argument, 2. .env, 3. Environment variable
        openai_key = args.openai_key or os.getenv("OPENAI_API_KEY")
        if not openai_key:
            console.print("[red]Error:[/] OPENAI_API_KEY is required when using --llm-filtering")
            sys.exit(1)
        os.environ["OPENAI_API_KEY"] = openai_key

    await crawl_all_docs(
        start_url=args.start_url,
        doc_name=args.doc_name,
        use_llm=args.llm_filtering,
        output_mode=args.output,
        max_depth=args.max_depth,
        output_dir=args.output_dir
    )

def main():
    """Entry point for the CLI when installed via pip."""
    asyncio.run(main_cli())

if __name__ == "__main__":
    main()
