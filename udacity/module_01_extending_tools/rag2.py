# Only needed for Udacity workspace

import importlib.util
import sys

# Check if 'pysqlite3' is available before importing
if importlib.util.find_spec("pysqlite3") is not None:
    import pysqlite3
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import os
from typing import List
from dotenv import load_dotenv

from lib.agents import Agent
from lib.llm import LLM
from lib.state_machine import Run, StateMachine, Step, EntryPoint, Termination, Resource
from lib.messages import BaseMessage, SystemMessage, UserMessage
from lib.tooling import tool
from lib.vectordb import VectorStoreManager, CorpusLoaderService, VectorStore

import logging
logging.getLogger('pdfminer').setLevel(logging.ERROR)

load_dotenv()


# ============================================================================
# Global Variables for RAG Instances
# ============================================================================

# These will be initialized in rag_demo() and accessed by tool functions
electric_vehicles_vector_store: VectorStore = None
games_market_vector_store: VectorStore = None
rag_llm: LLM = None

# ============================================================================
# Tool Functions
# ============================================================================

@tool
def search_global_ev_collection(query: str):
    """
    Search the vector database for relevant information about electric vehicles.
    
    Source: Global EV Outlook 2025
    Publisher: International Energy Agency
    Release: May 2025
    
    The Global EV Outlook is an annual publication that reports on recent
    developments in electric mobility around the world. It is developed with the support
    of members of the Electric Vehicles Initiative (EVI).

    Args:
        query (str): Search query
        
    Returns:
        str: Answer generated from relevant documents
    """
    if electric_vehicles_vector_store is None:
        return "Error: Electric vehicles vector store not initialized"
    
    try:
        # Query the vector store
        results = electric_vehicles_vector_store.query(query_text=query, n_results=3)
        documents = results['documents'][0] if results['documents'] else []
        
        if not documents:
            return "No relevant information found."
        
        # Create context from retrieved documents
        context = "\n\n".join(documents)
        
        # Use LLM to generate answer
        messages = [
            SystemMessage(content="You are an assistant for question-answering tasks about electric vehicles."),
            UserMessage(
                content=(
                    "Use the following pieces of retrieved context to answer the question. "
                    "If you don't know the answer, just say that you don't know. "
                    f"\n# Question: \n-> {query} "
                    f"\n# Context: \n-> {context} "
                    "\n# Answer: "
                )
            )
        ]
        
        response = rag_llm.invoke(messages)
        return response.content
    except Exception as e:
        return f"Error searching electric vehicles collection: {str(e)}"

@tool
def search_games_market_report_collection(query: str):
    """
    Search the vector database for relevant information about gaming industry.
    
    Source: The Gaming Industry in 2024 - Trends, Technologies & Predictions
    Publisher: Ixie Gaming
    Release: 2024
    
    The gaming industry, on the brink of transformative change due to technological
    advancements, is redefining entertainment and social interaction with
    immersive, personalized, and interactive experiences.

    Args:
        query (str): Search query
        
    Returns:
        str: Answer generated from relevant documents
    """
    if games_market_vector_store is None:
        return "Error: Games market vector store not initialized"
    
    try:
        # Query the vector store
        results = games_market_vector_store.query(query_text=query, n_results=3)
        documents = results['documents'][0] if results['documents'] else []
        
        if not documents:
            return "No relevant information found."
        
        # Create context from retrieved documents
        context = "\n\n".join(documents)
        
        # Use LLM to generate answer
        messages = [
            SystemMessage(content="You are an assistant for question-answering tasks about the gaming industry."),
            UserMessage(
                content=(
                    "Use the following pieces of retrieved context to answer the question. "
                    "If you don't know the answer, just say that you don't know. "
                    f"\n# Question: \n-> {query} "
                    f"\n# Context: \n-> {context} "
                    "\n# Answer: "
                )
            )
        ]
        
        response = rag_llm.invoke(messages)
        return response.content
    except Exception as e:
        return f"Error searching games market collection: {str(e)}"

# ============================================================================
# Agentic RAG Demo
# ============================================================================

def rag_demo():
    """Demo: Agentic RAG (Retrieval-Augmented Generation).
    
    Demonstrates an advanced RAG workflow with:
    1. Multiple vector stores (Electric Vehicles and Gaming Industry)
    2. Tool-based retrieval from different knowledge bases
    3. Intelligent agent that selects appropriate tools
    4. Session-based memory management
    """
    global electric_vehicles_vector_store, games_market_vector_store, rag_llm
    
    print("=" * 70)
    print("Demo: Agentic RAG with Multiple Knowledge Bases")
    print("=" * 70)

    # Check for required API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("\nERROR: OPENAI_API_KEY not found in environment")
        print("Skipping Agentic RAG demo")
        return
    
    print("\n--- Step 1: Initialize Vector Store Manager ---")
    db = VectorStoreManager(api_key)
    loader_service = CorpusLoaderService(db)
    print("Vector store manager initialized")

    print("\n--- Step 2: Initialize LLM ---")
    rag_llm = LLM(
        model="gpt-4o-mini",
        temperature=0.3,
    )
    print("LLM initialized (gpt-4o-mini, temp=0.3)")

    print("\n--- Step 3: Load Gaming Industry PDF ---")
    games_pdf = "TheGamingIndustry2024.pdf"
    if not os.path.exists(games_pdf):
        print(f"WARNING: PDF file '{games_pdf}' not found")
        print("Skipping gaming industry vector store")
        games_market_vector_store = None
    else:
        try:
            games_market_vector_store = loader_service.load_pdf(
                store_name="games_market",
                pdf_path=games_pdf,
            )
            print(f"Loaded '{games_pdf}' into vector store")
            
            # Test query
            print("\n--- Step 4: Test Query on Gaming Industry ---")
            test_query = "What's the state of virtual reality"
            print(f"Query: {test_query}")
            results = games_market_vector_store.query(query_text=test_query, n_results=2)
            print(f"Retrieved {len(results['documents'][0])} relevant chunks")
        except Exception as e:
            print(f"ERROR loading gaming industry PDF: {e}")
            games_market_vector_store = None

    print("\n--- Step 5: Load Electric Vehicles PDF ---")
    ev_pdf = "GlobalEVOutlook2025.pdf"
    if not os.path.exists(ev_pdf):
        print(f"WARNING: PDF file '{ev_pdf}' not found")
        print("Skipping electric vehicles vector store")
        electric_vehicles_vector_store = None
    else:
        try:
            electric_vehicles_vector_store = loader_service.load_pdf(
                store_name="electric_vehicles",
                pdf_path=ev_pdf,
            )
            print(f"Loaded '{ev_pdf}' into vector store")
            
            # Test query
            print("\n--- Step 6: Test Query on Electric Vehicles ---")
            test_query = "What was the number of electric car sales and their market share in Brazil in 2024?"
            print(f"Query: {test_query}")
            results = electric_vehicles_vector_store.query(query_text=test_query, n_results=2)
            print(f"Retrieved {len(results['documents'][0])} relevant chunks")
        except Exception as e:
            print(f"ERROR loading electric vehicles PDF: {e}")
            electric_vehicles_vector_store = None

    # Check if at least one vector store was loaded
    if electric_vehicles_vector_store is None and games_market_vector_store is None:
        print("\nERROR: No vector stores were successfully loaded")
        print("Cannot proceed with Agentic RAG demo")
        return

    print("\n--- Step 7: Initialize Agentic RAG Agent ---")
    agentic_rag = Agent(
        model_name="gpt-4o-mini",
        tools=[search_global_ev_collection, search_games_market_report_collection],
        instructions=(
            "You are an Agentic RAG assistant that can intelligently decide which tools to use "
            "to answer user questions. Reason about the response, change the query and call the tool again if needed "
            "in order to get better results. Always explain your reasoning for tool selection and provide comprehensive answers."
        )
    )
    print("Agentic RAG agent initialized with 2 tools")

    def print_messages(messages: List[BaseMessage], query: str):
        """Helper function to print messages in a readable format"""
        print(f"\nQuery: {query}")
        print(f"Total messages: {len(messages)}")
        for i, m in enumerate(messages, 1):
            role = getattr(m, 'role', 'unknown')
            content = getattr(m, 'content', str(m))
            tool_calls = getattr(m, 'tool_calls', None)
            
            # Truncate long content
            content_preview = content[:150] + "..." if len(str(content)) > 150 else content
            
            print(f"\n  Message {i}:")
            print(f"    Role: {role}")
            print(f"    Content: {content_preview}")
            if tool_calls:
                print(f"    Tool Calls: {len(tool_calls)} tool(s) called")

    # Run test queries
    print("\n" + "=" * 70)
    print("Running Test Queries")
    print("=" * 70)

    print("=" * 70)

    # Test Query 1: Irrelevant question (should decline)
    print("\n--- Test Query 1: Irrelevant Question ---")
    query_1 = "Who won the 2025 Oscar for International Movie?"
    try:
        run_1 = agentic_rag.invoke(
            query=query_1, 
            session_id="oscar",
        )
        messages_1 = run_1.get_final_state()["messages"]
        print_messages(messages_1, query_1)
    except Exception as e:
        print(f"ERROR in Query 1: {e}")

    # Test Query 2: Electric vehicles question
    print("\n" + "-" * 70)
    print("\n--- Test Query 2: Electric Vehicles ---")
    query_2 = "Which two countries accounted for most of the electric car exports from the Asia Pacific region (excluding China) in 2024?"
    try:
        run_2 = agentic_rag.invoke(
            query=query_2,
            session_id="electric_car",
        )
        messages_2 = run_2.get_final_state()["messages"]
        print_messages(messages_2, query_2)
    except Exception as e:
        print(f"ERROR in Query 2: {e}")

    # Test Query 3: Gaming industry question
    print("\n" + "-" * 70)
    print("\n--- Test Query 3: Gaming Industry ---")
    query_3 = "How are games revolutionizing education?"
    try:
        run_3 = agentic_rag.invoke(
            query=query_3,
            session_id="games",
        )
        messages_3 = run_3.get_final_state()["messages"]
        print_messages(messages_3, query_3)
    except Exception as e:
        print(f"ERROR in Query 3: {e}")

    print("\n" + "=" * 70)
    print("Agentic RAG demo completed")
    print("=" * 70)
    print()

def main():
    """Main function to run Agentic RAG demo.
    
    Demonstrates advanced RAG systems with:
    1. Multiple knowledge bases (vector stores)
    2. Tool-based retrieval system
    3. Intelligent agent routing
    4. Session-based conversations
    """
    rag_demo()

if __name__ == "__main__":
    main()
