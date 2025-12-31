import arxiv
import json
import os
from typing import List, Any, Dict
from utils import get_anthropic_api_key, load_env
import tempfile, subprocess

# load environment once (uses python-dotenv internally)
load_env()

# optional import for Anthropic; handle gracefully if not installed
try:
    import anthropic
except Exception:
    anthropic = None

PAPER_DIR = "papers"


def get_anthropic_client():
    """
    Lazily construct and return an Anthropic client.
    Raises RuntimeError with a helpful message if the package or API key is missing.
    """
    if anthropic is None:
        raise RuntimeError(
            "The 'anthropic' package is not installed. Install it with "
            "'python -m pip install anthropic' or add it to your requirements."
        )

    api_key = os.getenv("ANTHROPIC_API_KEY") or get_anthropic_api_key()
    if not api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY not found. Please set it as an environment variable "
            "or provide it in a .env file (ANTHROPIC_API_KEY=your-key)."
        )
    os.environ["ANTHROPIC_API_KEY"] = api_key

    # Try common constructor signatures and provide informative errors
    for ctor in ("Client", "Anthropic"):
        ctor_fn = getattr(anthropic, ctor, None)
        if not ctor_fn:
            continue
        # Try keyword, positional, then no-arg
        try:
            return ctor_fn(api_key=api_key)
        except TypeError:
            try:
                return ctor_fn(api_key)
            except Exception:
                try:
                    return ctor_fn()
                except Exception:
                    continue
        except Exception as e:
            raise RuntimeError(f"Failed to construct Anthropic client: {e}")

    raise RuntimeError(
        "Couldn't construct an Anthropic client. Ensure the installed 'anthropic' package "
        "exposes 'Client' or 'Anthropic' and that ANTHROPIC_API_KEY is set if required."
    )


def edit_prompt_via_editor(initial=""):
    fd, path = tempfile.mkstemp(suffix=".txt")
    os.write(fd, initial.encode())
    os.close(fd)
    editor = os.getenv("EDITOR","vi")
    subprocess.call([editor, path])
    with open(path, "r") as f:
        return f.read().strip()
# use: query = edit_prompt_via_editor()


def search_papers(topic: str, max_results: int = 5) -> List[str]:
    """
    Search for papers on arXiv based on a topic and store their information.
    Returns a list of paper IDs.
    """
    arxiv_client = arxiv.Client()

    search = arxiv.Search(
        query=topic,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.Relevance
    )

    papers = arxiv_client.results(search)

    # Create directory for this topic
    path = os.path.join(PAPER_DIR, topic.lower().replace(" ", "_"))
    os.makedirs(path, exist_ok=True)

    file_path = os.path.join(path, "papers_info.json")

    try:
        with open(file_path, "r") as json_file:
            papers_info = json.load(json_file)
    except (FileNotFoundError, json.JSONDecodeError):
        papers_info = {}

    paper_ids: List[str] = []
    for paper in papers:
        short_id = paper.get_short_id()
        paper_ids.append(short_id)
        paper_info = {
            "title": paper.title,
            "authors": [author.name for author in paper.authors],
            "summary": paper.summary,
            "pdf_url": paper.pdf_url,
            "published": str(paper.published.date())
        }
        papers_info[short_id] = paper_info

    with open(file_path, "w") as json_file:
        json.dump(papers_info, json_file, indent=2)

    print(f"Results are saved in: {file_path}")

    return paper_ids


def extract_info(paper_id: str) -> str:
    """
    Search for information about a specific paper across all topic directories.
    Returns JSON string with paper information if found, otherwise an error message.
    """
    if not os.path.isdir(PAPER_DIR):
        return f"No papers directory found ({PAPER_DIR}). Run a search first."

    for item in os.listdir(PAPER_DIR):
        item_path = os.path.join(PAPER_DIR, item)
        if os.path.isdir(item_path):
            file_path = os.path.join(item_path, "papers_info.json")
            if os.path.isfile(file_path):
                try:
                    with open(file_path, "r") as json_file:
                        papers_info = json.load(json_file)
                        if paper_id in papers_info:
                            return json.dumps(papers_info[paper_id], indent=2)
                except (FileNotFoundError, json.JSONDecodeError) as e:
                    print(f"Error reading {file_path}: {str(e)}")
                    continue

    return f"There's no saved information related to paper {paper_id}."


# mapping_tool_function moved here so search_papers/extract_info are defined first
mapping_tool_function = {
    "search_papers": search_papers,
    "extract_info": extract_info
}


def execute_tool(tool_name: str, tool_args: Dict[str, Any]) -> str:
    if tool_name not in mapping_tool_function:
        return f"Unknown tool: {tool_name}"

    result = mapping_tool_function[tool_name](**tool_args)

    if result is None:
        return "The operation completed but didn't return any results."
    if isinstance(result, list):
        return ", ".join(result)
    if isinstance(result, dict):
        return json.dumps(result, indent=2)
    return str(result)


def process_query(query: str) -> None:
    """
    Send the query to the Anthropic client (created lazily).
    Handles tool use responses by executing local tools.
    """
    try:
        client = get_anthropic_client()
    except RuntimeError as e:
        print(f"Anthropic client error: {e}")
        return

    messages = [{"role": "user", "content": query}]

    try:
        response = client.messages.create(
            max_tokens=2024,
            model="claude-sonnet-4-5-20250929",
            tools=[
                {
                    "name": "search_papers",
                    "description": "Search for papers on arXiv based on a topic and store their information.",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "topic": {"type": "string", "description": "The topic to search for"},
                            "max_results": {"type": "integer", "description": "Maximum number of results to retrieve", "default": 5}
                        },
                        "required": ["topic"]
                    }
                },
                {
                    "name": "extract_info",
                    "description": "Search for information about a specific paper across all topic directories.",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "paper_id": {"type": "string", "description": "The ID of the paper to look for"}
                        },
                        "required": ["paper_id"]
                    }
                }
            ],
            messages=messages
        )
    except Exception as e:
        print(f"Failed to call Anthropic API: {e}")
        return

    process_query_flag = True
    while process_query_flag:
        assistant_content = []

        for content in response.content:
            if getattr(content, "type", None) == "text":
                text = getattr(content, "text", str(content))
                print(text)
                assistant_content.append(content)
                if len(response.content) == 1:
                    process_query_flag = False

            elif getattr(content, "type", None) == "tool_use":
                assistant_content.append(content)
                messages.append({"role": "assistant", "content": assistant_content})

                tool_id = getattr(content, "id", None)
                tool_args = getattr(content, "input", {}) or {}
                tool_name = getattr(content, "name", None)
                print(f"Calling tool {tool_name} with args {tool_args}")

                result = execute_tool(tool_name, tool_args)
                messages.append({
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": tool_id,
                            "content": result
                        }
                    ]
                })
                try:
                    response = client.messages.create(
                        max_tokens=2024,
                        model="claude-sonnet-4-5-20250929",
                        tools=[],
                        messages=messages
                    )
                except Exception as e:
                    print(f"Failed to continue conversation: {e}")
                    process_query_flag = False
                    break

                if len(response.content) == 1 and getattr(response.content[0], "type", None) == "text":
                    print(getattr(response.content[0], "text", response.content[0]))
                    process_query_flag = False


def main() -> None:
    print("Type your queries or 'quit' to exit.")
    while True:
        try:
            query = input("System prompt (optional): ").strip()
            messages = []   
            if query.lower() == "quit":
                break
            process_query(query)
            print("\n")
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"\nError: {str(e)}")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        import traceback
        traceback.print_exc()
        raise