from flask import Flask, request, render_template, send_file, session
from unstructured.partition.auto import partition
from openai import OpenAI
import os, json, csv, io
from dotenv import load_dotenv
import json

load_dotenv() 

app = Flask(__name__)
app.secret_key = "supersecretkey"  # needed for session storage

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def extract_with_gpt(text_content):
    """Call GPT to extract structured JSON from raw document text"""
    prompt = f"""
    Extract structured information from the following document text.
    Return ONLY valid JSON with key-value pairs.

    Document text:
    {text_content}
    """
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a document parsing assistant."},
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )
    return resp.choices[0].message.content


def reduce_with_gpt(full_json, user_fields):
    """Call GPT to reduce extracted JSON to user-requested fields"""

    if not user_fields.strip():  # case: blank input
        prompt = f"""
        We have extracted structured data from a document:

        {json.dumps(full_json, indent=2)}

        The user did not specify any fields.
        Please select the 3-4 most important fields (such as parties involved, dates, addresses, amounts, locality).
        
        ⚠️ IMPORTANT RULES:
        - Focus only on high-level fields (not every detail).
        - If a field has subfields (like name + address), keep ONLY the most identifying one (usually 'name' or 'number').
        - Output must be ONLY valid JSON. No text before or after.
        """
    else:  # case: user entered specific fields
        prompt = f"""
        We have extracted structured data from a document:

        {json.dumps(full_json, indent=2)}

        The user only wants the following fields: {user_fields}.

        ⚠️ IMPORTANT RULES:
        - Only include the exact fields listed by the user.
        - Do not include subfields or extra details (e.g. if 'tenant' is requested, just give tenant names, not their full address).
        - Output must be ONLY valid JSON. No text before or after.
        """

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a JSON reducer."},
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )
    return resp.choices[0].message.content


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # Step 1: get user fields
        user_fields = request.form["fields"]

        # Step 2: save uploaded file
        file = request.files["file"]
        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(file_path)

        # Step 3: partition doc
        elements = partition(filename=file_path)
        text_content = "\n".join([el.text for el in elements if el.text])

        # Step 4: GPT extraction
        gpt_raw = extract_with_gpt(text_content)

        try:
            parsed = json.loads(gpt_raw)
        except json.JSONDecodeError:
            parsed = {"raw_output": gpt_raw}

        # Step 5: GPT reduction
        gpt_reduced = reduce_with_gpt(parsed, user_fields)

        try:
            reduced = json.loads(gpt_reduced)
        except json.JSONDecodeError:
            reduced = {"raw_output": gpt_reduced}

        # Save reduced data in session for download
        session["final_data"] = reduced

        # Convert to table format (key-value rows)
        table_data = [(k, v) for k, v in reduced.items()]

        return render_template("result.html", data=table_data)

    return render_template("index.html")


@app.route("/download/<fmt>")
def download(fmt):
    final_data = session.get("final_data", {})

    if fmt == "json":
        buf = io.BytesIO()
        buf.write(json.dumps(final_data, indent=2).encode("utf-8"))
        buf.seek(0)
        return send_file(buf, as_attachment=True,
                         download_name="output.json",
                         mimetype="application/json")

    elif fmt == "csv":
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["Field", "Value"])
        for k, v in final_data.items():
            writer.writerow([k, v])
        mem = io.BytesIO(buf.getvalue().encode("utf-8"))
        return send_file(mem, as_attachment=True,
                         download_name="output.csv",
                         mimetype="text/csv")

    return "Invalid format", 400


if __name__ == "__main__":
    app.run(debug=True)
