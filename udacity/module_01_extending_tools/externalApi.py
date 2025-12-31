import os
import random
from typing import List
import requests
from dotenv import load_dotenv

from lib.agents import Agent
from lib.messages import BaseMessage
from lib.tooling import tool

load_dotenv()


# ============================================================================
# External API Tool Definitions
# ============================================================================


@tool
def get_weather(city: str) -> dict:
    """Get current weather for a city using OpenWeather API.
    
    Args:
        city: Name of the city to get weather for
        
    Returns:
        Dictionary containing weather data including temperature, conditions, etc.
    """
    API_KEY = os.getenv("OPENWEATHER_API_KEY")
    if not API_KEY:
        return {"error": "OPENWEATHER_API_KEY not found in environment"}
    
    BASE_URL = "https://api.openweathermap.org/data/2.5/weather"
    
    params = {
        "q": city,
        "appid": API_KEY,
        "units": "metric"
    }
    
    try:
        response = requests.get(BASE_URL, params=params)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        return {"error": f"Failed to fetch weather: {str(e)}"}


@tool
def get_exchange_rate(from_currency: str = "USD") -> dict:
    """Get latest exchange rates from a base currency.
    
    Args:
        from_currency: Base currency code (default: USD)
        
    Returns:
        Dictionary containing exchange rates for various currencies
    """
    API_KEY = os.getenv("EXCHANGERATE_API_KEY")
    if not API_KEY:
        return {"error": "EXCHANGERATE_API_KEY not found in environment"}
    
    BASE_URL = "https://v6.exchangerate-api.com/v6"
    
    url = f"{BASE_URL}/{API_KEY}/latest/{from_currency}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        return {"error": f"Failed to fetch exchange rates: {str(e)}"}


@tool
def get_random_pokemon() -> dict:
    """Get a random Pokemon from the original 151.
    
    Returns:
        Dictionary containing name and URL for a random Pokemon
    """
    URL = "https://pokeapi.co/api/v2/pokemon?limit=151"
    
    try:
        response = requests.get(URL)
        response.raise_for_status()
        return random.choice(response.json()['results'])
    except requests.RequestException as e:
        return {"error": f"Failed to fetch Pokemon: {str(e)}"}


# ============================================================================
# Demo Implementation
# ============================================================================



def demo_external_api_agent():
    """Demo: External API Integration with Multiple Tools.
    
    Demonstrates how an agent can interact with external APIs including:
    - Weather data (OpenWeather API)
    - Currency exchange rates (ExchangeRate API)
    - Random Pokemon data (PokeAPI)
    """
    print("=" * 60)
    print("Demo: External API Integration")
    print("=" * 60)
    
    # Initialize agent with tools
    tools = [get_weather, get_exchange_rate, get_random_pokemon]
    agent = Agent(
        model_name="gpt-4o-mini",
        instructions=(
            "You are an assistant that can help with:\n"
            "1. Getting weather information for cities\n"
            "2. Checking currency exchange rates\n"
            "3. Getting random Pokemon information\n"
            "Use the available tools to help answer questions about these topics.\n"
            "Provide clear and concise responses based on the API data."
        ),
        tools=tools
    )
    
    session_id = "external_api_demo"
    
    # Query 1: Weather
    print("\n--- Query 1: Weather Information ---")
    query1 = "What's the weather like in London?"
    print(f"User: {query1}")
    run1 = agent.invoke(query=query1, session_id=session_id)
    final_state1 = run1.get_final_state()
    response1 = final_state1["messages"][-1].content
    print(f"Bot: {response1}")
    print(f"Messages in session: {len(final_state1['messages'])}")

    # Query 2: Exchange Rate
    print("\n--- Query 2: Currency Exchange ---")
    query2 = "What's the exchange rate from USD to EUR?"
    print(f"User: {query2}")
    run2 = agent.invoke(query=query2, session_id=session_id)
    final_state2 = run2.get_final_state()
    response2 = final_state2["messages"][-1].content
    print(f"Bot: {response2}")
    print(f"Messages in session: {len(final_state2['messages'])}")

    # Query 3: Random Pokemon
    print("\n--- Query 3: Random Pokemon ---")
    query3 = "Pick one random Pokemon!"
    print(f"User: {query3}")
    run3 = agent.invoke(query=query3, session_id=session_id)
    final_state3 = run3.get_final_state()
    response3 = final_state3["messages"][-1].content
    print(f"Bot: {response3}")
    print(f"Messages in session: {len(final_state3['messages'])}")

    # Summary
    print("\n" + "=" * 60)
    print("Session Summary")
    print("=" * 60)
    runs = agent.get_session_runs(session_id)
    print(f"Total runs in session '{session_id}': {len(runs)}")
    for i, run_object in enumerate(runs, 1):
        metadata = run_object.metadata
        print(f"\nRun {i}:")
        print(f"  Run ID: {metadata.get('run_id', 'N/A')[:8]}...")
        print(f"  Start: {metadata.get('start_timestamp', 'N/A')}")
        print(f"  Messages: {metadata.get('snapshot_counts', 0)}")
    print()


def main():
    """Main function to run the demo.
    
    Demonstrates how agents can integrate with external APIs
    to fetch real-time data like weather, currency rates, and more.
    """
    demo_external_api_agent()

if __name__ == "__main__":
    main()