from unstructured.partition.auto import partition
from openai import OpenAI
import os
from dotenv import load_dotenv
import json

load_dotenv() 

# Initialize OpenAI client (make sure OPENAI_API_KEY is set in your env)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

file_path = "/Users/revmag/Downloads/code-projs/document_agent/rent agreement sriven.pdf"  # your file here

# Step 1: Partition document
elements = partition(filename=file_path)

# Step 2: Gather plain text only
text_content = "\n".join([el.text for el in elements if el.text])

# Step 2: Extract structured info with GPT
extract_prompt = f"""
Extract structured information from the following document text.
Return ONLY valid JSON with key-value pairs.

Document text:
{text_content}
"""

resp = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": "You are a document parsing assistant."},
        {"role": "user", "content": extract_prompt}
    ],
    temperature=0
)

gpt_output = resp.choices[0].message.content

try:
    parsed_json = json.loads(gpt_output)
except json.JSONDecodeError:
    print("⚠️ GPT output invalid, saving raw.")
    parsed_json = {"raw_output": gpt_output}

# Step 3: Ask user required fields
user_input = input("Enter required fields (comma separated): ")

# Step 4: Second GPT call to reduce JSON
reduce_prompt = f"""
We have extracted structured data from a document:

{json.dumps(parsed_json, indent=2)}

The user only wants the following fields: {user_input}.

⚠️ IMPORTANT RULES:
- Only include the exact fields listed by the user.
- Do not include any subfields or extra details (e.g. if "tenant" is requested, just give tenant names, not their full address).
- The output must be ONLY valid JSON. No text before or after.
"""

resp2 = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": "You are a JSON reducer."},
        {"role": "user", "content": reduce_prompt}
    ],
    temperature=0
)

reduced_output = resp2.choices[0].message.content

try:
    reduced_json = json.loads(reduced_output)
except json.JSONDecodeError:
    print("⚠️ GPT reduced output invalid, saving raw.")
    reduced_json = {"raw_output": reduced_output}

# Step 5: Save final JSON
with open("final_output.json", "w", encoding="utf-8") as f:
    json.dump(reduced_json, f, indent=2, ensure_ascii=False)

print("✅ Saved filtered data to final_output.json")
print(reduced_json)