# Warning control
#usage : python3 firstAgent.py --topic "The Impact of Artificial Intelligence on Modern Healthcare" 2>&1 | head -100
import warnings
warnings.filterwarnings('ignore')

from crewai import Agent, Task, Crew
from IPython.display import Markdown

import os
import argparse
from utils import get_openai_api_key


# Default model; can be overridden via environment
os.environ.setdefault("OPENAI_MODEL_NAME", "gpt-4-turbo")
topic = "The Impact of Artificial Intelligence on Modern Healthcare"


def build_agents(verbose: bool = True, topic: str = topic):
    print("Inside Planner Verbose:", verbose)
    planner = Agent(
        role="Content Planner",
        goal=f"Plan engaging and factually accurate content on {topic}",
        backstory=(
            f"You're working on planning a blog article "
            f"about the topic: {topic}. "
            f"You collect information that helps the "
            f"audience learn something and make informed decisions. "
            f"Your work is the basis for the Content Writer to write an article."
        ),
        allow_delegation=False,
        verbose=verbose,
    )

    writer = Agent(
        role="Content Writer",
        goal=(
            f"Write insightful and factually accurate "
            f"opinion piece about the topic: {topic}"
        ),
        backstory=(
            f"You're writing a new opinion piece about the topic: {topic}. "
            f"Base your writing on the Content Planner's outline and context. "
            f"Provide objective insights and mark opinions clearly."
        ),
        allow_delegation=False,
        verbose=verbose,
    )

    editor = Agent(
        role="Editor",
        goal=(
            "Edit a given blog post to align with the writing style of the organization."
        ),
        backstory=(
            "You are an editor who receives a blog post from the Content Writer. "
            "Review for journalistic best practices, balance, and brand voice."
        ),
        allow_delegation=False,
        verbose=verbose,
    )

    return planner, writer, editor


def build_tasks(planner: Agent, writer: Agent, editor: Agent, topic: str = topic):
    plan = Task(
        description=(
            f"1. Prioritize the latest trends, key players, and noteworthy news on {topic}.\n"
            f"2. Identify the target audience, considering their interests and pain points.\n"
            f"3. Develop a detailed content outline including an introduction, key points, and a call to action.\n"
            f"4. Include SEO keywords and relevant data or sources."
        ),
        expected_output=(
            "A comprehensive content plan document with an outline, audience analysis, "
            "SEO keywords, and resources."
        ),
        agent=planner,
    )

    write = Task(
        description=(
            f"1. Use the content plan to craft a compelling blog post on {topic}.\n"
            f"2. Incorporate SEO keywords naturally.\n"
            f"3. Sections/Subtitles are properly named in an engaging manner.\n"
            f"4. Ensure the post is structured with an engaging introduction, insightful body, and a summarizing conclusion.\n"
            f"5. Proofread for grammatical errors and alignment with the brand's voice.\n"
        ),
        expected_output=(
            "A well-written blog post in markdown format, ready for publication, "
            "each section should have 2 or 3 paragraphs."
        ),
        agent=writer,
    )

    edit = Task(
        description=(
            "Proofread the given blog post for grammatical errors and alignment with the brand's voice."
        ),
        expected_output=(
            "A well-written blog post in markdown format, ready for publication, "
            "each section should have 2 or 3 paragraphs."
        ),
        agent=editor,
    )

    return plan, write, edit


def build_crew(topic: str, verbose: int = 2) -> Crew:
    planner, writer, editor = build_agents(verbose=bool(verbose), topic=topic)
    plan, write, edit = build_tasks(planner, writer, editor, topic)
    crew = Crew(agents=[planner, writer, editor], tasks=[plan, write, edit], verbose=bool(verbose))
    return crew


def run_topic(topic: str):
    crew = build_crew(topic)
    return crew.kickoff(inputs={"topic": topic})
  
def main():
    parser = argparse.ArgumentParser(description="Run the content crew for a topic")
    parser.add_argument("--topic", default="The Impact of Artificial Intelligence on Modern Healthcare", help="Topic to create content for")
    args = parser.parse_args()
    topic = args.topic
    print("Topic111:", topic)

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
    result = run_topic(args.topic)
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

