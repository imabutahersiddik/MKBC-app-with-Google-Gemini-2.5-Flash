# MindsDB Knowledge Base CLI with Google Gemini 2.5 Flash, Jobs, Metadata & AI Tables

A powerful command-line tool to create, populate, index, and query a MindsDB Knowledge Base using Google Gemini 2.5 Flash embeddings and reranking. Supports asynchronous JOBs for ingestion and indexing, advanced metadata handling, and MindsDB AI Tables for summarization, classification, and generation tasks.

---

## Features

- Create MindsDB Knowledge Base with Gemini 2.5 Flash embedding and reranking models  
- Asynchronous data ingestion and index creation using MindsDB JOBs  
- Semantic search with metadata columns and SQL window functions (e.g., `LAST_VALUE`)  
- Create and query MindsDB AI Tables for tasks like summarization, classification, and generation  
- Support for MindsDB projects to organize knowledge bases  
- Robust logging and error handling  

---

## Prerequisites

- Python 3.8+  
- MindsDB Python SDK (`mindsdb-sdk`)  
- Pandas (`pandas`)  
- MindsDB Cloud account with API key ([Get your MindsDB API key](https://mdb.ai/))  
- Google Gemini API key for Gemini 2.5 Flash model  
- CSV data file for ingestion  

---

## Installation

1. Clone this repository or copy the CLI script `kb_cli_advanced.py`.  
2. Install dependencies:

```bash
pip install mindsdb-sdk pandas
```

---

## Usage

### 1. Create Gemini Engine (Automatically done when ingesting data if Gemini API key provided)

```bash
python kb_cli_advanced.py --api_key YOUR_MINDSDB_API_KEY --gemini_api_key YOUR_GOOGLE_GEMINI_API_KEY
```

---

### 2. Ingest Data into Knowledge Base (Async with JOB)

```bash
python kb_cli_advanced.py \
  --api_key YOUR_MINDSDB_API_KEY \
  --gemini_api_key YOUR_GOOGLE_GEMINI_API_KEY \
  --kb_name your_kb_name \
  --input_file your_data.csv
```

- Creates the Gemini ML engine (if not exists)  
- Creates the knowledge base with Gemini embedding and reranking models  
- Inserts data asynchronously using MindsDB JOBs  
- Creates semantic index asynchronously  

---

### 3. Perform Semantic Search Queries with Metadata Handling

```bash
python kb_cli_advanced.py \
  --api_key YOUR_MINDSDB_API_KEY \
  --kb_name your_kb_name \
  --query "Your semantic search query here" \
  --limit 5 \
  --relevance_threshold 0.6
```

- Returns relevant results filtered by relevance score  
- Includes example metadata handling with SQL window functions (e.g., latest update timestamp)  

---

### 4. Create an AI Table (Summarization, Classification, Generation)

```bash
python kb_cli_advanced.py \
  --api_key YOUR_MINDSDB_API_KEY \
  --project your_project_name \
  --create_ai_table \
  --ai_table_name your_ai_table \
  --source_table your_kb_name \
  --task_type summarization \
  --input_columns content \
  --output_column summary
```

- Creates an AI Table based on your knowledge base or other source table  
- Supports tasks: `summarization`, `classification`, `generation`  

---

### 5. Query an AI Table

```bash
python kb_cli_advanced.py \
  --api_key YOUR_MINDSDB_API_KEY \
  --query_ai_table \
  --ai_table_name your_ai_table \
  --limit 5
```

- Query AI Table results with optional filtering  

---

## CSV Data Format

Your CSV file should contain:

- Unique identifier column (default `"id"` or first column if `"id"` missing)  
- Content columns (default `"content"` or all except ID and metadata)  
- Optional metadata columns (e.g., timestamps, categories)  

Example:

```csv
id,content,category,updated_at
1,"How to reset password?","support","2025-06-10"
2,"Pricing plans and billing info","sales","2025-06-12"
3,"Troubleshooting login issues","support","2025-06-11"
```

---

## Environment Variables (Recommended)

Store API keys securely:

```bash
export MINDSDB_API_KEY="your_mindsdb_api_key"
export GOOGLE_GEMINI_API_KEY="your_google_gemini_api_key"
```

Modify the script to use `os.getenv()` for keys if preferred.

---

## Troubleshooting

- **"Already exists" warnings:** Safe to ignore; the app continues if engine or KB exists.  
- **API key issues:** Verify API keys and permissions.  
- **CSV loading errors:** Check CSV format, encoding, and column names.  
- **Job failures:** Check MindsDB dashboard or logs for detailed job status.

---

## License

MIT License

---

## Contact

For questions or support, please open an issue or contact the maintainer.