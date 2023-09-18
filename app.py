from flask import Flask, render_template, request, redirect, session, url_for
import csv
import io
import openai 
import os
import tiktoken
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.urandom(12)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Check if a file was submitted
        if 'file' not in request.files:
            return redirect(request.url)

        file = request.files['file']

        # Check if the file has a CSV extension
        if file and file.filename.endswith('.csv'):
            api_key = os.getenv('API_KEY')
            if api_key:
                openai.api_key = api_key
            else:
                openai.api_key = request.form.get('apiKey')

            # Process the CSV file
            transactions = process_csv(file)
            context = generate_context(transactions, 3600)
            conversation.append({"role": "user", "content": context})
            suggestions = generate_savings_suggestions(conversation)

            session['commentary'] = [{'type': 'answer', 'text':suggestions}]

            return redirect(url_for('results'))

    return render_template('index.html')

@app.route('/results', methods=['GET', 'POST'])
def results():
    question = request.form.get('question')
    commentary = session.get('commentary')
    if request.method == 'POST' and question:
        conversation.append({"role": "user", "content": question})
        suggestions = generate_savings_suggestions(conversation)
    
        commentary = session.get('commentary')
        commentary.append({'type': 'question', 'text':question})
        commentary.append({'type': 'answer', 'text':suggestions})
        session['commentary'] = commentary
    return render_template('results.html', suggestions=commentary)

# Initialize conversation context
conversation = [
    {"role": "system", "content": ' \
        Analyze the following list of transactions set up in this format:\n\
        Date | Category | Amount | Type\n\
        For Type, d = Debit and c = Credit.\n\
        Generate suggestions on ways that this person can save money. Provide \
        practical advice to help me save money and make better financial \
        decisions. Reference specific transaction categories in your response.'}
]

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
    context = ''
    for transaction in transactions:
        # Calculate the tokens required for this transaction and check if it exceeds the limit
        line = f"- {transaction['date']} | {transaction['category']} | {transaction['amount']} | {transaction['type']}\n"
        current_tokens = calculate_transaction_tokens(context, line)
        if max_tokens >= current_tokens:
            context += line
        else:
            break
    return context

def calculate_transaction_tokens(context, line):
    # Combine the context, and line into a single prompt string
    prompt = f"{context}{line}"

    # Use tiktoken to count the tokens
    encoding = tiktoken.encoding_for_model("text-davinci-003")
    total_tokens = len(encoding.encode(prompt))

    return total_tokens

def generate_savings_suggestions(conversation):
    # Call the API with the updated conversation context
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=conversation,
    )

    # Extract the AI's response to the question
    suggestions = response.choices[0].message["content"]
    return suggestions

if __name__ == '__main__':
    app.run(debug=True)
