import warnings
warnings.filterwarnings('ignore')

from crewai.tools import BaseTool
from pydantic import BaseModel
from crewai import Crew, Process
from langchain_openai import ChatOpenAI

from crewai import Agent, Task, Crew
from IPython.display import Markdown
import json
from pprint import pprint
from crewai_tools import (
    SerperDevTool,
    ScrapeWebsiteTool,
    WebsiteSearchTool,
    DirectoryReadTool,
    FileReadTool,
)

import os
import argparse
from utils import get_openai_api_key, get_serper_api_key
# Default model; can be overridden via environment
os.environ.setdefault("OPENAI_MODEL_NAME", "gpt-3.5-turbo")
# Initialize the tools
search_tool = SerperDevTool()
scrape_tool = ScrapeWebsiteTool()


def build_agents(verbose: bool = True):

    data_analyst_agent = Agent(
        role="Data Analyst",
        goal="Monitor and analyze market data in real-time "
            "to identify trends and predict market movements.",
        backstory="Specializing in financial markets, this agent "
                "uses statistical modeling and machine learning "
                "to provide crucial insights. With a knack for data, "
                "the Data Analyst Agent is the cornerstone for "
                "informing trading decisions.",
        verbose=True,
        allow_delegation=True,
        tools = [scrape_tool, search_tool]
    )

    trading_strategy_agent = Agent(
        role="Trading Strategy Developer",
        goal="Develop and test various trading strategies based "
            "on insights from the Data Analyst Agent.",
        backstory="Equipped with a deep understanding of financial "
                "markets and quantitative analysis, this agent "
                "devises and refines trading strategies. It evaluates "
                "the performance of different approaches to determine "
                "the most profitable and risk-averse options.",
        verbose=True,
        allow_delegation=True,
        tools = [scrape_tool, search_tool]
    )

    execution_agent = Agent(
        role="Trade Advisor",
        goal="Suggest optimal trade execution strategies "
            "based on approved trading strategies.",
        backstory="This agent specializes in analyzing the timing, price, "
                "and logistical details of potential trades. By evaluating "
                "these factors, it provides well-founded suggestions for "
                "when and how trades should be executed to maximize "
                "efficiency and adherence to strategy.",
        verbose=True,
        allow_delegation=True,
        tools = [scrape_tool, search_tool]
    )

    risk_management_agent = Agent(
        role="Risk Advisor",
        goal="Evaluate and provide insights on the risks "
            "associated with potential trading activities.",
        backstory="Armed with a deep understanding of risk assessment models "
                "and market dynamics, this agent scrutinizes the potential "
                "risks of proposed trades. It offers a detailed analysis of "
                "risk exposure and suggests safeguards to ensure that "
                "trading activities align with the firm’s risk tolerance.",
        verbose=True,
        allow_delegation=True,
        tools = [scrape_tool, search_tool]
    )
    return data_analyst_agent, trading_strategy_agent, execution_agent, risk_management_agent

def build_tasks(data_analyst_agent: Agent, trading_strategy_agent: Agent, execution_agent: Agent, risk_management_agent: Agent, inputs: dict):
    
    # Task for Data Analyst Agent: Analyze Market Data
    data_analysis_task = Task(
        description=(
            "Continuously monitor and analyze market data for "
            "the selected stock {inputs['stock_selection']}. "
            "Use statistical modeling and machine learning to "
            "identify trends and predict market movements."
        ),
        expected_output=(
            "Insights and alerts about significant market "
            "opportunities or threats for {inputs['stock_selection']}."
        ),
        agent=data_analyst_agent,
    )

    # Task for Trading Strategy Agent: Develop Trading Strategies
    strategy_development_task = Task(
        description=(
            "Develop and refine trading strategies based on "
            "the insights from the Data Analyst and "
            "user-defined risk tolerance ({inputs['risk_tolerance']}). "
            "Consider trading preferences ({inputs['trading_strategy_preference']})."
        ),
        expected_output=(
            "A set of potential trading strategies for {inputs['stock_selection']} "
            "that align with the user's risk tolerance."
        ),
        agent=trading_strategy_agent,
    )

    # Task for Trade Advisor Agent: Plan Trade Execution
    execution_planning_task = Task(
        description=(
            "Analyze approved trading strategies to determine the "
            "best execution methods for {inputs['stock_selection']}, "
            "considering current market conditions and optimal pricing."
        ),
        expected_output=(
            "Detailed execution plans suggesting how and when to "
            "execute trades for {inputs['stock_selection']}."
        ),
        agent=execution_agent,
    )

    # Task for Risk Advisor Agent: Assess Trading Risks
    risk_assessment_task = Task(
        description=(
            "Evaluate the risks associated with the proposed trading "
            "strategies and execution plans for {inputs['stock_selection']}. "
            "Provide a detailed analysis of potential risks "
            "and suggest mitigation strategies."
        ),
        expected_output=(
            "A comprehensive risk analysis report detailing potential "
            "risks and mitigation recommendations for {inputs['stock_selection']}."
        ),
        agent=risk_management_agent,
    )
    return data_analysis_task, strategy_development_task, execution_planning_task, risk_assessment_task

def build_crew(inputs: dict, verbose: int = 2) -> Crew:
    data_analyst_agent, trading_strategy_agent, execution_agent, risk_management_agent = build_agents(verbose=bool(verbose))
    data_analysis_task, strategy_development_task, execution_planning_task, risk_assessment_task = build_tasks(
        data_analyst_agent, trading_strategy_agent, execution_agent, risk_management_agent, inputs=inputs
    )
    financial_trading_crew = Crew(
        agents=[data_analyst_agent, trading_strategy_agent, execution_agent, risk_management_agent],
        tasks=[data_analysis_task, strategy_development_task, execution_planning_task, risk_assessment_task],
        manager_llm=ChatOpenAI(model="gpt-3.5-turbo", temperature=0.7),
        verbose=bool(verbose),
        process=Process.hierarchical,
        memory=True
    )

    return financial_trading_crew


def run_topic(inputs: dict):
    #crew = build_crew(topic)

    financial_trading_crew = build_crew(inputs=inputs, verbose=2)
 
    return financial_trading_crew.kickoff(inputs=inputs)

def main():
    #parser = argparse.ArgumentParser(description="Run the content crew for a topic")
    #parser.add_argument("--topic", default="The Impact of Artificial Intelligence on Modern Healthcare", help="Topic to create content for")
    #args = parser.parse_args()
    #topic = args.topic
    #print("Topic111:", topic)

    # Ensure API key available: prefer environment, then utils.get_openai_api_key()
    if not os.environ.get("OPENAI_API_KEY"):
        try:
            key = get_openai_api_key()
            if key:
                os.environ["OPENAI_API_KEY"] = key
            else:
                raise ValueError(
                    "OPENAI_API_KEY not found. Please set it in:\n"
                    "1. Environment variable: export OPENAI_API_KEY=your-key\n"
                    "2. Create a .env file in the project root with: OPENAI_API_KEY=your-key\n"
                    "3. Create ~/.openai_api_key file with your key"
                )
        except ValueError:
            raise
        except Exception as e:
            raise ValueError(
                f"Failed to retrieve OPENAI_API_KEY: {e}\n"
                "Please set it in:\n"
                "1. Environment variable: export OPENAI_API_KEY=your-key\n"
                "2. Create a .env file in the project root with: OPENAI_API_KEY=your-key\n"
                "3. Create ~/.openai_api_key file with your key"
            )
        
    if not os.environ.get("SERPER_API_KEY"):
        try:
            key = get_serper_api_key()
            if key:
                os.environ["SERPER_API_KEY"] = key
            else:
                raise ValueError(
                    "SERPER_API_KEY not found. Please set it in:\n"
                    "1. Environment variable: export SERPER_API_KEY=your-key\n"
                    "2. Create a .env file in the project root with: SERPER_API_KEY=your-key\n"
                    "3. Create ~/.serper_api_key file with your key"
                )
        except ValueError:
            raise
        except Exception as e:
            raise ValueError(
                f"Failed to retrieve SERPER_API_KEY: {e}\n"
                "Please set it in:\n"
                "1. Environment variable: export SERPER_API_KEY=your-key\n"
                "2. Create a .env file in the project root with: SERPER_API_KEY=your-key\n"
                "3. Create ~/.serper_api_key file with your key"
            )
    #args.topic = "Artificial Intelligence in Healthcare: Transforming Patient Care and Medical Research"
    
    # Example data for kicking off the process
    financial_trading_inputs = {
        'stock_selection': 'AAPL',
        'initial_capital': '100000',
        'risk_tolerance': 'Medium',
        'trading_strategy_preference': 'Day Trading',
        'news_impact_consideration': True
    }
    
    result = run_topic(inputs=financial_trading_inputs)
    #result = run_topic(topic)

    try:
        Markdown(result)
    except Exception:
        print(result)

    return result


if __name__ == "__main__":
    try:
        main()
    except Exception:
        import traceback

        traceback.print_exc()
        raise