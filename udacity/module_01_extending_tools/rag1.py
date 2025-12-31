# SQLite compatibility fix for Udacity workspace
import importlib.util
import sys

# Check if 'pysqlite3' is available before importing
if importlib.util.find_spec("pysqlite3") is not None:
    try:
        import pysqlite3
        sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
    except Exception as e:
        print(f"Warning: Could not load pysqlite3: {e}")

import os
import chromadb
from chromadb.api.models.Collection import Collection
from chromadb.utils import embedding_functions
from dotenv import load_dotenv
from typing import List, TypedDict
import pdfplumber

from lib.state_machine import StateMachine, Step, EntryPoint, Termination, Resource
from lib.llm import LLM
from lib.messages import BaseMessage, UserMessage, SystemMessage

import logging
logging.getLogger('pdfminer').setLevel(logging.ERROR)

load_dotenv()


# ============================================================================
# Constants
# ============================================================================

# Sample AI news sentences for demo
SENTENCE_LIST = [
    "Meta drops multimodal Llama 3.2 — here's why it's such a big deal",
    "Chip giant Nvidia acquires OctoAI, a Seattle startup that helps companies run AI models",
    "Google is bringing Gemini to all older Pixel Buds",
    "The first Intel Battlemage GPU benchmarks have leaked",
    "Dell partners with Nvidia to accelerate AI adoption in telecoms",
]

DOCUMENT_IDS = ["id1", "id2", "id3", "id4", "id5"]

# PDF file path for RAG demo
PDF_FILE_PATH = "GlobalEVOutlook2025.pdf"


# ============================================================================
# ChromaDB RAG Demo
# ============================================================================


def demo_chromadb_basics():
    """Demo: ChromaDB Basics for RAG.
    
    Demonstrates how to use ChromaDB for vector storage and similarity search,
    which is fundamental for Retrieval-Augmented Generation (RAG) systems.
    """
    print("=" * 60)
    print("Demo 1: ChromaDB with Default Embeddings")
    print("=" * 60)

    print("\n--- Step 1: Initialize ChromaDB Client ---")
    chroma_client = chromadb.Client()
    print("ChromaDB client initialized")

    print("\n--- Step 2: Create Collection ---")
    collection = chroma_client.create_collection(name="demo")
    print(f"Collection 'demo' created")

    print("\n--- Step 3: Add Documents to Collection ---")
    collection.add(documents=SENTENCE_LIST, ids=DOCUMENT_IDS)
    print(f"Added {len(SENTENCE_LIST)} documents to collection")

    print("\n--- Step 4: Check Collection Count ---")
    count = collection.count()
    print(f"Total documents in collection: {count}")

    print("\n--- Step 5: Peek at First Document ---")
    peek_result = collection.peek(1)
    print(f"First document ID: {peek_result['ids'][0]}")
    print(f"First document text: {peek_result['documents'][0][:80]}...")

    print("\n--- Step 6: Query Collection (Search for 'gadget') ---")
    result = collection.query(
        query_texts=["gadget"],
        n_results=2,
        include=['metadatas', 'documents', 'distances']
    )
    
    print(f"\nQuery: 'gadget'")
    print(f"Top {len(result['documents'][0])} results:")
    for i, (doc, distance) in enumerate(zip(result['documents'][0], result['distances'][0]), 1):
        print(f"\n  Result {i}:")
        print(f"    Document: {doc}")
        print(f"    Distance: {distance:.4f}")

    print("\n--- Step 7: Check Embedding Function ---")
    embedding_function_name = collection._embedding_function.__class__.__name__
    print(f"Embedding function: {embedding_function_name}")

    print("\n--- Step 8: Check Embedding Dimensions ---")
    size = len(collection.peek(1)['embeddings'][0])
    print(f"Embedding dimensions: {size}")
    
    print("\n" + "=" * 60)
    print("Demo completed successfully")
    print("=" * 60)
    print()
        
# ============================================================================
# OPEN AI ChromaDB RAG Demo
# ============================================================================


def demo_openai_embeddings():
    """Demo: OpenAI Embeddings with ChromaDB.
    
    Demonstrates how to use OpenAI embeddings with ChromaDB for more accurate
    semantic search compared to default embeddings.
    """
    print("=" * 60)
    print("Demo 2: ChromaDB with OpenAI Embeddings")
    print("=" * 60)
    
    print("\n--- Step 1: Initialize ChromaDB Client ---")
    chroma_client = chromadb.Client()
    print("ChromaDB client initialized")
    
    # Clean up existing collection if it exists
    print("\n--- Step 2: Clean Up Previous Collection ---")
    try:
        chroma_client.delete_collection(name="demo_openai")
        print("Deleted existing 'demo_openai' collection")
    except Exception:
        print("No existing collection to delete")

    print("\n--- Step 3: Create OpenAI Embedding Function ---")
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: OPENAI_API_KEY not found in environment")
        print("Skipping OpenAI embeddings demo")
        return
    
    embeddings_fn = embedding_functions.OpenAIEmbeddingFunction(
        api_key=api_key,
        model_name="text-embedding-3-small"
    )
    print("OpenAI embedding function created")

    print("\n--- Step 4: Create Collection with OpenAI Embeddings ---")
    collection = chroma_client.create_collection(
        name="demo_openai",
        embedding_function=embeddings_fn
    )
    print("Collection 'demo_openai' created with OpenAI embeddings")

    print("\n--- Step 5: Add Documents to Collection ---")
    collection.add(
        documents=SENTENCE_LIST,
        ids=DOCUMENT_IDS
    )
    print(f"Added {len(SENTENCE_LIST)} documents to collection")

    print("\n--- Step 6: Query Collection (Search for 'gadget') ---")
    result = collection.query(
        query_texts=["gadget"],
        n_results=2,
        include=['metadatas', 'documents', 'distances']
    )
    
    print(f"\nQuery: 'gadget'")
    print(f"Top {len(result['documents'][0])} results:")
    for i, (doc, distance) in enumerate(zip(result['documents'][0], result['distances'][0]), 1):
        print(f"\n  Result {i}:")
        print(f"    Document: {doc}")
        print(f"    Distance: {distance:.4f}")

    print("\n--- Step 7: Check Embedding Function ---")
    embedding_function_name = collection._embedding_function.__class__.__name__
    print(f"Embedding function: {embedding_function_name}")

    print("\n--- Step 8: Check Embedding Dimensions ---")
    size = len(collection.peek(1)['embeddings'][0])
    print(f"Embedding dimensions: {size}")
    print("Note: OpenAI's text-embedding-3-small uses 1536 dimensions")
    
    print("\n" + "=" * 60)
    print("Demo completed successfully")
    print("=" * 60)
    print()

# ============================================================================
# RAG Demo
# ============================================================================


class State(TypedDict):
    messages: List[BaseMessage]
    question: str
    documents: List[str]
    answer: str

    
def retrieve(state:State, resource:Resource):
    question = state["question"]
    collection:Collection = resource.vars.get("collection")
    results = collection.query(
        query_texts=[question],
        n_results=3,
        include=['documents']
    )
    retrieved_docs = results['documents'][0]
    
    return {"documents": retrieved_docs}

def augment(state:State):
    question = state["question"]
    documents = state["documents"]
    context = "\n\n".join(documents)

    messages = [
        SystemMessage(content="You are an assistant for question-answering tasks."),
        UserMessage(
            content=(
                "Use the following pieces of retrieved context to answer the question. "
                "If you don't know the answer, just say that you don't know. "
                f"\n# Question: \n-> {question} "
                f"\n# Context: \n-> {context} "
                "\n# Answer: "
            )
        )
    ]

    return {"messages": messages}

def generate(state:State, resource:Resource):
    llm:LLM = resource.vars.get("llm")
    ai_message = llm.invoke(state["messages"])
    return {
        "answer": ai_message.content, 
        "messages": state["messages"] + [ai_message],
    }


def rag_demo():
    """Demo: RAG (Retrieval-Augmented Generation).
    
    Demonstrates a complete RAG workflow using ChromaDB, OpenAI embeddings,
    and a state machine to retrieve relevant documents from a PDF and generate
    answers to questions.
    """
    print("=" * 60)
    print("Demo 3: RAG Workflow with PDF")
    print("=" * 60)

    # Check for required API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("\nERROR: OPENAI_API_KEY not found in environment")
        print("Skipping RAG demo")
        return
    
    # Check if PDF file exists
    if not os.path.exists(PDF_FILE_PATH):
        print(f"\nERROR: PDF file '{PDF_FILE_PATH}' not found")
        print("Skipping RAG demo")
        return

    print("\n--- Step 1: Extract Text from PDF ---")
    documents = []
    page_nums = []
    
    try:
        with pdfplumber.open(PDF_FILE_PATH) as pdf:
            print(f"Opening PDF: {PDF_FILE_PATH}")
            for num, page in enumerate(pdf.pages, start=1):
                text = page.extract_text()
                if text:
                    documents.append(text)
                    page_nums.append(str(num))
        print(f"Extracted text from {len(documents)} pages")
    except Exception as e:
        print(f"\nERROR: Failed to extract PDF text: {e}")
        return
    
    print("\n--- Step 2: Initialize ChromaDB Client ---")
    chroma_client = chromadb.Client()
    print("ChromaDB client initialized")
    
    # Clean up existing collection
    try:
        chroma_client.delete_collection(name="traditional_rag")
        print("Deleted existing 'traditional_rag' collection")
    except Exception:
        pass
    
    print("\n--- Step 3: Create Embedding Function ---")
    embeddings_fn = embedding_functions.OpenAIEmbeddingFunction(
        api_key=api_key,
        model_name="text-embedding-3-small"
    )
    print("OpenAI embedding function created")
    
    print("\n--- Step 4: Create Collection and Add Documents ---")
    collection = chroma_client.create_collection(
        name="traditional_rag",
        embedding_function=embeddings_fn
    )
    print("Collection 'traditional_rag' created")
    
    collection.add(
        documents=documents,
        ids=page_nums
    )
    print(f"Added {len(documents)} document pages to collection")
    
    print("\n--- Step 5: Initialize State Machine Workflow ---")
    workflow = StateMachine(State)
    print("State machine initialized")

    print("\n--- Step 6: Configure Workflow Steps ---")
    # Create steps
    entry = EntryPoint()
    retrieve_step = Step("retrieve", retrieve)
    augment_step = Step("augment", augment)
    generate_step = Step("generate", generate)
    termination = Termination()
            
    workflow.add_steps(
        [
            entry, 
            retrieve_step, 
            augment_step, 
            generate_step, 
            termination
        ]
    )
    print("Added steps: entry → retrieve → augment → generate → termination")

    # Add transitions
    workflow.connect(entry, retrieve_step)
    workflow.connect(retrieve_step, augment_step)
    workflow.connect(augment_step, generate_step)
    workflow.connect(generate_step, termination)
    print("Workflow transitions configured")

    print("\n--- Step 7: Initialize LLM and Resources ---")
    llm = LLM(
        model="gpt-4o-mini",
        temperature=0.3,
    )
    print("LLM initialized (gpt-4o-mini)")

    resource = Resource(
        vars={
            "llm": llm,
            "collection": collection,
        }
    )
    print("Resource container created")
    
    print("\n--- Step 8: Execute RAG Workflow ---")
    question = "What was the number of electric car sales and their market share in Brazil in 2024?"
    print(f"Question: {question}")
    
    initial_state: State = {
        "question": question,
    }

    try:
        run_object = workflow.run(initial_state, resource)
        final_state = run_object.get_final_state()
        answer = final_state.get("answer", "No answer generated")
        
        print("\n--- Step 9: Display Results ---")
        print(f"\nQuestion: {question}")
        print(f"\nAnswer: {answer}")
        
        # Show retrieved documents
        if "documents" in final_state:
            print(f"\nRetrieved {len(final_state['documents'])} relevant document chunks")
        
        print("\n" + "=" * 60)
        print("RAG demo completed successfully")
        print("=" * 60)
        print()
        
    except Exception as e:
        print(f"\nERROR during RAG workflow execution: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main function to run all demos.
    
    Demonstrates ChromaDB and RAG systems with:
    1. ChromaDB basics with default embeddings
    2. ChromaDB with OpenAI embeddings (if API key is available)
    3. Complete RAG workflow with PDF document retrieval (if PDF file exists)
    """
    demo_chromadb_basics()
    print("\n" * 2)
    demo_openai_embeddings()
    print("\n" * 2)
    rag_demo()

if __name__ == "__main__":
    main()