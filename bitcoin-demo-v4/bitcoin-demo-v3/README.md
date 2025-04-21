# Bitcoin RAG System

A Retrieval-Augmented Generation (RAG) system for analyzing the Bitcoin Core codebase. This system combines code embedding, vector search, and large language models to provide intelligent analysis of Bitcoin's source code.

## Features

- CodeBERT-based embeddings for code understanding
- Subsystem-specific analysis (validation, P2P, mining, wallet)
- FAISS vector store for efficient similarity search
- Claude 3 Sonnet integration for intelligent responses
- Caching of embeddings for faster subsequent queries

## Setup

1. Clone this repository:
```bash
git clone <repository-url>
cd bitcoin-demo-v3
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
Create a `.env` file in the project root with:
```
ANTHROPIC_API_KEY=your_api_key_here
```

## Usage

1. Basic usage:
```python
from bitcoin_rag import BitcoinRAG

# Initialize the RAG system
rag = BitcoinRAG()

# Ask a question
result = rag.analyze_code(
    "How does Bitcoin validate transactions?",
    subsystem="validation"
)

print(result["answer"])
```

2. Subsystem-specific analysis:
```python
# Analyze P2P networking
result = rag.analyze_code(
    "How does Bitcoin handle peer connections?",
    subsystem="p2p"
)
```

3. Run the example script:
```bash
python bitcoin_rag.py
```

## Configuration

The system can be configured through `embedding_config.yaml`:

- Embedding settings (chunk size, overlap)
- Subsystem definitions
- LLM parameters
- Retrieval settings
- File patterns

## Project Structure

```
bitcoin-demo-v3/
├── embedding_switcher/     # Embedding model adapters
├── bitcoin/               # Bitcoin Core repository
├── embedding_cache/       # Cached embeddings
├── bitcoin_rag.py        # Main implementation
├── embedding_config.yaml # Configuration
├── requirements.txt      # Dependencies
└── README.md            # This file
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 