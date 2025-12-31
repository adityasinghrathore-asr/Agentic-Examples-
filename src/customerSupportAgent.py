# Warning control
#usage : python3 firstAgent.py --topic "The Impact of Artificial Intelligence on Modern Healthcare" 2>&1 | head -100
import warnings
warnings.filterwarnings('ignore')

from crewai import Agent, Task, Crew
from IPython.display import Markdown
from crewai_tools import SerperDevTool, \
                         ScrapeWebsiteTool, \
                         WebsiteSearchTool

import os
import argparse
from utils import get_openai_api_key


# Default model; can be overridden via environment
os.environ.setdefault("OPENAI_MODEL_NAME", "gpt-3.5-turbo")

def build_agents(verbose: bool = True, customer: str = "Acme Corp"):

    support_agent = Agent(
        role="Senior Support Representative",
        goal="Be the most friendly and helpful "
            "support representative in your team",
        backstory=(
            "You work at crewAI (https://crewai.com) and "
            " are now working on providing "
            "support to {customer}, a super important customer "
            " for your company."
            "You need to make sure that you provide the best support!"
            "Make sure to provide full complete answers, "
            " and make no assumptions."
        ),
        allow_delegation=False,
        verbose=verbose
    )

    support_quality_assurance_agent = Agent(
        role="Support Quality Assurance Specialist",
        goal="Get recognition for providing the "
             "best support quality assurance in your team",
        backstory=(
            "You work at crewAI (https://crewai.com) and "
            "are now working with your team "
            "on a request from {customer} ensuring that "
            "the support representative is "
            "providing the best support possible.\n"
            "You need to make sure that the support representative "
            "is providing full complete answers, and make no assumptions."
        ),
        allow_delegation=False,
        verbose=verbose
    )
    
    return support_agent, support_quality_assurance_agent
    

def build_tasks(support_agent: Agent,  support_quality_assurance_agent: Agent, customer: str="", inquiry: str = "", person: str = "Alex"):

    docs_scrape_tool = ScrapeWebsiteTool(
        website_url="https://docs.crewai.com/how-to/Creating-a-Crew-and-kick-it-off/"
    )


    inquiry_resolution = Task(
        description=(
            f"{customer} just reached out with a super important ask:\n"
            f"{inquiry}\n\n"
            f"{person} from {customer} is the one that reached out. "
            "Make sure to use everything you know "
            "to provide the best support possible."
            "You must strive to provide a complete "
            "and accurate response to the customer's inquiry."
        ),
        expected_output=(
            "A detailed, informative response to the "
            "customer's inquiry that addresses "
            "all aspects of their question.\n"
            "The response should include references "
            "to everything you used to find the answer, "
            "including external data or solutions. "
            "Ensure the answer is complete, "
            "leaving no questions unanswered, and maintain a helpful and friendly "
            "tone throughout."
        ),
        tools=[docs_scrape_tool],
        agent=support_agent,
    )

    quality_assurance_review = Task(
        description=(
            f"Review the response drafted by the Senior Support Representative for {customer}'s inquiry. "
            "Ensure that the answer is comprehensive, accurate, and adheres to the "
            "high-quality standards expected for customer support.\n"
            "Verify that all parts of the customer's inquiry "
            "have been addressed "
            "thoroughly, with a helpful and friendly tone.\n"
            "Check for references and sources used to "
            " find the information, "
            "ensuring the response is well-supported and "
            "leaves no questions unanswered."
        ),
        expected_output=(
            "A final, detailed, and informative response "
            "ready to be sent to the customer.\n"
            "This response should fully address the "
            "customer's inquiry, incorporating all "
            "relevant feedback and improvements.\n"
            "Don't be too formal, we are a chill and cool company "
            "but maintain a professional and friendly tone throughout."
        ),
        agent=support_quality_assurance_agent,
    )
    
    return inquiry_resolution, quality_assurance_review

def build_crew(customer: str, inquiry: str, person: str, verbose: int = 2) -> Crew:
    support_agent, support_quality_assurance_agent = build_agents(verbose=bool(verbose), customer=customer)
    inquiry_resolution,  quality_assurance_review = build_tasks(support_agent, support_quality_assurance_agent, customer, inquiry, person)
    crew = Crew(agents=[support_agent, support_quality_assurance_agent], tasks=[inquiry_resolution, quality_assurance_review], verbose=bool(verbose), memory=True)
   
    return crew


def run_topic(inputs: dict):
    #crew = build_crew(topic)

    crew = build_crew(inputs["customer"], inputs["inquiry"], inputs["person"])
 
    return crew.kickoff(inputs=inputs)


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
        
   
    #args.topic = "Artificial Intelligence in Healthcare: Transforming Patient Care and Medical Research"
    
    inputs = {
    "customer": "DeepLearningAI",
    "person": "Andrew Ng",
    "inquiry": "I need help with setting up a Crew "
               "and kicking it off, specifically "
               "how can I add memory to my crew? "
               "Can you provide guidance?"
    }
    
    result = run_topic(inputs)
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