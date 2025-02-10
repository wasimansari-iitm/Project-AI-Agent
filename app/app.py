import os
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

# 🔒 Load API Key from .env file
load_dotenv(dotenv_path=".env")
API_KEY = os.getenv("API_KEY")

if not API_KEY:
    print("API_KEY is not loaded. Check the .env file path.")
    exit()

# API Proxy URL
AI_PROXY_URL = "https://aiproxy.sanand.workers.dev/openai/v1/chat/completions"

# 🚫 Global Rules Enforcement
def restricted_access(file_path):
    """Ensure file operations are restricted to the /data directory."""
    data_directory = os.path.abspath("../data")
    if not os.path.commonpath([os.path.abspath(file_path), data_directory]) == data_directory:
        print(f"Access denied: {file_path} is outside /data directory.")
        return False
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
        elif file_type == "image":
            return Image.open(file_path)
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

# Task Functions
def format_markdown_file():
    """A2: Format the contents of /data/format.md using prettier@3.4.2."""
    file_path = "../data/format.md"
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

def index_markdown_files():
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

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
def extract_credit_card_number():
    """A8: Extract credit card number from image."""
    file_path = "../data/credit_card.png"
    if not restricted_access(file_path):
        return "Access denied."

    try:
        image = read_file_content(file_path, "image")
        if image is None:
            return "Error reading image file."

        card_number = pytesseract.image_to_string(image, config='--psm 6').strip()
        card_number = re.sub(r'\s+', '', card_number)

        write_file_content("../data/credit-card.txt", card_number)
        return f"Credit card number extracted and saved to /data/credit-card.txt."
    except Exception as e:
        return f"Error: {e}"

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
                    day_name = date_obj.strftime('%A')
                    day_counts[day_name] = day_counts.get(day_name, 0) + 1
                    break
                except ValueError:
                    continue

        result = {target_day: day_counts.get(target_day, 0)} if target_day else day_counts
        write_file_content("../data/dates-wednesdays.txt", str(day_counts.get(target_day, 0)))
        return f"Total {target_day}s found: {day_counts.get(target_day, 0)}"
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
    data_directory = "../data"
    if not restricted_access(data_directory):
        return "Access denied."

    try:
        extracted_data = []
        for root, _, files in os.walk(data_directory):
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

# 🚀 Enhanced Task Handler with Language Support
def send_task_to_ai(task_data):
    """Send task to AI with language detection."""
    try:
        detected_lang = detect(task_data["content"])
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {API_KEY}'
        }

        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {
                    "role": "system",
                    "content": f"You are a helpful assistant who processes tasks. Detected language: {detected_lang}"
                },
                {"role": "user", "content": task_data["content"]}
            ]
        }

        response = requests.post(AI_PROXY_URL, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def handle_task(task, permission=False):
    """Main task handler with support for original and new functions."""
    if not permission:
        return "Task processing not allowed."

    task_handlers = {
        "format markdown": format_markdown_file,
        "sort contacts": sort_contacts,
        "recent logs": process_recent_logs,
        "index markdown": index_markdown_files,
        "extract email": extract_email,
        "extract credit card": extract_credit_card_number,
        "similar comments": find_similar_comments,
        "gold ticket sales": calculate_gold_ticket_sales,
        "count day": count_specific_day,
        "count all days": count_specific_day,
        "read file": read_file_content
    }

    task_content = task["content"].lower()
    
    # Debug print: Generated Task
    print(f"\n🎯 Generated Task: {task['description']}")
    print(f"📥 Input Task Content: {task_content}")

    # Handle file operations
    if "read file" in task_content:
        file_path = task.get("file_path", "../data/sample.txt")
        file_type = task.get("file_type", "text")
        print(f"🔄 AI Agent is handling the read file task.")
        result = read_file_content(file_path, file_type)
        print(f"✅ Function Response: {result}")
        return result
    
    # Handle information extraction
    for pattern_type in ["email", "date", "phone", "url", "credit_card"]:
        if f"extract {pattern_type}" in task_content:
            file_path = task.get("file_path", None)
            if file_path:
                print(f"🔄 AI Agent is handling the extract {pattern_type} task from {file_path}.")
                text = task.get("text", "") or read_file_content(file_path)
                if text is None:
                    print(f"❌ Error: File '{file_path}' not found or could not be read.")
                    return f"Error: File '{file_path}' not found or could not be read."
                result = extract_information(text, pattern_type)
                print(f"✅ Function Response: {result}")
                return result
            else:
                print(f"🔄 AI Agent is traversing the /data directory to extract {pattern_type}.")
                result = extract_information_from_files(pattern_type)
                print(f"✅ Function Response: {result}")
                return result
    
    # Handle specific day counting
    if "count day" in task_content or "count all days" in task_content:
        print(f"🔄 AI Agent is handling the count specific day task.")
        result = count_specific_day(
            task.get("file_path", "../data/dates.txt"),
            task.get("target_day", None)
        )
        print(f"✅ Function Response: {result}")
        return result
    
    # Handle original functions
    for key, handler in task_handlers.items():
        if key in task_content:
            print(f"🔄 AI Agent is handling the {key} task.")
            result = handler()
            print(f"✅ Function Response: {result}")
            return result

    # Default to AI processing
    print(f"🔄 AI Agent is processing the task using the LLM.")
    ai_response = send_task_to_ai(task)
    if "choices" in ai_response and len(ai_response["choices"]) > 0:
        result = ai_response["choices"][0]["message"]["content"]  # Return only the AI's response content
        print(f"✅ AI Response: {result}")
        # Print monthly cost and requests
        print(f"💰 Monthly Cost: {ai_response.get('monthlyCost', 'N/A')}")
        print(f"📊 Monthly Requests: {ai_response.get('monthlyRequests', 'N/A')}")
        return result
    print(f"❌ AI Response: {ai_response}")
    return ai_response  # Fallback to return the full response if the structure is unexpected

if __name__ == "__main__":
    # Example tasks combining original and new functionality
    tasks = [
        {"description": "Format Markdown", "content": "Format markdown file."},
        {"description": "Sort Contacts", "content": "Sort contacts."},
        {"description": "Recent Logs", "content": "Process recent logs."},
        {"description": "Index Markdown", "content": "Index markdown files."},
        {"description": "Extract Email", "content": "Extract email."},
        {"description": "Extract Credit Card", "content": "Extract credit card number."},
        {"description": "Similar Comments", "content": "Find similar comments."},
        {"description": "Gold Ticket Sales", "content": "Calculate gold ticket sales."},
        {"description": "Count Specific Day", "content": "Count day occurrences for Wednesday.", "target_day": "Wednesday"}
    ]
    
    for task in tasks:
        print(f"\n--- Processing Task: {task['description']} ---")
        result = handle_task(task, permission=True)
        print(f"Result: {result}")
        print("----------------------------")