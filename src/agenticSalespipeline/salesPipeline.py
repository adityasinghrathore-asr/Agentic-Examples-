# Warning control
import asyncio
import textwrap
import warnings
warnings.filterwarnings('ignore')

# Load environment variables
from helper import load_env, get_openai_api_key, get_serper_api_key
load_env()


import os
import yaml
from crewai import Agent, Task, Crew, Flow
from crewai.flow.flow import listen, start
from crewai_tools import SerperDevTool, ScrapeWebsiteTool
from pydantic import BaseModel, Field
from typing import Optional, List
from IPython.display import display, HTML, IFrame
import pandas as pd


os.environ['OPENAI_MODEL_NAME'] = 'gpt-4o-mini'


# Define file paths for YAML configurations
base_dir = os.path.dirname(__file__)
files = {
    'lead_agents': os.path.join(base_dir, 'config', 'lead_qualification_agents.yaml'),
    'lead_tasks': os.path.join(base_dir, 'config', 'lead_qualification_tasks.yaml'),
    'email_agents': os.path.join(base_dir, 'config', 'email_engagement_agents.yaml'),
    'email_tasks': os.path.join(base_dir, 'config', 'email_engagement_tasks.yaml')
}

# Load configurations from YAML files
configs = {}
for config_type, file_path in files.items():
    with open(file_path, 'r') as file:
        configs[config_type] = yaml.safe_load(file)

lead_agents_config = configs['lead_agents']
lead_tasks_config = configs['lead_tasks']
email_agents_config = configs['email_agents']
email_tasks_config = configs['email_tasks']


# ======================== Pydantic Models ========================

class LeadPersonalInfo(BaseModel):
    name: str = Field(..., description="The full name of the lead.")
    job_title: str = Field(..., description="The job title of the lead.")
    role_relevance: int = Field(..., ge=0, le=10, description="Score for lead role relevance (0-10).")
    professional_background: Optional[str] = Field(..., description="Lead's professional background.")


class CompanyInfo(BaseModel):
    company_name: str = Field(..., description="The name of the company.")
    industry: str = Field(..., description="The industry of the company.")
    company_size: int = Field(..., description="Number of employees.")
    revenue: Optional[float] = Field(None, description="Annual revenue.")
    market_presence: int = Field(..., ge=0, le=10, description="Market presence score (0-10).")


class LeadScore(BaseModel):
    score: int = Field(..., ge=0, le=100, description="Final lead score (0-100).")
    scoring_criteria: List[str] = Field(..., description="Criteria used for scoring.")
    validation_notes: Optional[str] = Field(None, description="Validation notes.")


class LeadScoringResult(BaseModel):
    personal_info: LeadPersonalInfo
    company_info: CompanyInfo
    lead_score: LeadScore


# ======================== Lead Qualification ========================

def build_lead_agents(verbose: bool = True):
    """Build agents for lead qualification."""
    lead_data_agent = Agent(
        config=lead_agents_config['lead_data_agent'],
        tools=[SerperDevTool(), ScrapeWebsiteTool()]
    )

    cultural_fit_agent = Agent(
        config=lead_agents_config['cultural_fit_agent'],
        tools=[SerperDevTool(), ScrapeWebsiteTool()]
    )

    scoring_validation_agent = Agent(
        config=lead_agents_config['scoring_validation_agent'],
        tools=[SerperDevTool(), ScrapeWebsiteTool()]
    )

    return lead_data_agent, cultural_fit_agent, scoring_validation_agent


def build_lead_qualification_tasks(
    lead_data_agent: Agent,
    cultural_fit_agent: Agent,
    scoring_validation_agent: Agent
):
    """Build tasks for lead qualification."""
    lead_data_task = Task(
        config=lead_tasks_config['lead_data_collection'],
        agent=lead_data_agent
    )

    cultural_fit_task = Task(
        config=lead_tasks_config['cultural_fit_analysis'],
        agent=cultural_fit_agent
    )

    scoring_validation_task = Task(
        config=lead_tasks_config['lead_scoring_and_validation'],
        agent=scoring_validation_agent,
        context=[lead_data_task, cultural_fit_task],
        output_pydantic=LeadScoringResult
    )
    
    return lead_data_task, cultural_fit_task, scoring_validation_task


def build_lead_crew(inputs: dict, verbose: int = 2) -> Crew:
    """Build lead qualification crew."""
    lead_data_agent, cultural_fit_agent, scoring_validation_agent = build_lead_agents(
        verbose=bool(verbose)
    )
    lead_data_task, cultural_fit_task, scoring_validation_task = build_lead_qualification_tasks(
        lead_data_agent, cultural_fit_agent, scoring_validation_agent
    )
    
    lead_crew = Crew(
        agents=[lead_data_agent, cultural_fit_agent, scoring_validation_agent],
        tasks=[lead_data_task, cultural_fit_task, scoring_validation_task],
        verbose=bool(verbose),
    )

    return lead_crew


def run_lead(inputs):
    """Run lead qualification crew. Accepts a dict or a list of leads."""
    lead_crew = build_lead_crew(inputs=inputs, verbose=2)

    # Single-dict case
    if isinstance(inputs, dict):
        kickoff_inputs = inputs if 'lead_data' in inputs else {'lead_data': inputs}
        result = lead_crew.kickoff(inputs=kickoff_inputs)
        return result, lead_crew

    # List case: run kickoff once per lead and collect results
    if isinstance(inputs, list):
        results = []
        for item in inputs:
            kickoff_inputs = item if (isinstance(item, dict) and 'lead_data' in item) else {'lead_data': item}
            results.append(lead_crew.kickoff(inputs=kickoff_inputs))
        return results, lead_crew

    # Fallback for other types
    result = lead_crew.kickoff(inputs={'lead_data': inputs})
    return result, lead_crew

# ======================== Email Engagement ========================

def build_email_agents(verbose: bool = True):
    """Build agents for email engagement."""
    email_content_specialist = Agent(
        config=email_agents_config['email_content_specialist']
    )

    engagement_strategist = Agent(
        config=email_agents_config['engagement_strategist']
    )
    
    return email_content_specialist, engagement_strategist


def build_email_tasks(
    email_content_specialist: Agent,
    engagement_strategist: Agent
):
    """Build tasks for email engagement."""
    email_drafting = Task(
        config=email_tasks_config['email_drafting'],
        agent=email_content_specialist
    )

    engagement_optimization = Task(
        config=email_tasks_config['engagement_optimization'],
        agent=engagement_strategist
    )
    
    return email_drafting, engagement_optimization


def build_email_crew(inputs: dict, verbose: int = 2) -> Crew:
    """Build email engagement crew."""
    email_content_specialist, engagement_strategist = build_email_agents(
        verbose=bool(verbose)
    )
    email_drafting, engagement_optimization = build_email_tasks(
        email_content_specialist, engagement_strategist
    )
    
    email_crew = Crew(
        agents=[email_content_specialist, engagement_strategist],
        tasks=[email_drafting, engagement_optimization],
        verbose=bool(verbose),
    )

    return email_crew


def run_email(inputs):
    """Run email engagement crew. Accepts a dict or a list of email inputs."""
    email_crew = build_email_crew(inputs=inputs, verbose=2)

    if isinstance(inputs, dict):
        result = email_crew.kickoff(inputs=inputs)
        return result, email_crew

    if isinstance(inputs, list):
        results = []
        for item in inputs:
            kickoff_inputs = item if isinstance(item, dict) else {'email': item}
            results.append(email_crew.kickoff(inputs=kickoff_inputs))
        return results, email_crew

    result = email_crew.kickoff(inputs={'email': inputs})
    return result, email_crew


# ======================== Sales Pipeline Flow ========================

class SalesPipeline(Flow):
    """Main sales pipeline flow."""

    @start()
    def fetch_leads(self):
        """Fetch leads from database."""
        leads = [
            {
                "lead_data": {
                    "name": "João Moura",
                    "job_title": "Director of Engineering",
                    "company": "Clearbit",
                    "email": "joao@clearbit.com",
                    "use_case": "Using AI Agent to do better data enrichment."
                },
            },
        ]
        return leads

    @listen(fetch_leads)
    def score_leads(self, leads):
        """Score leads using qualification crew."""
        scores = run_lead(leads)
        self.state["score_crews_results"] = scores
        return scores

    @listen(score_leads)
    def store_leads_score(self, scores):
        """Store lead scores in database."""
        return scores

    @listen(score_leads)
    def filter_leads(self, scores):
        """Filter leads based on score threshold."""
        result, crew = scores
        return result if hasattr(result, '__iter__') else [result]

    @listen(filter_leads)
    def write_email(self, filtered_leads):
        """Generate email content for filtered leads."""
        if not filtered_leads:
            return None
            
        email_inputs = []
        for lead in filtered_leads:
            email_inputs.append({
                "CompanyInfo": str(lead.company_info) if hasattr(lead, 'company_info') else str(lead),
                "PersonalInfo": str(lead.personal_info) if hasattr(lead, 'personal_info') else str(lead),
                "LeadScore": str(lead.lead_score.score) if hasattr(lead, 'lead_score') else "0"
            })
        
        return run_email(email_inputs) if email_inputs else None

    @listen(write_email)
    def send_email(self, emails):
        """Send emails to leads (placeholder)."""
        return emails


def main():

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
    """Main async function to run the sales pipeline."""
    flow = SalesPipeline()
    
    # Plot flow visualization
    flow.plot()
    IFrame(src='./crewai_flow.html', width='150%', height=600)
    
    # Kickoff the flow
    result = flow.kickoff()

    # Extract and display lead scoring results
    if hasattr(flow.state, 'get') and 'score_crews_results' in flow.state:
        scores, crew = flow.state["score_crews_results"]
        
        # Display usage metrics
        if hasattr(scores, 'token_usage'):
            try:
                df_usage_metrics = pd.DataFrame([scores.token_usage.dict()])
                costs = 0.150 * df_usage_metrics['total_tokens'].sum() / 1_000_000
                print(f"Total costs (Lead Qualification): ${costs:.4f}")
            except Exception as e:
                print(f"Could not calculate costs: {e}")

        # Display lead scoring result
        if hasattr(scores, 'pydantic'):
            lead_scoring_result = scores.pydantic
            
            data = {
                'Name': lead_scoring_result.personal_info.name,
                'Job Title': lead_scoring_result.personal_info.job_title,
                'Role Relevance': lead_scoring_result.personal_info.role_relevance,
                'Professional Background': lead_scoring_result.personal_info.professional_background,
                'Company Name': lead_scoring_result.company_info.company_name,
                'Industry': lead_scoring_result.company_info.industry,
                'Company Size': lead_scoring_result.company_info.company_size,
                'Revenue': lead_scoring_result.company_info.revenue,
                'Market Presence': lead_scoring_result.company_info.market_presence,
                'Lead Score': lead_scoring_result.lead_score.score,
                'Scoring Criteria': ', '.join(lead_scoring_result.lead_score.scoring_criteria),
                'Validation Notes': lead_scoring_result.lead_score.validation_notes
            }

            df = pd.DataFrame.from_dict(data, orient='index', columns=['Value'])
            df = df.reset_index()
            df = df.rename(columns={'index': 'Attribute'})

            html_table = df.style.set_properties(**{'text-align': 'left'}).hide(axis='index').to_html()
            display(HTML(html_table))

    # Display email results
    if result:
        try:
            emails_result, _ = result if isinstance(result, tuple) else (result, None)
            if hasattr(emails_result, 'raw'):
                result_text = emails_result.raw
                wrapped_text = textwrap.fill(result_text, width=80)
                print(wrapped_text)
                return result_text
        except Exception as e:
            print(f"Could not process email results: {e}")

    return result


if __name__ == "__main__":
    try:
        main()
    except Exception:
        import traceback
        traceback.print_exc()
        raise