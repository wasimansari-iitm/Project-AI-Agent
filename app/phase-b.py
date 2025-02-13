import requests
import os
import json
import csv
import unittest
import git
import logging
from dotenv import load_dotenv
from langdetect import detect
import sqlite3
from bs4 import BeautifulSoup
from PIL import Image
import speech_recognition as sr
import markdown
from flask import Flask, request, jsonify
from datetime import datetime

# ---------------------------
# Logging Configuration
# ---------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# ---------------------------
# Environment Setup
# ---------------------------
load_dotenv(dotenv_path=".env")
API_KEY = os.getenv("API_KEY")

if not API_KEY:
    logging.error("API_KEY is not loaded. Check the .env file path.")
    exit()

# API Proxy URL for AI processing
AI_PROXY_URL = "https://aiproxy.sanand.workers.dev/openai/v1/chat/completions"

# ---------------------------
# B0. Send Task to AI with Language Detection
# ---------------------------
def send_task_to_ai(task_data):
    """Send task to AI with language detection."""
    if not task_data or "content" not in task_data:
        logging.error("Invalid task data: 'content' key is missing")
        return {"error": "Invalid task data: 'content' key is missing"}
    
    try:
        detected_lang = detect(task_data["content"])
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {API_KEY}'
        }
        payload = {
            "model": "gpt-4",  # Updated model name
            "messages": [
                {
                    "role": "system",
                    "content": f"You are a helpful assistant who processes tasks. Detected language: {detected_lang}"
                },
                {"role": "user", "content": task_data["content"]}
            ]
        }
        logging.info("🔄 AI Agent is processing the task using the LLM.")
        response = requests.post(AI_PROXY_URL, json=payload, headers=headers)
        response.raise_for_status()
        ai_response = response.json()
        
        if "choices" in ai_response and len(ai_response["choices"]) > 0:
            result = ai_response["choices"][0]["message"]["content"]
            logging.info(f"✅ AI Response: {result}")
            logging.info(f"💰 Monthly Cost: {ai_response.get('monthlyCost', 'N/A')}")
            logging.info(f"📊 Monthly Requests: {ai_response.get('monthlyRequests', 'N/A')}")
            return result
        
        logging.error(f"❌ AI Response: {ai_response}")
        return ai_response
    
    except requests.exceptions.RequestException as e:
        logging.error(f"❌ Request failed: {e}")
        return {"error": f"Request failed: {str(e)}"}
    except json.JSONDecodeError as e:
        logging.error(f"❌ JSON decode error: {e}")
        return {"error": f"JSON decode error: {str(e)}"}
    except Exception as e:
        logging.error(f"❌ Unexpected error: {e}")
        return {"error": f"Unexpected error: {str(e)}"}

# ---------------------------
# B3. Fetch Data from an API and Save It
# ---------------------------
def fetch_data_from_api(api_url, method="GET", params=None, headers=None, body=None, filename='output.json', output_format='json'):
    try:
        logging.info(f"🌐 Fetching data from API: {api_url} with method: {method}")
        if method.upper() == "GET":
            response = requests.get(api_url, params=params, headers=headers)
        elif method.upper() == "POST":
            response = requests.post(api_url, json=body, headers=headers)
        elif method.upper() == "PUT":
            response = requests.put(api_url, json=body, headers=headers)
        else:
            logging.error("❌ Error: Unsupported HTTP method.")
            return {"status": "error", "message": "Unsupported HTTP method"}
        
        response.raise_for_status()
        logging.info("✅ API response received successfully.")
        
        data_dir = '/data'
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
            logging.info(f"📂 Created directory: {data_dir}")
        
        file_path = os.path.join(data_dir, filename)
        if output_format == 'json':
            try:
                data = response.json()
                with open(file_path, 'w') as file:
                    json.dump(data, file, indent=4)
            except json.JSONDecodeError:
                logging.error("❌ Error: The API response is not valid JSON.")
                return {"status": "error", "message": "Invalid JSON response"}
        elif output_format == 'csv':
            try:
                data = response.json()
                if isinstance(data, list) and all(isinstance(item, dict) for item in data):
                    with open(file_path, 'w', newline='') as file:
                        writer = csv.DictWriter(file, fieldnames=data[0].keys())
                        writer.writeheader()
                        writer.writerows(data)
                else:
                    logging.error("❌ Error: Data is not in a list of dictionaries format for CSV export.")
                    return {"status": "error", "message": "Invalid data format for CSV"}
            except json.JSONDecodeError:
                logging.error("❌ Error: The API response is not valid JSON.")
                return {"status": "error", "message": "Invalid JSON response"}
        else:
            with open(file_path, 'w') as file:
                file.write(response.text)
        
        logging.info(f"💾 Data saved successfully to {file_path}")
        return {"status": "success", "file_path": file_path}
    
    except requests.exceptions.RequestException as e:
        logging.error(f"❌ Error fetching data from API: {e}")
        return {"status": "error", "message": str(e)}

# ---------------------------
# B4. Clone and Commit to Git Repository
# ---------------------------
def clone_and_commit_repo(repo_url, commit_message, file_changes):
    if not file_changes:
        logging.warning("⚠️ No file changes provided.")
        return {"status": "error", "message": "No file changes provided"}
    
    try:
        repo_name = repo_url.split('/')[-1].replace('.git', '')
        clone_dir = os.path.join('/data', repo_name)
        logging.info(f"🔗 Cloning repository: {repo_url}")
        if not os.path.exists(clone_dir):
            git.Repo.clone_from(repo_url, clone_dir)
            logging.info(f"✅ Repository cloned to {clone_dir}")
        else:
            logging.info(f"ℹ️ Repository already exists locally at {clone_dir}")
        
        repo = git.Repo(clone_dir)
        
        # Apply file changes
        for file_path, content in file_changes.items():
            full_path = os.path.join(clone_dir, file_path)
            with open(full_path, 'w') as f:
                f.write(content)
            logging.info(f"✏️ Updated file: {file_path}")
        
        # Stage changes
        repo.git.add(A=True)
        
        # Check if there are any changes to commit
        if repo.is_dirty(index=True, working_tree=True, untracked_files=True):
            repo.index.commit(commit_message)
            logging.info(f"✅ Commit successful with message: '{commit_message}'")
            return {"status": "success", "message": f"Changes committed to {repo_url}"}
        else:
            logging.warning("⚠️ No changes detected to commit.")
            return {"status": "error", "message": "No changes to commit"}
    
    except Exception as e:
        logging.error(f"❌ Error during Git operations: {e}")
        return {"status": "error", "message": str(e)}

# ---------------------------
# B5. Run a SQL Query on a SQLite or DuckDB Database
# ---------------------------
def run_sql_query(database_path, query):
    """Run a SQL query on a SQLite or DuckDB database."""
    try:
        logging.info(f"🔍 Running SQL query on database: {database_path}")
        connection = sqlite3.connect(database_path)
        cursor = connection.cursor()
        cursor.execute(query)
        result = cursor.fetchall()
        connection.close()
        logging.info("✅ SQL query executed successfully.")
        return {"status": "success", "data": result}
    except Exception as e:
        logging.error(f"❌ Error executing SQL query: {e}")
        return {"status": "error", "message": str(e)}

# ---------------------------
# B6. Extract Data from a Website (Scraping)
# ---------------------------
def scrape_website(url, selector):
    """Extract data from a website using a CSS selector."""
    try:
        logging.info(f"🌐 Scraping website: {url}")
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        elements = soup.select(selector)
        data = [element.get_text(strip=True) for element in elements]
        logging.info("✅ Data extracted successfully.")
        return {"status": "success", "data": data}
    except Exception as e:
        logging.error(f"❌ Error scraping website: {e}")
        return {"status": "error", "message": str(e)}

# ---------------------------
# B7. Compress or Resize an Image
# ---------------------------
def compress_or_resize_image(image_path, output_path, quality=85, size=None):
    """Compress or resize an image."""
    try:
        logging.info(f"🖼️ Processing image: {image_path}")
        with Image.open(image_path) as img:
            if size:
                img = img.resize(size)
            img.save(output_path, quality=quality)
        logging.info(f"✅ Image saved to: {output_path}")
        return {"status": "success", "output_path": output_path}
    except Exception as e:
        logging.error(f"❌ Error processing image: {e}")
        return {"status": "error", "message": str(e)}

# ---------------------------
# B8. Transcribe Audio from an MP3 File
# ---------------------------
def transcribe_audio(mp3_file_path):
    """Transcribe audio from an MP3 file."""
    try:
        logging.info(f"🎤 Transcribing audio file: {mp3_file_path}")
        recognizer = sr.Recognizer()
        with sr.AudioFile(mp3_file_path) as source:
            audio = recognizer.record(source)
        text = recognizer.recognize_google(audio)
        logging.info("✅ Transcription completed.")
        return {"status": "success", "text": text}
    except Exception as e:
        logging.error(f"❌ Error transcribing audio: {e}")
        return {"status": "error", "message": str(e)}

# ---------------------------
# B9. Convert Markdown to HTML
# ---------------------------
def convert_markdown_to_html(markdown_text):
    """Convert Markdown text to HTML."""
    try:
        logging.info("📝 Converting Markdown to HTML.")
        html = markdown.markdown(markdown_text, extensions=['extra'])
        logging.info("✅ Conversion completed.")
        return {"status": "success", "html": html}
    except Exception as e:
        logging.error(f"❌ Error converting Markdown: {e}")
        return {"status": "error", "message": str(e)}

# ---------------------------
# B10. Write an API Endpoint to Filter a CSV File and Return JSON Data
# ---------------------------
app = Flask(__name__)

@app.route('/filter_csv', methods=['POST'])
def filter_csv_api():
    try:
        data = request.json
        file_path = data.get("file_path")
        filters = data.get("filters", {})

        logging.info(f"📂 Filtering CSV file: {file_path} with filters: {filters}")

        with open(file_path, mode='r') as file:
            reader = csv.DictReader(file)
            filtered_data = [row for row in reader if all(row.get(key) == value for key, value in filters.items())]

        logging.info(f"✅ Filtered data retrieved successfully.")
        return jsonify({"status": "success", "data": filtered_data})

    except FileNotFoundError:
        logging.error(f"❌ Error: File '{file_path}' not found.")
        return jsonify({"status": "error", "message": f"File '{file_path}' not found"}), 404
    except Exception as e:
        logging.error(f"❌ Error filtering CSV: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# ---------------------------
# Dynamic AI Agent Handler Integration
# ---------------------------
def ai_agent_handler(task, api_key):
    if not task or "operation" not in task:
        return {"status": "error", "message": "Invalid task: 'operation' key is missing"}

    if api_key != API_KEY:
        logging.error("❌ Authentication failed: Invalid API key.")
        return {"status": "error", "message": "Invalid API key"}

    logging.info(f"🤖 AI Agent received task: {task}")
    operation = task.get("operation")

    if operation == "clone_and_commit":
        return clone_and_commit_repo(
            repo_url=task.get("repo_url"),
            commit_message=task.get("commit_message", "Automated commit"),
            file_changes=task.get("file_changes", {})
        )
    elif operation == "run_sql_query":
        return run_sql_query(
            database_path=task.get("database_path"),
            query=task.get("query")
        )
    elif operation == "scrape_website":
        return scrape_website(
            url=task.get("url"),
            selector=task.get("selector")
        )
    elif operation == "compress_or_resize_image":
        return compress_or_resize_image(
            image_path=task.get("image_path"),
            output_path=task.get("output_path"),
            quality=task.get("quality", 85),
            size=task.get("size")
        )
    elif operation == "transcribe_audio":
        return transcribe_audio(
            mp3_file_path=task.get("mp3_file_path")
        )
    elif operation == "convert_markdown_to_html":
        return convert_markdown_to_html(
            markdown_text=task.get("markdown_text")
        )
    elif operation == "filter_csv":
        return filter_csv_api(task)
    else:
        logging.error("⚠️ Unsupported operation requested.")
        return {"status": "error", "message": "Unsupported operation"}

# ✅ Dynamic & Challenging Test Cases for All Operations
class TestAIAgent(unittest.TestCase):
    def setUp(self):
        logging.info("🚀 Starting a new test case")

    def tearDown(self):
        logging.info("✅ Finished the test case")

    def test_dynamic_sql_query(self):
        db_path = "test_dynamic.db"
        
        # Ensure the database is clean before running the test
        if os.path.exists(db_path):
            os.remove(db_path)
        
        # Create a new database and insert test data
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY, name TEXT, price REAL);")
        cursor.execute("INSERT INTO products (name, price) VALUES ('Laptop', 1500), ('Phone', 800);")
        conn.commit()
        conn.close()

        task = {
            "operation": "run_sql_query",
            "database_path": db_path,
            "query": "SELECT * FROM products WHERE price > 1000;"
        }
        response = ai_agent_handler(task, API_KEY)
        logging.info(f"📥 Test Response: {response}")
        self.assertEqual(response["status"], "success")
        self.assertEqual(len(response.get("data", [])), 1)  # Expect only 1 row

    def test_complex_markdown_conversion(self):
        markdown_text = """
        # Complex Document
        - **Item 1**: Description with `inline code`
        - Item 2: [Link](https://example.com)
        """.strip()
        task = {
            "operation": "convert_markdown_to_html",
            "markdown_text": markdown_text.strip()
        }
        response = ai_agent_handler(task, API_KEY)
        logging.info(f"📥 Test Response: {response}")
        self.assertEqual(response["status"], "success")
        self.assertIn("<strong>Item 1</strong>", response.get("html", ""))

    def test_filter_csv(self):
        # Create a sample CSV file
        csv_file = "test_data.csv"
        with open(csv_file, mode='w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=["name", "age", "city"])
            writer.writeheader()
            writer.writerow({"name": "Alice", "age": "30", "city": "New York"})
            writer.writerow({"name": "Bob", "age": "25", "city": "Los Angeles"})
            writer.writerow({"name": "Charlie", "age": "35", "city": "Chicago"})

        with app.test_client() as client:
            response = client.post('/filter_csv', json={
                "file_path": csv_file,
                "filters": {"city": "Chicago"}
            })

        response_data = response.get_json()
        logging.info(f"📥 Test Response: {response_data}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response_data["status"], "success")
        self.assertEqual(len(response_data.get("data", [])), 1)
        self.assertEqual(response_data["data"][0]["name"], "Charlie")

if __name__ == "__main__":
    unittest.main(verbosity=2, buffer=False)