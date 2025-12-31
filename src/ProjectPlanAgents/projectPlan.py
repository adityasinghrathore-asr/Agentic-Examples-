# Warning control
from asyncio import tasks
import warnings
warnings.filterwarnings('ignore')

# Load environment variables
from helper import load_env
load_env()

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

project = 'Website'
industry = 'Technology'
project_objectives = 'Create a website for a small business'
team_members = """
- John Doe (Project Manager)
- Jane Doe (Software Engineer)
- Bob Smith (Designer)
- Alice Johnson (QA Engineer)
- Tom Brown (QA Engineer)
"""
project_requirements = """
- Create a responsive design that works well on desktop and mobile devices
- Implement a modern, visually appealing user interface with a clean look
- Develop a user-friendly navigation system with intuitive menu structure
- Include an "About Us" page highlighting the company's history and values
- Design a "Services" page showcasing the business's offerings with descriptions
- Create a "Contact Us" page with a form and integrated map for communication
- Implement a blog section for sharing industry news and company updates
- Ensure fast loading times and optimize for search engines (SEO)
- Integrate social media links and sharing capabilities
- Include a testimonials section to showcase customer feedback and build trust
"""

# Format the dictionary as Markdown for a better display in Jupyter Lab
formatted_output = f"""
**Project Type:** {project}

**Project Objectives:** {project_objectives}

**Industry:** {industry}

**Team Members:**
{team_members}
**Project Requirements:**
{project_requirements}
"""
# Display the formatted output as Markdown
display(Markdown(formatted_output))

# Load configurations from YAML files
configs = {}
for config_type, file_path in files.items():
    with open(file_path, 'r') as file:
        configs[config_type] = yaml.safe_load(file)

# Assign loaded configurations to specific variables
agents_config = configs['agents']
tasks_config = configs['tasks']


class TaskEstimate(BaseModel):
    task_name: str = Field(..., description="Name of the task")
    estimated_time_hours: float = Field(..., description="Estimated time to complete the task in hours")
    required_resources: List[str] = Field(..., description="List of resources required to complete the task")

class Milestone(BaseModel):
    milestone_name: str = Field(..., description="Name of the milestone")
    tasks: List[str] = Field(..., description="List of task IDs associated with this milestone")

class ProjectPlan(BaseModel):
    tasks: List[TaskEstimate] = Field(..., description="List of tasks with their estimates")
    milestones: List[Milestone] = Field(..., description="List of project milestones")

def build_agents(project_type: str, industry: str, verbose: bool = True):
    # Agents are created based on the loaded configuration
    project_planning_agent = Agent(
        config=agents_config['project_planning_agent']
    )

    estimation_agent = Agent(
        config=agents_config['estimation_agent']
    )

    resource_allocation_agent = Agent(
        config=agents_config['resource_allocation_agent']
    )

    return project_planning_agent, estimation_agent, resource_allocation_agent



def build_tasks(project_planning_agent: Agent, estimation_agent: Agent, resource_allocation_agent: Agent, project_type: str, industry: str, project_requirements: str, team_members: str):
    # Tasks are created based on the loaded configuration
   
    # Creating Tasks
    task_breakdown = Task(
        config=tasks_config['task_breakdown'],
        agent=project_planning_agent
    )

    time_resource_estimation = Task(
        config=tasks_config['time_resource_estimation'],
        agent=estimation_agent
    )

    resource_allocation = Task(
        config=tasks_config['resource_allocation'],
        agent=resource_allocation_agent,
        output_pydantic=ProjectPlan # This is the structured output we want
    )
    return task_breakdown, time_resource_estimation, resource_allocation


def build_crew(inputs: dict, verbose: int = 2) -> Crew:
    project_planning_agent, estimation_agent, resource_allocation_agent = build_agents(project_type=inputs['project_type'], industry=inputs['industry'], verbose=bool(verbose))
    task_breakdown, time_resource_estimation, resource_allocation = build_tasks(
        project_planning_agent, estimation_agent, resource_allocation_agent, project_type=inputs['project_type'], industry=inputs['industry'], project_requirements=inputs['project_requirements'], team_members=inputs['team_members']
    )
    project_plan_crew = Crew(
        agents=[project_planning_agent, estimation_agent, resource_allocation_agent],
        tasks=[task_breakdown, time_resource_estimation, resource_allocation],
        verbose=bool(verbose),
    )

    return project_plan_crew


def run_topic(inputs: dict):
    #crew = build_crew(topic)

    project_plan_crew = build_crew(inputs=inputs, verbose=2)

    result = project_plan_crew.kickoff(inputs=inputs)
    return result, project_plan_crew



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
        
    # The given Python dictionary
    inputs = {
        'project_type': project,
        'project_objectives': project_objectives,
        'industry': industry,
        'team_members': team_members,
        'project_requirements': project_requirements
    }

    # Run the crew
    result, project_plan_crew = run_topic(inputs=inputs)
    #result = run_topic(topic)
    try:
        Markdown(result)
    except Exception:
        print(result)

    # Safely read usage metrics from crew or result
    usage = None
    if hasattr(project_plan_crew, 'usage_metrics') and project_plan_crew.usage_metrics is not None:
        usage = project_plan_crew.usage_metrics
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

    result.pydantic.dict()

    tasks = result.pydantic.dict()['tasks']
    df_tasks = pd.DataFrame(tasks)

    # Display the DataFrame as an HTML table
    df_tasks.style.set_table_attributes('border="1"').set_caption("Task Details").set_table_styles(
        [{'selector': 'th, td', 'props': [('font-size', '120%')]}]
    )

    milestones = result.pydantic.dict()['milestones']
    df_milestones = pd.DataFrame(milestones)

    # Display the DataFrame as an HTML table
    df_milestones.style.set_table_attributes('border="1"').set_caption("Task Details").set_table_styles(
        [{'selector': 'th, td', 'props': [('font-size', '120%')]}]
    )

    return result


if __name__ == "__main__":
    try:
        main()
    except Exception:
        import traceback

        traceback.print_exc()
        raise