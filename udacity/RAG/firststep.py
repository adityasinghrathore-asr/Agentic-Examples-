import os
from openai import OpenAI
from pprint import pprint

os.environ['OPENAI_API_KEY'] = "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"

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