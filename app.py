from flask import Flask, render_template, request, redirect
import csv
import io
import openai 
import tiktoken
from datetime import datetime

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Check if a file was submitted
        if 'file' not in request.files:
            return redirect(request.url)

        file = request.files['file']

        # Check if the file has a CSV extension
        if file and file.filename.endswith('.csv'):
            openai.api_key = request.form.get('apiKey')

            # Process the CSV file
            transactions = process_csv(file)
            context = generate_context(transactions, 3600)
            suggestions = generate_savings_suggestions(context)

            return render_template('results.html', suggestions=suggestions)

    return render_template('index.html')

def process_csv(file):
    transactions = []

    # Read the CSV file from the uploaded file object
    csv_data = file.read().decode('utf-8')

    # Use the CSV module to parse the data
    csv_reader = csv.DictReader(io.StringIO(csv_data))

    # Sort the CSV data by the "Date" column in reverse order (most recent to earliest)
    sorted_data = sorted(csv_reader, key=lambda row: datetime.strptime(row['Date'], '%m/%d/%y'), reverse=True)

    for row in sorted_data:
        date = row['Date']
        category = row['Category']
        amount = float(row['Amount'])
        transaction_type = row['Transaction Type']

        transaction = {
            'date': date,
            'category': category,
            'amount': round(amount),
            'type': transaction_type[0]
        }
        transactions.append(transaction)
    return transactions

def generate_context(transactions, max_tokens):
    # Define the context for GPT-3.5
    context = 'Analyze the following list of transactions where d = Date, c = Category, a = Amount, and t = Type. For Type, d = Debit and c = Credit.\n'
    closing_line = 'Generate suggestions on ways that this person can save money. Provide practical advice to help me save money and make better financial decisions. Reference specific transaction descriptions in your response.'

    for transaction in transactions:
        # Calculate the tokens required for this transaction and check if it exceeds the limit
        line = f"- d: {transaction['date']}, c: {transaction['category']}, a: {transaction['amount']}, t: {transaction['type']}\n"
        current_tokens = calculate_transaction_tokens(context, line, closing_line)
        if max_tokens >= current_tokens:
            context += line
        else:
            break

    return context + closing_line

def calculate_transaction_tokens(context, line, closing_line):
    # Combine the context, line, and closing_line into a single prompt string
    prompt = f"{context}{line}{closing_line}"

    # Use tiktoken to count the tokens
    encoding = tiktoken.encoding_for_model("text-davinci-003")
    total_tokens = len(encoding.encode(prompt))

    return total_tokens

def generate_savings_suggestions(prompt):
    # Send a prompt to GPT-3.5 to generate savings suggestions
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        n = 1,
        max_tokens = 400,
        stop=None,
    )

    # Extract and return the generated suggestions
    suggestions = response.choices[0].text.strip().split('\n')
    return suggestions

if __name__ == '__main__':
    app.run(debug=True)
