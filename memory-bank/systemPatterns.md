# System Patterns: Documentation Crawler

## Architecture Overview

### Core Components
1. **BFS Crawler**
   - Manages URL queue and visited set
   - Implements breadth-first traversal
   - Handles batch processing

2. **Content Filters**
   - LLMContentFilter: Uses GPT for intelligent filtering
   - PruningContentFilter: Uses heuristics for basic filtering
   - Strategy pattern for filter selection

3. **Path Manager**
   - Replicates source URL structure
   - Handles directory creation
   - Manages file naming

4. **Dispatcher**
   - MemoryAdaptiveDispatcher for resource management
   - Controls concurrent operations
   - Manages browser sessions

## Design Patterns

1. **Strategy Pattern**
   - Used for content filtering
   - Allows switching between LLM and heuristic approaches
   - Encapsulates filtering algorithms

2. **Factory Pattern**
   - Creates appropriate content filters
   - Manages browser configuration
   - Handles dispatcher initialization

3. **Observer Pattern**
   - Implements progress logging
   - Handles error reporting
   - Manages async operations

## Data Flow
1. URL Processing
   ```
   Input URL → BFS Queue → Batch Processing → Content Extraction
   ```

2. Content Processing
   ```
   Raw HTML → Content Filter → Markdown Conversion → File Storage
   ```

3. Directory Management
   ```
   URL Path → Path Analysis → Directory Creation → File Writing
   ```

## Technical Decisions

1. **Async Processing**
   - Why: Efficient handling of multiple URLs
   - How: asyncio and async/await
   - Benefits: Better resource utilization

2. **Memory Management**
   - Why: Handle large sites efficiently
   - How: Batch processing and adaptive dispatching
   - Benefits: Prevents memory exhaustion

3. **Content Filtering**
   - Why: Clean, relevant content
   - How: Multiple filter strategies
   - Benefits: Flexibility and quality

## Error Handling
1. Network errors: Retry with backoff
2. Parse errors: Skip and log
3. File system errors: Fail gracefully
4. Memory issues: Adaptive throttling
