# Project Brief: Crawl4AI Documentation Extractor

## Overview
A Python-based tool that uses Crawl4AI to extract documentation from websites and convert it to Markdown format. The tool performs a breadth-first search (BFS) traversal of documentation sites, maintaining the original structure while filtering out irrelevant content.

## Core Requirements
1. Multi-URL crawling with BFS traversal
2. Domain-scoped crawling (stay within the same domain)
3. Content filtering (remove menus, footers, sidebars)
4. Directory structure preservation
5. Console logging for progress tracking
6. Support for both LLM and heuristic-based content filtering

## Technical Specifications
- Python 3.8+
- Crawl4AI library for web crawling
- Environment variables for configuration
- Async/await for concurrent processing
- Memory-adaptive dispatcher for resource management

## Success Criteria
- Successfully extracts documentation content
- Maintains original site structure in output
- Provides clear progress feedback via console
- Handles errors gracefully
- Produces clean, readable Markdown files
