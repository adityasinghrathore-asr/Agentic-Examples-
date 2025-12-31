import os
from datetime import datetime
from typing import Dict
from dotenv import load_dotenv
from tavily import TavilyClient
from lib.agents import Agent
from lib.tooling import tool

load_dotenv()


# ============================================================================
# Web Search Tool Definition
# ============================================================================


@tool
def web_search(query: str, search_depth: str = "advanced") -> Dict:
    """Search the web using Tavily API.
    
    Args:
        query: Search query string
        search_depth: Type of search - 'basic' or 'advanced' (default: advanced)
        
    Returns:
        Dictionary containing search results with answer and sources
    """
    if TavilyClient is None:
        return {
            "error": "Tavily client not available. Please install: pip install tavily-python",
            "answer": "Unable to perform web search - Tavily package not installed",
            "results": []
        }
    
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return {
            "error": "TAVILY_API_KEY not found in environment",
            "answer": "Unable to perform web search - API key not configured",
            "results": []
        }
    
    try:
        client = TavilyClient(api_key=api_key)
        
        # Perform the search
        search_result = client.search(
            query=query,
            search_depth=search_depth,
            include_answer=True,
            include_raw_content=False,
            include_images=False
        )
        
        # Format the results
        formatted_results = {
            "answer": search_result.get("answer", ""),
            "results": search_result.get("results", []),
            "search_metadata": {
                "timestamp": datetime.now().isoformat(),
                "query": query,
                "search_depth": search_depth
            }
        }
        
        return formatted_results
    except Exception as e:
        return {
            "error": f"Search failed: {str(e)}",
            "answer": f"Unable to complete web search: {str(e)}",
            "results": []
        }


# ============================================================================
# Demo Implementation
# ============================================================================


def demo_web_search_agent():
    """Demo: Web Search API Integration.
    
    Demonstrates how an agent can perform web searches using Tavily API
    to answer questions with up-to-date information from the internet.
    """
    print("=" * 60)
    print("Demo: Web Search Agent with Tavily API")
    print("=" * 60)
    
    tools = [web_search]
    
    # Agent without web search capability
    simple_agent = Agent(
        model_name="gpt-4o-mini",
        instructions="You are a helpful assistant",
        tools=tools
    )

    # Agent with web search instructions
    web_agent = Agent(
        model_name="gpt-4o-mini",
        instructions=(
            "You are a web-aware assistant that can search for updated information. "
            "For each query, you will search the web for current information using "
            "Tavily's AI-optimized search and provide a comprehensive answer.\n"
            "Always cite your sources and explain any discrepancies found.\n"
            "Be particularly attentive to dates and time-sensitive information."
        ),
        tools=tools
    )

    # Demo 1: Time-sensitive query
    print("\n--- Query 1: Time-Sensitive Information ---")
    query1 = "Who won the 2024 Nobel Prize in Physics?"
    print(f"User: {query1}")
    run1 = web_agent.invoke(query=query1)
    final_state1 = run1.get_final_state()
    response1 = final_state1["messages"][-1].content
    print(f"\nBot: {response1}")
    print(f"\nMessages in session: {len(final_state1['messages'])}")

    # Demo 2: Recent developments
    print("\n--- Query 2: Recent Developments ---")
    query2 = "What are the most recent developments in AI technology?"
    print(f"User: {query2}")
    run2 = web_agent.invoke(query=query2)
    final_state2 = run2.get_final_state()
    response2 = final_state2["messages"][-1].content
    print(f"\nBot: {response2}")
    print(f"\nMessages in session: {len(final_state2['messages'])}")
    
    # Show summary
    print("\n" + "=" * 60)
    print("Demo completed successfully")
    print("=" * 60)
    print()

def main():
    """Main function to run the demo.
    
    Demonstrates how agents can integrate with web search APIs
    to access real-time information from the internet.
    """
    demo_web_search_agent()

if __name__ == "__main__":
    main()