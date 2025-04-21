import os
from pathlib import Path
from bitcoin_rag import BitcoinRAG
from dotenv import load_dotenv

# Load environment variables from project root .env file
root_env_path = Path(__file__).parent.parent / '.env'
load_dotenv(root_env_path)

def test_bitcoin_rag():
    """Test the Bitcoin RAG system functionality."""
    print("\n=== Testing Bitcoin RAG System ===\n")
    
    # Initialize RAG system
    repo_path = "bitcoin"
    rag = BitcoinRAG(repo_path=repo_path)
    
    # Test repository loading
    print("1. Testing repository loading...")
    rag.load_repository(repo_path)
    print("✓ Repository loading complete\n")
    
    # Test embedding creation for validation subsystem
    print("2. Testing embedding creation for validation subsystem...")
    rag.create_embeddings("validation")
    print("✓ Embeddings created successfully\n")
    
    # Test QA chain setup
    print("3. Setting up QA chain...")
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable not set")
    rag.setup_qa_chain(api_key)
    print("✓ QA chain setup complete\n")
    
    # Test questions
    print("4. Testing questions...")
    questions = [
        "How does the CheckTransaction function validate Bitcoin transactions? Focus on security checks.",
        "What are the main performance optimizations in block validation?",
        "How does Bitcoin prevent double-spending attacks in its consensus code?"
    ]
    
    for i, question in enumerate(questions, 1):
        print(f"\nQuestion {i}: {question}")
        try:
            answer = rag.ask_question(question)
            print("\nAnswer:")
            print(answer)
            print("\n" + "="*80 + "\n")
        except Exception as e:
            print(f"Error processing question: {str(e)}")
    
    # Test cache statistics
    print("5. Testing cache statistics...")
    stats = rag.get_cache_stats()
    print("\nCache Statistics:")
    print(f"Total chunks: {stats['total_chunks']}")
    print("\nCached Subsystems:")
    for subsystem in stats['cached_subsystems']:
        print(f"- {subsystem}")
    print("\nMemory Usage:")
    print(f"- Chunk cache size: {stats['memory_usage']['chunk_cache_size']} bytes")
    print(f"- Model cache size: {stats['memory_usage']['model_cache_size']} bytes")
    if 'gpu_memory' in stats:
        print("\nGPU Memory:")
        print(f"- Allocated: {stats['gpu_memory']['allocated']} bytes")
        print(f"- Cached: {stats['gpu_memory']['cached']} bytes")

if __name__ == "__main__":
    test_bitcoin_rag() 