# Bitcoin RAG System v4

A Retrieval-Augmented Generation (RAG) system for analyzing Bitcoin Core source code, featuring a robust .kno cache system for efficient embedding management.

## Features

- File-level embedding caching with .kno system
- Support for multiple embedding types (CodeBERT, GraphCodeBERT)
- Subsystem-specific processing (validation, p2p, mining)
- Background processing queue for efficient file handling
- Integration with Claude for advanced code analysis

## Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd bitcoin-demo-v4
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
echo "ANTHROPIC_API_KEY=your_api_key_here" > .env
```

## Usage

1. Initialize the RAG system:
```python
from bitcoin_rag import BitcoinRAG

rag = BitcoinRAG()
```

2. Load the Bitcoin repository:
```python
rag.load_repository("/path/to/bitcoin/repository")
```

3. Create embeddings for a subsystem:
```python
rag.create_embeddings("validation")
```

4. Set up the QA chain:
```python
rag.setup_qa_chain("your_anthropic_api_key")
```

5. Ask questions about the codebase:
```python
answer = rag.ask_question("How does transaction validation work in validation.cpp?")
print(answer)
```

## Cache Management

The .kno cache system automatically manages embeddings and file changes. Key features:

- Automatic detection of file changes
- Background processing of new/changed files
- Subsystem-specific embedding storage
- Cache statistics and monitoring

To view cache statistics:
```python
stats = rag.get_cache_stats()
print(json.dumps(stats, indent=2))
```

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

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License 