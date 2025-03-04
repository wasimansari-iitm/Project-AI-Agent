---

### **🚀 AI Automation Agent - README**
#### **An Intelligent Automation API for Data Processing & Business Tasks**

## **📌 Overview**
The **AI Automation Agent** is a powerful API designed to **process files, automate tasks, and enhance business operations** using AI capabilities. It runs inside a container and interacts via simple API requests.

- 🌐 **Fully Automated AI-Powered Task Execution**
- 📂 **Secure File Processing within `/data/` Directory**
- 🔗 **API-Driven Architecture**
- 🔒 **Prevents Data Exfiltration & Deletion**
- 🏎️ **Fast & Scalable**

---

## **🛠️ Features & Capabilities**
### **🔹 Phase A: Data Processing Tasks**
✔️ **Preprocess & Format Data**  
- Format Markdown files with **Prettier** (`/data/format.md`)  
- Sort **contacts.json** by name (`/data/contacts-sorted.json`)  
- Extract structured data from files (`/data/email.txt`, `/data/credit-card.png`)  

✔️ **Analyze & Extract Insights**  
- Count specific days from a list of dates (`/data/dates-wednesdays.txt`)  
- Find the most similar comments in a text file (`/data/comments.txt`)  
- Extract and index Markdown headings (`/data/docs/index.json`)  
- Process logs and extract the first line from the most recent log files (`/data/logs-recent.txt`)  

✔️ **Database & Financial Data Processing**  
- Query a SQLite database (`/data/ticket-sales.db`)  
- Calculate **total sales** for Gold tickets (`/data/ticket-sales-gold.txt`)  

✔️ **AI-Based File Processing**  
- Transcribe audio files (`/data/audio.mp3`)  
- Convert Markdown to HTML (`/data/output.html`)  

---

### **🔹 Phase B: Business Automation Tasks**
✔️ **API Data Fetching & Web Scraping**  
- Fetch data from an **external API** and save results (`/data/api-results.json`)  
- Scrape and extract website content (`/data/web-content.txt`)  

✔️ **Git & Code Operations**  
- Clone Git repositories and make commits automatically  
- Run SQL queries on SQLite or DuckDB databases  

✔️ **File & Image Processing**  
- **Compress or resize images** (`/data/image-resized.jpg`)  
- **Convert Markdown to HTML** (`/data/output.html`)  

✔️ **Secure Execution & Compliance**  
- ✅ **Never accesses files outside `/data/`**
- ✅ **Never deletes or exfiltrates data**
- ✅ **Ensures data integrity**  

---

## **🚀 How to Run**
### **🔹 1. Pull & Run the Docker Container**
```bash
podman run -e AIPROXY_TOKEN=your_token -p 8000:8000 wasimansariiitm/my-ai-agent
```
### **🔹 2. Trigger an API Task**
#### **Run a Task (Example: Count Wednesdays in `/data/dates.txt`)**
```bash
curl "http://localhost:8000/run?task=Count the number of Wednesdays"
```

#### **Read a File (Example: `/data/output.txt`)**
```bash
curl "http://localhost:8000/read?path=output.txt"
```

---

## **🔑 Security & Compliance**
- **Restricts file operations to `/data/`**
- **Ensures `AIPROXY_TOKEN` is set before execution**
- **Handles all requests securely & efficiently**

---

## **📩 Contact & Support**
For issues, feature requests, or contributions, feel free to create an issue in the repository. 🚀

---
