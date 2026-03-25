import os
from pathlib import Path
from pyexpat import model

from dotenv import load_dotenv
from anthropic import Anthropic, AuthenticationError


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

def chat(messages, system=None, temperature=1.0):

    params = {
        "model": model,
        "max_tokens": 1000,
        "messages": messages,
        "temperature": temperature
    }


    if system:
        params["system"] = system
    
    response = client.messages.create(
        **params
    )
    return response.content[0].text 

def main() -> None:
    system = """
    You are a python programmer who writes very concise and efficient code.
    """
    add_user_message(messages, "write a 1 sentence description of a fake database")
    #response = chat(messages, temperature=0.0)
    #response = chat(messages, temperature=1.0)
    #print("Assistant:", response)

    with client.messages.stream(
        model=model,
        max_tokens=1000,
        messages=messages,
    ) as stream:
        for response in stream.text_stream:
            #print(response, end="", flush=True) 
            pass
    stream.get_final_message()
     # Wait for the stream to finish and get the final message object if needed.essage()  # Wait for the stream to finish and get the final message object if needed.

if __name__ == "__main__":
    main()



