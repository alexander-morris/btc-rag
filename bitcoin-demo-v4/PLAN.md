# Bitcoin RAG System v4 - .kno Cache System Plan

## Overview
The .kno cache system is designed to efficiently manage and store embeddings for Bitcoin Core source files. It provides a robust caching mechanism that tracks file changes and manages different types of embeddings based on subsystems and request types.

## Directory Structure
```
.kno/
├── metadata/
│   ├── file_hashes.json      # Tracks file hashes for change detection
│   └── embedding_types.json  # Configuration for different embedding types
├── embeddings/
│   ├── codebert/
│   │   ├── validation/
│   │   ├── p2p/
│   │   └── mining/
│   └── [other_embedding_types]/
└── temp/                     # Temporary storage for processing
```

## Key Components

### 1. Cache Manager (`KnoCacheManager`)
- Manages the cache directory structure
- Tracks file hashes for change detection
- Handles embedding type configurations
- Provides thread-safe queue for processing files
- Implements background processing of files

### 2. Cache Entry (`KnoCacheEntry`)
- Stores metadata about cached embeddings:
  - File path
  - Embedding type
  - Subsystem
  - File hash
  - Timestamp
  - Embeddings
  - Additional metadata

### 3. Processing Queue
- Priority-based queue for processing files
- Background thread pool for parallel processing
- Automatic detection of file changes
- Efficient handling of multiple embedding types

## Features

### File Change Detection
- Uses SHA-256 hashing to detect file changes
- Automatically invalidates cache entries when files change
- Maintains hash database for quick comparison

### Embedding Type Management
- Configurable embedding types (e.g., CodeBERT)
- Subsystem-specific embeddings
- Extensible architecture for new embedding types

### Background Processing
- Asynchronous processing of files
- Priority-based queue system
- Thread pool for parallel processing
- Automatic cleanup of completed tasks

### Cache Validation
- Automatic validation of cache entries
- Removal of invalid entries
- Rebuilding of cache when needed

## Implementation Plan

1. **Phase 1: Core Infrastructure**
   - [x] Create cache directory structure
   - [x] Implement file hash tracking
   - [x] Set up basic cache entry management

2. **Phase 2: Processing System**
   - [x] Implement processing queue
   - [x] Add background processing
   - [x] Create thread pool management

3. **Phase 3: Integration**
   - [ ] Integrate with existing embedding system
   - [ ] Add support for multiple embedding types
   - [ ] Implement subsystem-specific processing

4. **Phase 4: Optimization**
   - [ ] Add compression for embeddings
   - [ ] Implement batch processing
   - [ ] Add cache cleanup utilities

## Usage Example

```python
# Initialize cache manager
cache = KnoCacheManager()

# Scan directory for processing
cache.scan_directory("src/", "codebert", "validation")

# Get cached embeddings
entry = cache.get_cache("src/validation.cpp", "codebert", "validation")
if entry:
    embeddings = entry.embeddings
else:
    # Handle missing cache
    pass
```

## Future Enhancements

1. **Compression**
   - Add support for compressed embeddings
   - Implement efficient serialization

2. **Distributed Processing**
   - Add support for distributed processing
   - Implement work distribution

3. **Advanced Caching**
   - Add LRU cache for frequently accessed files
   - Implement predictive caching

4. **Monitoring**
   - Add cache hit/miss statistics
   - Implement performance monitoring 