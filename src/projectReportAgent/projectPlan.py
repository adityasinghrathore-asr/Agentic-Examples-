# Warning control
from asyncio import tasks
from unittest import result
import warnings
warnings.filterwarnings('ignore')

# Load environment variables
from helper import load_env, get_openai_api_key
load_env()
from crewai.tools import BaseTool
import json
import requests
from IPython.display import Image, display

import os
import yaml
from crewai import Agent, Process, Task, Crew
import pandas as pd

from typing import List
from pydantic import BaseModel, Field
from IPython.display import display, Markdown


os.environ['OPENAI_MODEL_NAME'] = 'gpt-4o-mini'
project_plan_crew = None
# Define file paths for YAML configurations (resolve relative to script location)
base_dir = os.path.dirname(__file__)
files = {
    'agents': os.path.join(base_dir, 'config', 'agents.yaml'),
    'tasks': os.path.join(base_dir, 'config', 'tasks.yaml')
}

# Load and display the image (resolve path relative to this script; skip if missing)
try:
    image_path = os.path.join(base_dir, 'trello.png')
    if os.path.exists(image_path):
        trello_image = Image(filename=image_path)
        display(trello_image)
    else:
        print(f"Info: trello.png not found at {image_path}; skipping image display.")
except Exception as e:
    print(f"Warning: failed to load trello image: {e}")

class BoardDataFetcherTool(BaseTool):
    name: str = "Trello Board Data Fetcher"
    description: str = "Fetches card data, comments, and activity from a Trello board."

    api_key: str = os.environ['TRELLO_API_KEY']
    api_token: str = os.environ['TRELLO_API_TOKEN']
    board_id: str = os.environ['TRELLO_BOARD_ID']

    def _run(self) -> dict:
        """
        Fetch all cards from the specified Trello board.
        """
        url = f"{os.getenv('DLAI_TRELLO_BASE_URL', 'https://api.trello.com')}/1/boards/{self.board_id}/cards"

        query = {
            'key': self.api_key,
            'token': self.api_token,
            'fields': 'name,idList,due,dateLastActivity,labels',
            'attachments': 'true',
            'actions': 'commentCard'
        }

        response = requests.get(url, params=query)

        if response.status_code == 200:
            return response.json()
        else:
            # Fallback in case of timeouts or other issues
            return json.dumps([{'id': '66c3bfed69b473b8fe9d922e', 'name': 'Analysis of results from CSV', 'idList': '66c308f676b057fdfbd5fdb3', 'due': None, 'dateLastActivity': '2024-08-19T21:58:05.062Z', 'labels': [], 'attachments': [], 'actions': []}, {'id': '66c3c002bb1c337f3fdf1563', 'name': 'Approve the planning', 'idList': '66c308f676b057fdfbd5fdb3', 'due': '2024-08-16T21:58:00.000Z', 'dateLastActivity': '2024-08-19T21:58:57.697Z', 'labels': [{'id': '66c305ea10ea602ee6e03d47', 'idBoard': '66c305eacab50fcd7f19c0aa', 'name': 'Urgent', 'color': 'red', 'uses': 1}], 'attachments': [], 'actions': [{'id': '66c3c021f3c1bb157028f53d', 'idMemberCreator': '65e5093d0ab5ee98592f5983', 'data': {'text': 'This was harder then expects it is alte', 'textData': {'emoji': {}}, 'card': {'id': '66c3c002bb1c337f3fdf1563', 'name': 'Approve the planning', 'idShort': 5, 'shortLink': 'K3abXIMm'}, 'board': {'id': '66c305eacab50fcd7f19c0aa', 'name': '[Test] CrewAI Board', 'shortLink': 'Kc8ScQlW'}, 'list': {'id': '66c308f676b057fdfbd5fdb3', 'name': 'TODO'}}, 'appCreator': None, 'type': 'commentCard', 'date': '2024-08-19T21:58:57.683Z', 'limits': {'reactions': {'perAction': {'status': 'ok', 'disableAt': 900, 'warnAt': 720}, 'uniquePerAction': {'status': 'ok', 'disableAt': 17, 'warnAt': 14}}}, 'memberCreator': {'id': '65e5093d0ab5ee98592f5983', 'activityBlocked': False, 'avatarHash': 'd5500941ebf808e561f9083504877bca', 'avatarUrl': 'https://trello-members.s3.amazonaws.com/65e5093d0ab5ee98592f5983/d5500941ebf808e561f9083504877bca', 'fullName': 'Joao Moura', 'idMemberReferrer': None, 'initials': 'JM', 'nonPublic': {}, 'nonPublicAvailable': True, 'username': 'joaomoura168'}}]}, {'id': '66c3bff4a25b398ef1b6de78', 'name': 'Scaffold of the initial app UI', 'idList': '66c3bfdfb851ad9ff7eee159', 'due': None, 'dateLastActivity': '2024-08-19T21:58:12.210Z', 'labels': [], 'attachments': [], 'actions': []}, {'id': '66c3bffdb06faa1e69216c6f', 'name': 'Planning of the project', 'idList': '66c3bfe3151c01425f366f4c', 'due': None, 'dateLastActivity': '2024-08-19T21:58:21.081Z', 'labels': [], 'attachments': [], 'actions': []}])


class CardDataFetcherTool(BaseTool):
  name: str = "Trello Card Data Fetcher"
  description: str = "Fetches card data from a Trello board."

  api_key: str = os.environ['TRELLO_API_KEY']
  api_token: str = os.environ['TRELLO_API_TOKEN']

  def _run(self, card_id: str) -> dict:
    url = f"{os.getenv('DLAI_TRELLO_BASE_URL', 'https://api.trello.com')}/1/cards/{card_id}"
    query = {
      'key': self.api_key,
      'token': self.api_token
    }
    response = requests.get(url, params=query)

    if response.status_code == 200:
      return response.json()
    else:
      # Fallback in case of timeouts or other issues
      return json.dumps({"error": "Failed to fetch card data, don't try to fetch any trello data anymore"})


# Load configurations from YAML files
configs = {}
for config_type, file_path in files.items():
    with open(file_path, 'r') as file:
        configs[config_type] = yaml.safe_load(file)

# Assign loaded configurations to specific variables
agents_config = configs['agents']
tasks_config = configs['tasks']




def build_agents(verbose: bool = True):
    data_collection_agent = Agent(
        config=agents_config['data_collection_agent'],
        tools=[BoardDataFetcherTool(), CardDataFetcherTool()]
    )

    analysis_agent = Agent(
        config=agents_config['analysis_agent']
    )

    return data_collection_agent, analysis_agent



def build_tasks(data_collection_agent: Agent, analysis_agent: Agent):
    data_collection = Task(
        config=tasks_config['data_collection'],
        agent=data_collection_agent
    )

    data_analysis = Task(
        config=tasks_config['data_analysis'],
        agent=analysis_agent
    )

    report_generation = Task(
        config=tasks_config['report_generation'],
        agent=analysis_agent,
    )
    return data_collection, data_analysis, report_generation


def build_crew(verbose: int = 2) -> Crew:
    data_collection_agent, analysis_agent = build_agents(verbose=bool(verbose))
    data_collection, data_analysis, report_generation = build_tasks(
        data_collection_agent, analysis_agent
    )
    project_report_crew = Crew(
        agents=[data_collection_agent, analysis_agent],
        tasks=[data_collection, data_analysis, report_generation],
        verbose=bool(verbose),
    )

    return project_report_crew


def run_topic():
    #crew = build_crew(topic)

    project_report_crew = build_crew(verbose=2)

    result = project_report_crew.kickoff()
    return result, project_report_crew



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
        


    # Run the crew
    result, project_report_crew = run_topic()
    #result = run_topic(topic)
    try:
        Markdown(result)
    except Exception:
        print(result)

    # Safely read usage metrics from crew or result
    usage = None
    if hasattr(project_report_crew, 'usage_metrics') and project_report_crew.usage_metrics is not None:
        usage = project_report_crew.usage_metrics
    elif hasattr(result, 'usage_metrics') and result.usage_metrics is not None:
        usage = result.usage_metrics

    if usage is not None:
        costs = 0.150 * (usage.prompt_tokens + usage.completion_tokens) / 1_000_000
        print(f"Total costs: ${costs:.4f}")

        # Convert UsageMetrics instance to a DataFrame
        df_usage_metrics = pd.DataFrame([usage.dict()])
        df_usage_metrics
    else:
        print("Usage metrics not available; skipping cost calculation.")

    markdown  = result.raw
    Markdown(markdown)

   
    return result


if __name__ == "__main__":
    try:
        main()
    except Exception:
        import traceback

        traceback.print_exc()
        raise