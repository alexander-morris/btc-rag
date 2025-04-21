# KNO SDK

A powerful SDK for integrating knowledge embeddings and caching into GitHub repositories.

## Overview

The KNO SDK provides a seamless way to add knowledge embeddings and caching capabilities to any GitHub repository. It enables intelligent file analysis, caching, and iterative improvement of knowledge representations.

## Core Features

### 1. GitHub Integration
- Seamless integration with GitHub repositories using API tokens
- Automatic repository scanning and file indexing
- Support for both public and private repositories
- Configurable file type filtering and processing

### 2. Local KNO Services
- **File Embeddings**: Generate embeddings for individual files
  - Support for multiple file types (text, code, markdown, etc.)
  - Configurable embedding models and parameters
  - Efficient batch processing capabilities

- **KNO Cache**: Agentic interaction caching system
  - Persistent storage of embeddings and metadata
  - Efficient querying and retrieval
  - Support for multiple cache backends (local, remote, hybrid)

- **Iterative Improvement**: Continuous enhancement of knowledge cache
  - File change detection and automatic updates
  - Incremental embedding updates
  - Version tracking and history management

## Architecture

### Components

1. **GitHub Connector**
   - Repository scanning and file discovery
   - Authentication and API management
   - File change detection and webhook integration

2. **Embedding Engine**
   - File preprocessing and parsing
   - Embedding generation and storage
   - Model management and configuration

3. **Cache Manager**
   - Cache storage and retrieval
   - Query optimization
   - Cache invalidation and updates

4. **Version Control**
   - Change tracking
   - Version management
   - History preservation

### Data Flow

1. Repository → GitHub Connector → File List
2. File List → Embedding Engine → Embeddings
3. Embeddings → Cache Manager → Persistent Storage
4. File Changes → Version Control → Cache Updates

## Implementation Plan

### Phase 1: Core Infrastructure
- [ ] GitHub API integration
- [ ] Basic file embedding system
- [ ] Local cache implementation

### Phase 2: Advanced Features
- [ ] Multi-file embedding support
- [ ] Cache optimization
- [ ] Change detection system

### Phase 3: Production Ready
- [ ] Error handling and recovery
- [ ] Performance optimization
- [ ] Documentation and examples

## Usage Example

```python
from kno_sdk import KNO

# Initialize SDK
kno = KNO(api_token="your_github_token")

# Connect to repository
repo = kno.connect_repository("owner/repo")

# Generate embeddings
embeddings = repo.generate_embeddings()

# Access cache
cache = repo.get_cache()
results = cache.query("your query")

# Handle file changes
repo.watch_changes(callback=update_cache)
```

## Requirements

- Python 3.8+
- GitHub API access
- Local storage for cache
- Optional: GPU for faster embeddings

## Installation

```bash
pip install kno-sdk
```

## License

MIT License 