import os
from pathlib import Path
from statistics import mean

from dotenv import load_dotenv
from anthropic import Anthropic, AuthenticationError
import json
import re
import ast


env_path = Path(__file__).with_name(".env")
load_dotenv(dotenv_path=env_path)

api_key = (os.getenv("ANTHROPIC_API_KEY") or "").strip().strip('"').strip("'")
if not api_key:
    print("Set ANTHROPIC_API_KEY in your environment or .env file.")
    exit(1)

# Anthropic keys start with sk-ant-; catch common copy/paste mistakes early.
if not api_key.startswith("sk-ant-"):
    print("Invalid ANTHROPIC_API_KEY format. Expected key to start with 'sk-ant-'.")
    exit(1)

client = Anthropic(api_key=api_key)
model = "claude-sonnet-4-0"

messages = []


def add_user_message(messages: list, content: str):
    user_message =  {"role": "user", "content": content}
    messages.append(user_message)

def add_assistant_message(messages: list, content: str):
    assistant_message = {"role": "assistant", "content": content}
    messages.append(assistant_message)  

def chat(messages, system=None, temperature=1.0, stop_sequences=None):

    params = {
        "model": model,
        "max_tokens": 1000,
        "messages": messages,
       # "temperature": temperature
    }


    if system:
        params["system"] = system

    if stop_sequences:
        params["stop_sequences"] = stop_sequences
    
    response = client.messages.create(
        **params
    )
    return response.content[0].text 

def generate_dataset():
        prompt = """
    Generate a evaluation dataset for a prompt evaluation. The dataset will be used to evaluate prompts
    that generate Python, JSON, or Regex specifically for AWS-related tasks. Generate an array of JSON objects,
    each representing task that requires Python, JSON, or a Regex to complete.

    Example output:
    ```json
    [
        {
            "task": "Description of task",
            "format": "python" or "json" or "regex"
            "solution_criteria": "Criteria that a solution must meet to be considered correct",
        },
        ...additional
    ]
    ```

    * Focus on tasks that can be solved by writing a single Python function, a single JSON object, or a regular expression.
    * Focus on tasks that do not require writing much code

    Please generate 3 objects.
    """
        messages = []
        add_user_message(messages, prompt)
        add_assistant_message(messages, "```json")
        response = chat(messages, stop_sequences=["```"])   
        return json.loads(response.strip())

def run_prompt(test_case):
    """ Merge the prompt and test case input, then return the result. """
    prompt = f"""
    Please solve the following task:
    {test_case["task"]}
    * Respond only with python, json, and regex.
    * Do not add any comments or commentary or explanation.

    """
    messages = []
    add_user_message(messages, prompt)
    add_assistant_message(messages, "```code")
    response = chat(messages, stop_sequences=["```"])
    return response 

def validate_json(text):
    try:
        json.loads(text.strip())
        return 10   
    except json.JSONDecodeError:
        print("Failed to parse JSON:", text)
        return 0

def validate_python(text):
    try:
        ast.parse(text.strip())
        return 10
    except SyntaxError as e:
        print("Failed to parse Python code:", e)
        return 0

def grade_syntax(test_case, output):   
    format = test_case["format"]
    if format == "python":
        return validate_python(output)
    elif format == "json":
        return validate_json(output)
    elif format == "regex":
        return validate_regex(output)
    else:
        print("Unknown task type. Cannot grade syntax.")
        return 0

def validate_regex(text):
    try:
        re.compile(text)
        return 10
    except re.error as e:
        print("Failed to parse Regex:", e)
        return 0

# Function to grade a test case + output using a model
def grade_by_model(test_case, output):
    eval_prompt = f"""
    You are an expert AWS code reviewer. Your task is to evaluate the following AI-generated solution.

    Original Task:
    <task>
    {test_case["task"]}
    </task>

    Solution to Evaluate:
    <solution>
    {output}
    </solution>

    Criteria you shoule use to evaluate the solution:
    <criteria>
    {test_case["solution_criteria"]}
    </criteria>
    
    Output Format
    Provide your evaluation as a structured JSON object with the following fields, in this specific order:
    - "strengths": An array of 1-3 key strengths
    - "weaknesses": An array of 1-3 key areas for improvement
    - "reasoning": A concise explanation of your overall assessment
    - "score": A number between 1-10

    Respond with JSON. Keep your response concise and direct.
    Example response shape:
    {{
        "strengths": string[],
        "weaknesses": string[],
        "reasoning": string,
        "score": number
    }}
        """
    messages = []
    add_user_message(messages, eval_prompt)
    add_assistant_message(messages, "```json")
    response = chat(messages, stop_sequences=["```"])

    return json.loads(response.strip())


def run_test_case(test_case):
    """ Call run_prompt, then grades the result. """
    output = run_prompt(test_case)

    # TODO: Grading

    model_grade = grade_by_model(test_case, output) 
    model_score = model_grade["score"]
    reasoning = model_grade["reasoning"]

    code_grade = grade_syntax(test_case, output)
    score = (model_score + code_grade) / 2

    #score = 10

    return {
        "output": output,
        "test_case": test_case,
        "score": score,
        "reasoning": reasoning
    }

def run_eval(dataset):
    """ Loads the dataset and calls run_test_case for each test case. """
    results = []
    for test_case in dataset:
        result = run_test_case(test_case)
        results.append(result)
    
    average_score = mean([result["score"] for result in results])
    print(f"Average Score : {average_score}")   
     
    return results

def main() -> None:
   
    #dataset = generate_dataset()
    #with open("dataset.json", "w") as f:
  #      json.dump(dataset, f, indent=2)

    #print(json.dumps(dataset, indent=2))

    #results = run_eval(dataset)
    #==================================
    with open("dataset.json", "r") as f:
       dataset = json.load(f)
    results = run_eval(dataset)
  
    print(json.dumps(results, indent=2))


    #add_user_message(messages, "Generte a very short event bridge rule as JSON")
    #response = chat(messages, temperature=0.0)
    #response = chat(messages, temperature=1.0)
    #print("Assistant:", response)
    #add_assistant_message(messages, "```json")
   # response = chat(messages, stop_sequences=["```"])

    #print("Assistant:", json.loads(response.strip()))

     # Wait for the stream to finish and get the final message object if needed.essage()  # Wait for the stream to finish and get the final message object if needed.

if __name__ == "__main__":
    main()



