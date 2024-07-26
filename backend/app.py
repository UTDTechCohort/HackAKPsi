from flask import Flask, request, jsonify
from flask_cors import CORS
import csv
import openai
import json
import gspread

# Initialize Flask app
app = Flask(__name__)

# Enable CORS for all routes from the specific origin where your React app is hosted
CORS(app, resources={r"/process-csv": {"origins": "http://localhost:3000"}})

# Load OpenAI API key from JSON file
with open('./apikey.json', 'r') as file:
    json_data = file.read()
parsed_data = json.loads(json_data)
openai.api_key = parsed_data['api_key']

# Initialize gspread with the service account credentials
sa = gspread.service_account(filename='service_account.json')

# Path to the CSV file
filename = 'roster.csv'

def send_chat_messages(content):
    """
    Sends a chat message to the OpenAI API and returns the response content.
    """

    try:
        # Create chat completion request
        completion = openai.ChatCompletion.create(
            model="gpt-4",  # Update model ID as appropriate
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": content}
            ]
        )
        # Return the response content
        return completion.choices[0].message['content']
    except Exception as e:
        return f"An error occurred: {str(e)}"

def send_chat_to_openai(sample_query):
    """
    Prepares the query and sends it to OpenAI. Handles simple greetings differently.
    """

    # Handle simple greetings separately
    if ("Hi" in sample_query or "Hello" in sample_query) and (len(sample_query) <= 8):
        return "Hello there! I am a chatbot for the AKPsi Mu Rho Chapter. How can I assist you today?"
    
    # Format the sheet data and create a new query
    new_query = format_sheet_data(sample_query)
    return send_chat_messages(new_query)

def format_sheet_data(sample_query):
    """
    Formats the data from the Google Sheets and prepares it for inclusion in the chat query.
    """
    previous_context = "Here is the context of our previous discussion:\n\n"
    
    try:
        # Access the Google Sheets document
        sh = sa.open("Mu Rho Roster Spring 2024")
        rosterSheet = sh.get_worksheet(1)
        list_of_lists = rosterSheet.get_all_values()

        # Save data to CSV for testing purposes
        with open(filename, 'w', newline='\n') as f:
            writer = csv.writer(f)
            writer.writerows(list_of_lists)
        
        # Format the CSV data
        previous_context += "### Roster Data:\n\n"
        for row in list_of_lists:
            previous_context += f"- {' | '.join(row)}\n"

        # Combine formatted data with the sample query
        new_query = f"{previous_context}\n\n{sample_query}"
        return new_query
    
    except Exception as e:
        return str(e)

@app.route('/process-csv', methods=['POST'])
def process_csv():
    """
    Endpoint to process CSV data and respond with chat completion.
    """
    
    data = request.json
    sample_query = data.get('query', '')
    
    if not sample_query:
        return jsonify({"error": "Empty query"}), 400
    
    final_result = send_chat_to_openai(sample_query)
    return jsonify({"response": final_result})

if __name__ == '__main__':
    # Run the Flask app
    app.run(debug=True, host='0.0.0.0', port=5000)
