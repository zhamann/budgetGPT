from flask import Flask, render_template, request, redirect, session, url_for
import csv
import io
import openai
import os
import tiktoken
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.urandom(12)


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # Check if a file was submitted
        if "file" not in request.files:
            return redirect(request.url)

        file = request.files["file"]

        # Check if the file has a CSV extension
        if file and file.filename.endswith(".csv"):
            api_key = os.getenv("API_KEY")
            if api_key:
                openai.api_key = api_key
            else:
                openai.api_key = request.form.get("apiKey")

            # Process the CSV file
            transactions = process_csv(file)
            context, last_date = generate_context(transactions, 3600)
            conversation.append({"role": "user", "content": context})
            suggestions = generate_savings_suggestions(conversation)

            session["commentary"] = [{"type": "answer", "text": suggestions}]
            session["last_date"] = last_date

            return redirect(url_for("results"))

    return render_template("index.html")


@app.route("/results", methods=["GET", "POST"])
def results():
    question = request.form.get("question")
    commentary = session.get("commentary")
    last_date = session.get("last_date")
    if last_date:
        input_date = datetime.strptime(last_date, "%m/%d/%y")
        last_date = input_date.strftime("%B %d, %Y")
    if request.method == "POST" and question:
        message = conversation
        message.append({"role": "user", "content": question})
        suggestions = generate_savings_suggestions(message)

        commentary = session.get("commentary")
        commentary.append({"type": "question", "text": question})
        commentary.append({"type": "answer", "text": suggestions})
        session["commentary"] = commentary
    return render_template("results.html", suggestions=commentary, last_date=last_date)


# Initialize conversation context
conversation = [
    {
        "role": "system",
        "content": " \
        Analyze the following list of transactions set up in this format: \
        Date / Category / Amount / Type\n\
        For Type, d = Debit and c = Credit. \
        Generate suggestions on ways that this person can save money. Provide \
        practical advice to help me save money and make better financial \
        decisions. Reference specific transaction categories in your response. \
        After each suggestion in your response, say [BREAK].\n",
    }
]


def process_csv(file):
    transactions = []

    # Read the CSV file from the uploaded file object
    csv_data = file.read().decode("utf-8")

    # Use the CSV module to parse the data
    csv_reader = csv.DictReader(io.StringIO(csv_data))

    # Sort the CSV data by the "Date" column in reverse order (most recent to earliest)
    sorted_data = sorted(
        csv_reader,
        key=lambda row: datetime.strptime(row["Date"], "%m/%d/%y"),
        reverse=True,
    )

    for row in sorted_data:
        date = row["Date"]
        category = row["Category"]
        amount = float(row["Amount"])
        transaction_type = row["Transaction Type"]

        transaction = {
            "date": date,
            "category": category,
            "amount": round(amount),
            "type": transaction_type[0],
        }
        transactions.append(transaction)
    return transactions


def generate_context(transactions, max_tokens):
    # Define the context for GPT-3.5
    context = ""
    last_date = transactions[-1].get('date')
    for transaction in transactions:
        # Calculate the tokens required for this transaction and check if it exceeds the limit
        line = f"- {transaction['date']} / {transaction['category']} / {transaction['amount']} / {transaction['type']}\n"
        current_tokens = calculate_transaction_tokens(context, line)
        if max_tokens >= current_tokens:
            context += line
        else:
            last_date = transaction['date']
            break
    return context, last_date


def calculate_transaction_tokens(context, line):
    # Combine the context and line into a single prompt string
    prompt = f"{context}{line}"

    # Use tiktoken to count the tokens
    encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
    total_tokens = len(encoding.encode(prompt))

    return total_tokens

def num_tokens_from_messages(messages, model="gpt-3.5-turbo"):
  """Returns the number of tokens used by a list of messages."""
  try:
      encoding = tiktoken.encoding_for_model(model)
  except KeyError:
      encoding = tiktoken.get_encoding("cl100k_base")
  if model == "gpt-3.5-turbo":  # note: future models may deviate from this
      num_tokens = 0
      for message in messages:
          num_tokens += 4  # every message follows <im_start>{role/name}\n{content}<im_end>\n
          for key, value in message.items():
              num_tokens += len(encoding.encode(value))
              if key == "name":  # if there's a name, the role is omitted
                  num_tokens += -1  # role is always required and always 1 token
      num_tokens += 2  # every reply is primed with <im_start>assistant
      return num_tokens
  else:
      raise NotImplementedError(f"""num_tokens_from_messages() is not presently implemented for model {model}.
  See https://github.com/openai/openai-python/blob/main/chatml.md for information on how messages are converted to tokens.""")


def generate_savings_suggestions(conversation):
    # Use tiktoken to calculate the remaining tokens
    total_tokens = num_tokens_from_messages(conversation)
    print('\nTotal tokens:', total_tokens)
    remaining_tokens = 4097 - total_tokens
    print('\nRemaining tokens:', remaining_tokens)

    # Call the API with the updated conversation context
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=conversation,
        max_tokens=remaining_tokens
    )

    # Extract the AI's response to the question
    suggestions = response.choices[0].message["content"]
    suggestions = suggestions.rsplit('[BREAK]', 1)[0].replace('[BREAK]', '')
    return suggestions


if __name__ == "__main__":
    app.run(debug=True)
