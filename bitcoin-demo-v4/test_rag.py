import os
from dotenv import load_dotenv
from bitcoin_rag import BitcoinRAG
import json

def main():
    # Load environment variables
    load_dotenv()
    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
    if not anthropic_api_key:
        raise ValueError("ANTHROPIC_API_KEY not found in environment variables")

    # Initialize RAG system
    print("Initializing Bitcoin RAG system...")
    rag = BitcoinRAG()

    # Load Bitcoin repository (assuming it's in the current directory)
    print("\nLoading Bitcoin repository...")
    repo_path = "bitcoin"  # Adjust this path as needed
    if not os.path.exists(repo_path):
        print(f"Warning: Bitcoin repository not found at {repo_path}")
        print("Please clone the Bitcoin repository first:")
        print("git clone https://github.com/bitcoin/bitcoin.git")
        return

    rag.load_repository(repo_path)

    # Create embeddings for validation subsystem
    print("\nCreating embeddings for validation subsystem...")
    rag.create_embeddings("validation")

    # Set up QA chain
    print("\nSetting up QA chain with Claude...")
    rag.setup_qa_chain(anthropic_api_key)

    # Get cache statistics
    print("\nCache Statistics:")
    stats = rag.get_cache_stats()
    print(json.dumps(stats, indent=2))

    # Test questions
    questions = [
        "How does transaction validation work in validation.cpp?",
        "What are the key security checks in the validation process?",
        "How does the validation subsystem handle double-spending prevention?"
    ]

    print("\nTesting QA system...")
    for question in questions:
        print(f"\nQuestion: {question}")
        try:
            answer = rag.ask_question(question)
            print(f"Answer: {answer}")
        except Exception as e:
            print(f"Error processing question: {str(e)}")

if __name__ == "__main__":
    main() 