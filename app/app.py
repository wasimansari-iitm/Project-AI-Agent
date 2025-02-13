import os
import sys
import pandas as pd
import requests
import json
import re
import subprocess
from datetime import datetime
from dotenv import load_dotenv
from PIL import Image
import pytesseract
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
import sqlite3
from langdetect import detect
from deep_translator import GoogleTranslator as Translator
import csv
import git
import logging
from bs4 import BeautifulSoup
import speech_recognition as sr
import markdown
from flask import Flask, request, jsonify, Response
from bs4 import BeautifulSoup
from pydub import AudioSegment
import markdown

# Initialize Flask app
app = Flask(__name__)

# ---------------------------
# Logging Configuration
# ---------------------------

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# ---------------------------
# Environment Setup
# ---------------------------
load_dotenv(dotenv_path=".env")
AIPROXY_TOKEN = os.getenv("AIPROXY_TOKEN")

if not AIPROXY_TOKEN:
    logging.error("AIPROXY_TOKEN is not loaded. Check the .env file path.")
    exit()

# API Proxy URL for AI processing
AI_PROXY_URL = "https://aiproxy.sanand.workers.dev/openai/v1/chat/completions"

# ---------------------------
# Utility Functions
# ---------------------------

# Constants
DATA_DIRECTORY = os.getenv("DATA_DIR", "/data")
FEEDBACK_LOG_FILE = "feedback_log.json"

# 🚫 Global Rules Enforcement

def restricted_access(file_path):
    """Ensure file operations are restricted to the /data directory."""
    # Resolve the absolute path of the file
    absolute_file_path = os.path.abspath(file_path)
    
    # Resolve the absolute path of the /data directory
    DATA_DIRECTORY = os.getenv("DATA_DIR", "/data")
    
    # Normalize both paths to ensure consistent formatting
    absolute_file_path = os.path.normpath(absolute_file_path)
    DATA_DIRECTORY = os.path.normpath(DATA_DIRECTORY)
    
    # Debug logs to verify paths
    print(f"🔒 Checking access for file: {absolute_file_path}")
    print(f"🔒 Data directory: {DATA_DIRECTORY}")
    
    # Ensure the file is within the /data directory
    if not os.path.commonpath([absolute_file_path, DATA_DIRECTORY]) == DATA_DIRECTORY:
        print(f"❌ Access denied: {file_path} is outside /data directory.")
        return False
    
    print(f"✅ Access granted: {file_path} is within /data directory.")
    return True

# 📂 Enhanced File Operations
def read_file_content(file_path, file_type="text"):
    """Read content from various file types."""
    if not restricted_access(file_path):
        return None
    
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return None
    
    try:
        if file_type == "json":
            with open(file_path, 'r', encoding='utf-8') as file:
                return json.load(file)
        elif file_type == "text":
            with open(file_path, 'r') as file:
                return file.read()
        elif file_type == "image":
            # Open the image file using Pillow
            image = Image.open(file_path)
            image.verify()  # Verify that the file is not corrupted
            image = Image.open(file_path)  # Reopen the file for processing
            return image
        else:  # text, log, markdown, etc.
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
    except Exception as e:
        print(f"Error reading file: {e}")
        return None

def write_file_content(file_path, content, file_type="text"):
    """Write content to various file types."""
    if not restricted_access(file_path):
        return False
    
    try:
        if file_type == "json":
            with open(file_path, 'w', encoding='utf-8') as file:
                json.dump(content, file, indent=4)
        else:
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(str(content))
        return True
    except Exception as e:
        print(f"Error writing file: {e}")
        return False
    
# ---------------------------
# Task Handlers (Phase-A)
# ---------------------------
def install_uvicorn():
    """Install uvicorn if it is not already installed."""
    try:
        import uvicorn
    except ImportError:
        print("Uvicorn not found, installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "uvicorn"])

def run_script(email):
    """Download and run datagen.py with email argument."""
    url = "https://raw.githubusercontent.com/sanand0/tools-in-data-science-public/tds-2025-01/project-1/datagen.py"
    script_name = "datagen.py"

    try:
        # Download the script
        subprocess.run(["curl", "-O", url], check=True)

        # Run the script with email argument
        subprocess.run([sys.executable, script_name, email], check=True)
        return "Script executed successfully with email{email}."
    except subprocess.CalledProcessError as e:
        return f"Error running script: {e}"
    except Exception as e:
        return f"Unexpected error: {e}"

def format_markdown_file():
    """Format the contents of /data/format.md using prettier@3.4.2."""
    file_path = os.path.join(DATA_DIRECTORY, "format.md")
    if not restricted_access(file_path):
        return "Access denied."

    try:
        # Check if prettier is installed
        try:
            subprocess.run(["prettier", "--version"], check=True, capture_output=True)
        except FileNotFoundError:
            return "Error: Prettier is not installed. Install it using 'npm install -g prettier@3.4.2'."

        # Format the file using prettier
        subprocess.run(["prettier", "--write", file_path], check=True)
        return f"File {file_path} formatted using prettier@3.4.2."
    except subprocess.CalledProcessError as e:
        return f"Error formatting file: {e}"
    except Exception as e:
        return f"Error: {e}"

def count_specific_day(file_path="../data/dates.txt", target_day=None):
    """A3: Count occurrences of specific days."""
    if not restricted_access(file_path):
        return "Access denied."

    try:
        content = read_file_content(file_path)
        if content is None:
            return "Error reading dates file."

        dates = content.splitlines()
        date_formats = ["%Y-%m-%d", "%d/%m/%Y", "%d.%m.%Y"]
        day_counts = {}

        for date_str in dates:
            date_str = date_str.strip()
            for fmt in date_formats:
                try:
                    date_obj = datetime.strptime(date_str, fmt)
                    day_name = date_obj.strftime('%A')  # Get the day name (e.g., "Wednesday")
                    day_counts[day_name] = day_counts.get(day_name, 0) + 1
                    break
                except ValueError:
                    continue

        if target_day:
            # Ensure the target_day is capitalized (e.g., "wednesday" -> "Wednesday")
            target_day = target_day.capitalize()
            result = {target_day: day_counts.get(target_day, 0)}
        else:
            result = day_counts  # Return counts for all days if no specific day is requested

        # Save the result to a file
        output_file = "../data/dates-count.txt"
        write_file_content(output_file, str(result))
        return f"Total {target_day}s found: {day_counts.get(target_day, 0)}" if target_day else f"Day counts: {day_counts}"
    except Exception as e:
        return f"Error: {e}"

def sort_contacts():
    """A4: Sort contacts by last name and first name."""
    file_path = "../data/contacts.json"
    if not restricted_access(file_path):
        return "Access denied."

    try:
        contacts = read_file_content(file_path, "json")
        if contacts is None:
            return "Error reading contacts file."

        sorted_contacts = sorted(contacts, key=lambda x: (x.get('last_name', ''), x.get('first_name', '')))
        write_file_content("../data/contacts-sorted.json", sorted_contacts, "json")
        return f"Contacts sorted and saved to /data/contacts-sorted.json."
    except Exception as e:
        return f"Error: {e}"

def process_recent_logs():
    """A5: Write the first line of the 10 most recent .log files."""
    logs_directory = "../data/logs"
    if not restricted_access(logs_directory):
        return "Access denied."

    try:
        log_files = [f for f in os.listdir(logs_directory) if f.endswith('.log')]
        log_files.sort(key=lambda x: os.path.getmtime(os.path.join(logs_directory, x)), reverse=True)

        recent_logs = []
        for log_file in log_files[:10]:
            content = read_file_content(os.path.join(logs_directory, log_file))
            if content:
                recent_logs.append(content.split('\n')[0])

        write_file_content("../data/logs-recent.txt", '\n'.join(recent_logs))
        return f"First lines of the 10 most recent logs saved to /data/logs-recent.txt."
    except Exception as e:
        return f"Error: {e}"

def index_the_markdown_files():
    """A6: Index markdown files and create index."""
    docs_directory = "../data/docs"
    if not restricted_access(docs_directory):
        return "Access denied."

    try:
        index = {}
        for root, _, files in os.walk(docs_directory):
            for file in files:
                if file.endswith('.md'):
                    content = read_file_content(os.path.join(root, file))
                    if content:
                        first_heading = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
                        if first_heading:
                            index[file] = first_heading.group(1).strip()

        write_file_content("../data/docs/index.json", index, "json")
        return f"Markdown index created and saved to /data/docs/index.json."
    except Exception as e:
        return f"Error: {e}"

def extract_email():
    """A7: Extract email from email content."""
    file_path = "../data/email.txt"
    if not restricted_access(file_path):
        return "Access denied."

    try:
        email_content = read_file_content(file_path)
        if email_content is None:
            return "Error reading email file."

        sender_email = re.findall(r'From:.*<(.*)>', email_content)
        if sender_email:
            write_file_content("../data/email-sender.txt", sender_email[0])
            return f"Sender email extracted and saved to /data/email-sender.txt."
        return "No sender email found."
    except Exception as e:
        return f"Error: {e}"

# Set the path to the Tesseract executable
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def extract_credit_card_number():
    """A8: Extract credit card number from image."""
    file_path = "../data/credit_card.png"
    if not restricted_access(file_path):
        return "Access denied."

    try:
        # Read the image file
        image = read_file_content(file_path, "image")
        if isinstance(image, str):  # If an error message is returned
            return image

        # Extract text from the image using pytesseract
        card_number = pytesseract.image_to_string(image, config='--psm 6').strip()
        card_number = re.sub(r'\s+', '', card_number)  # Remove whitespace

        # Save the extracted credit card number to a text file
        output_file_path = "../data/credit-card.txt"
        if not restricted_access(output_file_path):
            return "Access denied for output file."

        with open(output_file_path, 'w') as file:
            file.write(card_number)

        return f"Credit card number extracted and saved to {output_file_path}."
    except Exception as e:
        return f"Error: {str(e)}"

def find_similar_comments():
    """A9: Find similar comments using cosine similarity."""
    file_path = "../data/comments.txt"
    if not restricted_access(file_path):
        return "Access denied."

    try:
        content = read_file_content(file_path)
        if content is None:
            return "Error reading comments file."

        comments = content.splitlines()
        vectorizer = TfidfVectorizer().fit_transform(comments)
        similarity_matrix = cosine_similarity(vectorizer)

        max_sim = 0
        pair = (0, 0)
        for i in range(len(comments)):
            for j in range(i + 1, len(comments)):
                if similarity_matrix[i, j] > max_sim:
                    max_sim = similarity_matrix[i, j]
                    pair = (i, j)

        similar_comments = f"{comments[pair[0]]}\n{comments[pair[1]]}"
        write_file_content("../data/comments-similar.txt", similar_comments)
        return f"Most similar comments saved to /data/comments-similar.txt."
    except Exception as e:
        return f"Error: {e}"

def calculate_gold_ticket_sales():
    """A10: Calculate gold ticket sales from database."""
    db_path = "../data/ticket-sales.db"
    if not restricted_access(db_path):
        return "Access denied."

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT SUM(units * price) FROM tickets WHERE type='Gold'")
        total_sales = cursor.fetchone()[0]
        conn.close()

        write_file_content("../data/ticket-sales-gold.txt", str(total_sales))
        return f"Total Gold Ticket Sales: {total_sales}"
    except Exception as e:
        return f"Error: {e}"

# 🔍 Enhanced Information Extraction
def extract_information(text, pattern_type):
    """Extract specific information based on pattern type."""
    if text is None:
        return "Error: No text provided for extraction."

    patterns = {
        "email": r'[\w\.-]+@[\w\.-]+\.\w+',
        "date": r'\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4}|\d{2}\.\d{2}\.\d{4}',
        "phone": r'\+?\d{1,4}?[-.\s]?\(?\d{1,3}?\)?[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}',
        "url": r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[^\s]*',
        "credit_card": r'\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}'
    }
    
    if pattern_type in patterns:
        matches = re.finditer(patterns[pattern_type], text)
        return [match.group() for match in matches]
    return []

def extract_information_from_files(pattern_type):
    """Traverse the /data directory to extract information based on pattern type."""
    DATA_DIRECTORY = "../data"
    if not restricted_access(DATA_DIRECTORY):
        return "Access denied."

    try:
        extracted_data = []
        for root, _, files in os.walk(DATA_DIRECTORY):
            for file in files:
                if file.endswith('.txt') or file.endswith('.md') or file.endswith('.log'):
                    file_path = os.path.join(root, file)
                    content = read_file_content(file_path)
                    if content:
                        matches = extract_information(content, pattern_type)
                        if matches:
                            extracted_data.extend(matches)

        if not extracted_data:
            return f"No {pattern_type} found in any files."

        return extracted_data
    except Exception as e:
        return f"Error: {e}"

# ---------------------------
# Task Handlers (Phase-B)
# ---------------------------

# B3: Fetch data from an API and save it
def fetch_data_from_api(api_url, output_file):
    """Fetch data from an API and save it to a file."""
    if not restricted_access(output_file):
        return "Access denied."

    try:
        response = requests.get(api_url)
        response.raise_for_status()
        data = response.json()

        with open(output_file, 'w') as file:
            json.dump(data, file)
        
        return f"Data fetched from {api_url} and saved to {output_file}."
    except Exception as e:
        return f"Error fetching data: {str(e)}"

# B4: Clone a git repo and make a commit
def clone_and_commit_repo(repo_url, commit_message):
    """Clone a git repository and make a commit."""
    repo_name = repo_url.split("/")[-1].replace(".git", "")
    repo_path = os.path.join(DATA_DIRECTORY, repo_name)

    if not restricted_access(repo_path):
        return "Access denied."

    try:
        # Clone the repository
        subprocess.run(["git", "clone", repo_url, repo_path], check=True)
        
        # Make a commit
        subprocess.run(["git", "-C", repo_path, "add", "."], check=True)
        subprocess.run(["git", "-C", repo_path, "commit", "-m", commit_message], check=True)
        
        return f"Repository cloned and commit made with message: {commit_message}."
    except Exception as e:
        return f"Error cloning repository or making commit: {str(e)}"

# B5: Run a SQL query on a SQLite or DuckDB database
def run_sql_query(db_path, query):
    """Run a SQL query on a SQLite database."""
    if not restricted_access(db_path):
        return "Access denied."

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(query)
        result = cursor.fetchall()
        conn.close()
        
        return f"Query executed successfully. Result: {result}"
    except Exception as e:
        return f"Error executing SQL query: {str(e)}"

# B6: Extract data from (i.e. scrape) a website
def scrape_website(url, output_file):
    """Scrape data from a website and save it to a file."""
    if not restricted_access(output_file):
        return "Access denied."

    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Example: Extract all text
        text = soup.get_text()
        
        with open(output_file, 'w') as file:
            file.write(text)
        
        return f"Data scraped from {url} and saved to {output_file}."
    except Exception as e:
        return f"Error scraping website: {str(e)}"

# B7: Compress or resize an image
def compress_or_resize_image(image_path, output_path, quality=85, size=None):
    """Compress and/or resize an image."""
    if not restricted_access(image_path) or not restricted_access(output_path):
        return "Access denied."

    try:
        with Image.open(image_path) as img:
            if size:
                img = img.resize(size)
            img.save(output_path, quality=quality)
        return f"Image processed and saved to {output_path}."
    except Exception as e:
        return f"Error processing image: {str(e)}"

# B8: Transcribe audio from an MP3 file
def transcribe_audio(audio_path, output_file):
    """Transcribe audio from an MP3 file and save the transcription."""
    if not restricted_access(audio_path) or not restricted_access(output_file):
        return "Access denied."

    try:
        audio = AudioSegment.from_mp3(audio_path)
        # Dummy transcription logic (replace with actual transcription logic)
        transcription = "This is a dummy transcription."
        
        with open(output_file, 'w') as file:
            file.write(transcription)
        
        return f"Audio transcribed and saved to {output_file}."
    except Exception as e:
        return f"Error transcribing audio: {str(e)}"

# B9: Convert Markdown to HTML
def convert_markdown_to_html(markdown_file, output_file):
    """Convert a Markdown file to HTML."""
    if not restricted_access(markdown_file) or not restricted_access(output_file):
        return "Access denied."

    try:
        with open(markdown_file, 'r') as file:
            md_content = file.read()
        
        html_content = markdown.markdown(md_content)
        
        with open(output_file, 'w') as file:
            file.write(html_content)
        
        return f"Markdown converted to HTML and saved to {output_file}."
    except Exception as e:
        return f"Error converting Markdown to HTML: {str(e)}"

# B10: Write an API endpoint that filters a CSV file and returns JSON data
def filter_csv_api(csv_file, filters, output_file):
    """Filter a CSV file and save the results to a JSON file."""
    if not restricted_access(csv_file) or not restricted_access(output_file):
        return "Access denied."

    try:
        with open(csv_file, 'r') as file:
            reader = csv.DictReader(file)
            filtered_data = [row for row in reader if all(row[key] == value for key, value in filters.items())]
        
        with open(output_file, 'w') as file:
            json.dump(filtered_data, file, indent=2)
        
        return f"CSV data filtered and saved to {output_file}."
    except Exception as e:
        return f"Error filtering CSV data: {str(e)}"

@app.route('/filter_csv', methods=['GET'])
def filter_csv_handler():
    """Filter a CSV file and return JSON data."""
    file_path = request.args.get("file_path")
    filters = request.args.get("filters")

    if not file_path or not filters:
        return jsonify({"error": "File path and filters are required."}), 400

    try:
        filters = json.loads(filters)  # Convert filters from JSON string to dictionary
    except json.JSONDecodeError:
        return jsonify({"error": "Invalid filters format. Expected JSON."}), 400

    full_path = os.path.join(DATA_DIRECTORY, os.path.basename(file_path))
    if not os.path.isfile(full_path):
        return jsonify({"error": "File not found."}), 404

    try:
        with open(full_path, 'r') as file:
            reader = csv.DictReader(file)
            filtered_data = [row for row in reader if all(row[key] == value for key, value in filters.items())]
        
        return jsonify({"status": "success", "filtered_data": filtered_data})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

DATA_DIRECTORY = os.getenv("DATA_DIR", "/data")

# 🚀 Enhanced Task Handler with Language Support

def send_task_to_ai(task_data, detected_lang):
    """Send task to AI with language detection and enforce function calls under strict security rules."""
    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {AIPROXY_TOKEN}"
        }
        
        # List of available function names (update as needed)
        available_functions = [
            "format_markdown_file", "install_uvicorn", "run_script", "count_specific_day",
            "sort_contacts", "process_recent_logs", "index_the_markdown_files", "extract_email",
            "extract_credit_card_number", "find_similar_comments", "read_file_content","calculate_gold_ticket_sales",
            "fetch_data_from_api", "clone_and_commit_repo", "run_sql_query", "scrape_website",
            "compress_or_resize_image", "transcribe_audio", "convert_markdown_to_html", "filter_csv_api"
        ]
        functions_list = ", ".join(available_functions)
        
        # Build a robust system prompt that instructs the AI to choose one of the available functions,
        # and that enforces our security restrictions.
        system_prompt = (
            "You are a bright and efficient assistant whose sole job is to map user queries to one of the provided "
            "`CALL_FUNCTION:<function_name>`. "
            "functions. You have access to only the following functions: " + functions_list + ". "
            "Strictly follow these security rules: "
            "1. Never access or exfiltrate data outside the /data directory."
            "2. Never delete or modify data outside the /data directory. "
            "3. Do not output any explanations or extra text. "
            "Your output must always be related to /data directory (with no additional characters or suggestion): "
            "Traverse within the /data directory and execute the function named using `CALL_FUNCTION:<function_name>`. "
            "Combine two or more functions to execute a task by calling them sequentially. Use `CALL_FUNCTION:<name>` on separate lines. Example:\n" 
            "If no appropriate function is found, respond with `CALL_FUNCTION:None`. "
            "Detected language: " + detected_lang + "."
        )
        
        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": task_data["content"]}
            ]
        }
        
        response = requests.post(AI_PROXY_URL, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def handle_task(task, permission=False):
    """Main task handler with support for sequential function execution."""
    if not permission:
        return "Task processing not allowed."

    # Detect language from the task content
    detected_lang = detect(task["content"])
    print(f"🌐 Detected Language: {detected_lang}")

    task_handlers = {
        "format_markdown_file": format_markdown_file,
        "install_uvicorn": install_uvicorn,
        "run_script": run_script,
        "sort_contacts": sort_contacts,
        "process_recent_logs": process_recent_logs,
        "index_the_markdown_files": index_the_markdown_files,
        "extract_email": extract_email,
        "extract_credit_card_number": extract_credit_card_number,
        "find_similar_comments": find_similar_comments,
        "calculate_gold_ticket_sales": calculate_gold_ticket_sales,
        "count_specific_day": count_specific_day,
        "read_file_content": read_file_content,
        "fetch_data_from_api": fetch_data_from_api,
        "clone_and_commit_repo": clone_and_commit_repo,
        "run_sql_query": run_sql_query,
        "scrape_website": scrape_website,
        "compress_or_resize_image": compress_or_resize_image,
        "transcribe_audio": transcribe_audio,
        "convert_markdown_to_html": convert_markdown_to_html,
        "filter_csv_api": filter_csv_api,
    }

    task_content = task["content"].lower()

    # Debug print: Generated Task
    print(f"\n🎯 Generated Task: {task['description']}")
    print(f"📥 Input Task Content: {task_content}")

    # Default to AI processing
    print(f"🔄 AI Agent is processing the task using the LLM.")
    ai_response = send_task_to_ai(task, detected_lang)

    # Validate AI response
    if "choices" in ai_response and len(ai_response["choices"]) > 0:
        ai_message = ai_response["choices"][0]["message"]["content"]
        print(f"🔄 AI Response: {ai_message}")  # Debug log

        # Split multiple function calls
        function_calls = [line.strip() for line in ai_message.split('\n') if line.startswith("CALL_FUNCTION:")]
        
        if not function_calls:
            return "Error: No valid function calls detected."

        results = []
        for func_call in function_calls:
            function_name = func_call.split(":")[1].strip()
            print(f"🔄 Function Name: {function_name}")

            if function_name in task_handlers:
                print(f"🔄 Executing {function_name}...")

                if function_name == "run_script":
                    # Extract email from the task description
                    email_match = re.search(r'with\s+([\w\.-]+@[\w\.-]+)', task_content)
                    email = email_match.group(1) if email_match else "user@example.com"
                    result = task_handlers[function_name](email=email)
                    results.append(result)
                    continue
                
                # Handle count_specific_day task dynamically
                if function_name == "count_specific_day":
                    # Extract the day of the week from the task description
                    day_match = re.search(r'Count the number of (\w+)s', task_content, re.IGNORECASE)
                    if day_match:
                        target_day = day_match.group(1).capitalize()  # Ensure proper capitalization (e.g., "wednesday" -> "Wednesday")
                        result = task_handlers[function_name](target_day=target_day)
                    else:
                        result = "Error: No day specified in the task."
                    results.append(result)
                    continue
                
                # Extract parameters for other functions
                try:
                    if function_name == "filter_csv_api":
                        csv_match = re.search(r'file\s+(\S+)', task_content)
                        filters = dict(re.findall(r'(\w+)=(\w+)', task_content))
                        output_match = re.search(r'to\s+(\S+)', task_content)

                        if not csv_match or not output_match:
                            results.append("Error: Could not extract CSV file or output file.")
                            continue

                        csv_file = csv_match.group(1)
                        output_file = output_match.group(1)

                        result = task_handlers[function_name](csv_file, filters, output_file)

                    elif function_name == "run_sql_query":
                        db_match = re.search(r'on\s+(\S+)', task_content)
                        query_match = re.search(r'query\s+"([^"]+)"', task_content)

                        if not db_match or not query_match:
                            results.append("Error: Could not extract database path or query.")
                            continue

                        db_path = db_match.group(1)
                        query = query_match.group(1)

                        result = task_handlers[function_name](db_path, query)

                    elif function_name == "clone_and_commit_repo":
                        repo_match = re.search(r'clone\s+git\s+repo\s+(\S+)', task_content)
                        commit_match = re.search(r'message\s+"?([^"]+)"?', task_content)

                        if not repo_match or not commit_match:
                            results.append("Error: Could not extract repository URL or commit message.")
                            continue

                        repo_url = repo_match.group(1)
                        commit_message = commit_match.group(1).strip('"')

                        result = task_handlers[function_name](repo_url, commit_message)

                    elif function_name == "fetch_data_from_api":
                        api_match = re.search(r'from\s+(\S+)', task_content)
                        output_match = re.search(r'to\s+(\S+)', task_content)

                        if not api_match or not output_match:
                            results.append("Error: Could not extract API URL or output file.")
                            continue

                        api_url = api_match.group(1)
                        output_file = output_match.group(1)

                        result = task_handlers[function_name](api_url, output_file)

                    elif function_name == "scrape_website":
                        url_match = re.search(r'from\s+(\S+)', task_content)
                        output_match = re.search(r'to\s+(\S+)', task_content)

                        if not url_match or not output_match:
                            results.append("Error: Could not extract URL or output file.")
                            continue

                        url = url_match.group(1)
                        output_file = output_match.group(1)

                        result = task_handlers[function_name](url, output_file)

                    elif function_name == "compress_or_resize_image":
                        image_match = re.search(r'image\s+(\S+)', task_content)
                        output_match = re.search(r'to\s+(\S+)', task_content)
                        quality_match = re.search(r'quality\s+(\d+)', task_content)
                        size_match = re.search(r'resize\s+to\s+(\d+)x(\d+)', task_content)

                        if not image_match or not output_match:
                            results.append("Error: Could not extract image path or output path.")
                            continue

                        image_path = image_match.group(1)
                        output_path = output_match.group(1)
                        quality = int(quality_match.group(1)) if quality_match else 85
                        size = tuple(map(int, size_match.groups())) if size_match else None

                        result = task_handlers[function_name](image_path, output_path, quality, size)

                    elif function_name == "transcribe_audio":
                        audio_match = re.search(r'from\s+(\S+)', task_content)
                        output_match = re.search(r'to\s+(\S+)', task_content)

                        if not audio_match or not output_match:
                            results.append("Error: Could not extract audio path or output file.")
                            continue

                        audio_path = audio_match.group(1)
                        output_file = output_match.group(1)

                        result = task_handlers[function_name](audio_path, output_file)

                    elif function_name == "convert_markdown_to_html":
                        markdown_match = re.search(r'file\s+(\S+)', task_content)
                        output_match = re.search(r'to\s+(\S+)', task_content)

                        if not markdown_match or not output_match:
                            results.append("Error: Could not extract Markdown file or output file.")
                            continue

                        markdown_file = markdown_match.group(1)
                        output_file = output_match.group(1)

                        result = task_handlers[function_name](markdown_file, output_file)

                    else:
                        result = task_handlers[function_name]()

                    results.append(result)

                except Exception as e:
                    results.append(f"Error in {function_name}: {str(e)}")
            else:
                results.append(f"Error: Function '{function_name}' not found.")

        return jsonify({"status": "success", "results": results})

    print(f"❌ AI Response: {ai_response}")
    return jsonify({"error": "Unable to process the task."})

# /run endpoint
@app.route('/run', methods=['GET', 'POST'])
def run_handler():
    task_description = None

    if request.is_json:
        data = request.get_json()
        task_description = data.get("task")

    if not task_description:
        task_description = request.args.get("task")

    if not task_description:
        return jsonify({"error": "Task not provided."}), 400

    logging.info(f"Task received: {task_description}")

    task = {
        "content": task_description,
        "description": task_description
    }

    try:
        result = handle_task(task, permission=True)

        # 🔹 Ensure result is JSON serializable
        if isinstance(result, dict):
            return jsonify({
                "status": "success",
                "task": task_description,
                "result": result
            })
        elif isinstance(result, str):
            return jsonify({
                "status": "success",
                "task": task_description,
                "result": {"message": result}
            })
        elif isinstance(result, Response):  # Ensure response is returned directly
            return result
        else:
            return jsonify({
                "status": "error",
                "task": task_description,
                "error": "Unexpected response type"
            }), 500

    except Exception as e:
        logging.error(f"Error executing task: {e}")
        return jsonify({"error": f"Error executing task: {str(e)}"}), 500
    
# /read endpoint
@app.route('/read', methods=['GET', 'POST'])
def read_handler():
    # Try to get the path from the JSON body (for POST requests)
    data = request.json or {}
    file_path = data.get("path")

    # If the path is not in the JSON body, try to get it from the query parameters
    if not file_path:
        file_path = request.args.get("path")

    # If the path is still not provided, return an error
    if not file_path:
        return jsonify({"error": "File path not provided."}), 400

    full_path = os.path.join(DATA_DIRECTORY, os.path.basename(file_path))
    if not os.path.isfile(full_path):
        return jsonify({"error": "File not found."}), 404

    try:
        with open(full_path, 'r') as file:
            content = file.read()
        return jsonify({"content": content})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000) 