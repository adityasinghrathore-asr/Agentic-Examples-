import os
from openai import OpenAI
from pprint import pprint

os.environ['OPENAI_API_KEY'] = ""

#print(os.environ)

client = OpenAI()

completion = client.chat.completions.create(
  model="gpt-4.1",
  messages=[
    {"role": "user", "content": "Give me a short description of what an embedding is"}
  ],
  logprobs=True,
  top_logprobs=5
)

pprint(completion.choices[0].message)

#pprint(completion.choices[0].logprobs)