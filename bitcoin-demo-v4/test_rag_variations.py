import os
from pathlib import Path
from bitcoin_rag import BitcoinRAG
from dotenv import load_dotenv
import json
from datetime import datetime
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from langchain_anthropic import ChatAnthropic
import logging

# Load environment variables
root_env_path = Path(__file__).parent.parent / '.env'
load_dotenv(root_env_path)

def run_test_questions(rag, test_name: str, test_params: dict):
    """Run standard test questions and record results."""
    results = {
        "test_name": test_name,
        "parameters": test_params,
        "timestamp": datetime.now().isoformat(),
        "questions": []
    }
    
    questions = [
        "How does the CheckTransaction function validate Bitcoin transactions? Focus on security checks.",
        "What are the main performance optimizations in block validation?",
        "How does Bitcoin prevent double-spending attacks in its consensus code?"
    ]
    
    for question in questions:
        try:
            answer = rag.ask_question(question)
            results["questions"].append({
                "question": question,
                "answer": answer["answer"],
                "confidence": answer["confidence"],
                "query_time": answer["query_time"],
                "total_sources": answer["total_sources"],
                "sources": answer["sources"]
            })
        except Exception as e:
            results["questions"].append({
                "question": question,
                "error": str(e)
            })
    
    return results

def update_test_results(results: dict):
    """Update the test-results.md file with new results."""
    results_file = Path(__file__).parent / "test-results.md"
    
    # Read existing content
    content = results_file.read_text() if results_file.exists() else ""
    
    # Add new results section
    new_section = f"\n### {results['test_name']} ({datetime.now().strftime('%Y-%m-%d %H:%M')})\n"
    new_section += "Parameters:\n"
    for k, v in results["parameters"].items():
        new_section += f"- {k}: {v}\n"
    
    new_section += "\nResults:\n"
    for q in results["questions"]:
        new_section += f"\nQuestion: {q['question']}\n"
        if "error" in q:
            new_section += f"Error: {q['error']}\n"
        else:
            new_section += f"- Confidence: {q['confidence']:.2f}\n"
            new_section += f"- Query Time: {q['query_time']:.2f}s\n"
            new_section += f"- Total Sources: {q['total_sources']}\n"
            new_section += "- Sources:\n"
            for src in q["sources"]:
                new_section += f"  * {src['path']}\n"
            new_section += f"- Answer Summary: {q['answer'][:200]}...\n"
    
    # Add new section before the last "Results will be added..." line
    if "Results will be added here as tests are completed..." in content:
        content = content.replace(
            "Results will be added here as tests are completed...",
            new_section + "\nResults will be added here as tests are completed..."
        )
    else:
        content += new_section
    
    # Write updated content
    results_file.write_text(content)

def test_chunk_parameters():
    """Test 1: Adjust chunk parameters."""
    params = {
        "chunk_size": 500,
        "chunk_overlap": 300,
        "retriever_k": 4
    }
    
    # Initialize RAG with modified parameters
    repo_path = "bitcoin"
    rag = BitcoinRAG(repo_path=repo_path)
    
    # Modify chunk parameters
    rag.text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=params["chunk_size"],
        chunk_overlap=params["chunk_overlap"],
        length_function=len,
    )
    
    # Run standard test process
    rag.load_repository(repo_path)
    rag.create_embeddings("validation")
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable not set")
    rag.setup_qa_chain(api_key)
    
    # Run tests and record results
    results = run_test_questions(rag, "Test 1: Chunk Parameters", params)
    update_test_results(results)
    
    # Cleanup
    rag.cleanup()

def test_retrieval_parameters():
    """Test 2: Adjust retrieval parameters."""
    params = {
        "chunk_size": 1000,  # Back to original
        "chunk_overlap": 200,  # Back to original
        "retriever_k": 6,
        "search_type": "mmr",
        "diversity_bias": 0.3
    }
    
    # Initialize RAG
    repo_path = "bitcoin"
    rag = BitcoinRAG(repo_path=repo_path)
    
    # Run standard test process
    rag.load_repository(repo_path)
    rag.create_embeddings("validation")
    
    # Modify retriever parameters for all subsystems
    for subsystem, retriever in rag.retrievers.items():
        vectorstore = retriever.vectorstore
        rag.retrievers[subsystem] = vectorstore.as_retriever(
            search_type="mmr",
            search_kwargs={
                "k": params["retriever_k"],
                "fetch_k": params["retriever_k"] * 4,  # Fetch more candidates for MMR
                "lambda_mult": 1 - params["diversity_bias"]  # Convert diversity_bias to lambda_mult
            }
        )
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable not set")
    rag.setup_qa_chain(api_key)
    
    # Run tests and record results
    results = run_test_questions(rag, "Test 2: Retrieval Parameters", params)
    update_test_results(results)
    
    # Cleanup
    rag.cleanup()

def test_prompt_engineering():
    """Test 3: Improve prompt engineering."""
    params = {
        "chunk_size": 1000,
        "chunk_overlap": 200,
        "retriever_k": 6,
        "search_type": "mmr",
        "diversity_bias": 0.3,
        "prompt_template": """You are an expert Bitcoin Core developer analyzing the codebase. You have deep knowledge of C++ and systems programming.

Context about Bitcoin Core architecture:
- The codebase is organized into subsystems (validation, consensus, p2p, wallet, etc.)
- Validation handles transaction and block verification
- Consensus enforces network rules and maintains blockchain state
- Code often uses RAII patterns and careful memory management
- Security is paramount, with extensive checks and error handling

Given this context and the following code snippets, answer the question. Focus on:
1. Specific code paths and function implementations
2. Security implications and edge cases
3. Performance considerations and optimizations
4. How the code interacts with other subsystems
5. Any potential vulnerabilities or attack vectors

If you cannot find the relevant code in the provided context, explain what you would expect to find and where it might be located.

Code context:
{context}

Question: {question}

Answer: Let me analyze the code and provide a detailed technical response:"""
    }
    
    # Initialize RAG
    repo_path = "bitcoin"
    rag = BitcoinRAG(repo_path=repo_path)
    
    # Run standard test process
    rag.load_repository(repo_path)
    rag.create_embeddings("validation")
    
    # Modify retriever parameters
    for subsystem, retriever in rag.retrievers.items():
        vectorstore = retriever.vectorstore
        rag.retrievers[subsystem] = vectorstore.as_retriever(
            search_type="mmr",
            search_kwargs={
                "k": params["retriever_k"],
                "fetch_k": params["retriever_k"] * 4,
                "lambda_mult": 1 - params["diversity_bias"]
            }
        )
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable not set")
    
    # Create QA chains with improved prompt
    rag.llm = ChatAnthropic(
        anthropic_api_key=api_key,
        model="claude-3-sonnet-20240229",
        temperature=0.2,
        max_tokens=4000
    )
    
    for subsystem, retriever in rag.retrievers.items():
        PROMPT = PromptTemplate(
            template=params["prompt_template"],
            input_variables=["context", "question"]
        )
        
        rag.qa_chains[subsystem] = RetrievalQA.from_chain_type(
            llm=rag.llm,
            chain_type="stuff",
            retriever=retriever,
            chain_type_kwargs={
                "prompt": PROMPT,
            },
            return_source_documents=True
        )
    
    # Run tests and record results
    results = run_test_questions(rag, "Test 3: Improved Prompt", params)
    update_test_results(results)
    
    # Cleanup
    rag.cleanup()

def test_source_filtering():
    """Test 4: Source file filtering."""
    params = {
        "chunk_size": 1000,
        "chunk_overlap": 200,
        "retriever_k": 6,
        "search_type": "mmr",
        "diversity_bias": 0.3,
        "file_patterns": {
            "include": [
                "src/validation.cpp",
                "src/validation.h",
                "src/consensus/*.cpp",
                "src/consensus/*.h",
                "src/primitives/*.cpp",
                "src/primitives/*.h",
                "src/script/*.cpp",
                "src/script/*.h",
                "src/policy/*.cpp",
                "src/policy/*.h"
            ],
            "exclude": [
                "*/test/*",
                "*/bench/*",
                "*/fuzzing/*",
                "*/qt/*",
                "*/leveldb/*",
                "*_test.cpp",
                "*_tests.cpp",
                "*_bench.cpp",
                "*_fuzzer.cpp",
                "*_mock.cpp",
                "*_mock.h"
            ]
        },
        "prompt_template": """You are an expert Bitcoin Core developer analyzing the codebase. You have deep knowledge of C++ and systems programming.

Context about Bitcoin Core architecture:
- The codebase is organized into subsystems (validation, consensus, p2p, wallet, etc.)
- Validation handles transaction and block verification
- Consensus enforces network rules and maintains blockchain state
- Code often uses RAII patterns and careful memory management
- Security is paramount, with extensive checks and error handling

Given this context and the following code snippets from core implementation files (excluding tests), answer the question. Focus on:
1. Specific code paths and function implementations
2. Security implications and edge cases
3. Performance considerations and optimizations
4. How the code interacts with other subsystems
5. Any potential vulnerabilities or attack vectors

If you cannot find the relevant code in the provided context, explain what you would expect to find and where it might be located.

Code context:
{context}

Question: {question}

Answer: Let me analyze the code and provide a detailed technical response:"""
    }
    
    # Configure logging
    logging.getLogger('bitcoin_rag').setLevel(logging.DEBUG)
    
    # Initialize RAG
    repo_path = "bitcoin"
    rag = BitcoinRAG(repo_path=repo_path)
    
    # Run standard test process with file filtering
    print("\nLoading repository with source filtering...")
    rag.load_repository(
        repo_path,
        include_patterns=params["file_patterns"]["include"],
        exclude_patterns=params["file_patterns"]["exclude"]
    )
    
    print("\nCreating embeddings for validation subsystem...")
    rag.create_embeddings("validation")
    
    # Modify retriever parameters
    for subsystem, retriever in rag.retrievers.items():
        vectorstore = retriever.vectorstore
        rag.retrievers[subsystem] = vectorstore.as_retriever(
            search_type="mmr",
            search_kwargs={
                "k": params["retriever_k"],
                "fetch_k": params["retriever_k"] * 4,
                "lambda_mult": 1 - params["diversity_bias"]
            }
        )
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable not set")
    
    # Create QA chains with improved prompt
    print("\nSetting up QA chain...")
    rag.llm = ChatAnthropic(
        anthropic_api_key=api_key,
        model="claude-3-sonnet-20240229",
        temperature=0.2,
        max_tokens=4000
    )
    
    for subsystem, retriever in rag.retrievers.items():
        PROMPT = PromptTemplate(
            template=params["prompt_template"],
            input_variables=["context", "question"]
        )
        
        rag.qa_chains[subsystem] = RetrievalQA.from_chain_type(
            llm=rag.llm,
            chain_type="stuff",
            retriever=retriever,
            chain_type_kwargs={
                "prompt": PROMPT,
            },
            return_source_documents=True
        )
    
    # Run tests and record results
    print("\nRunning test questions...")
    results = run_test_questions(rag, "Test 4: Source Filtering", params)
    update_test_results(results)
    
    # Print source statistics
    print("\nSource file statistics:")
    for question in results["questions"]:
        print(f"\nQuestion: {question['question'][:50]}...")
        print(f"Number of sources: {len(question.get('sources', []))}")
        print("Source files:")
        for source in question.get('sources', []):
            print(f"  - {source['path']}")
    
    # Cleanup
    rag.cleanup()

if __name__ == "__main__":
    # Run Test 1
    print("Running Test 1: Chunk Parameters...")
    test_chunk_parameters()
    print("Test 1 complete. Results have been recorded in test-results.md")

    # Run Test 2
    print("Running Test 2: Retrieval Parameters...")
    test_retrieval_parameters()
    print("Test 2 complete. Results have been recorded in test-results.md")

    # Run Test 3
    print("Running Test 3: Improved Prompt...")
    test_prompt_engineering()
    print("Test 3 complete. Results have been recorded in test-results.md")

    # Run Test 4
    print("Running Test 4: Source Filtering...")
    test_source_filtering()
    print("Test 4 complete. Results have been recorded in test-results.md") 