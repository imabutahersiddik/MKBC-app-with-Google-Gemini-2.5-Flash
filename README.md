# MindsDB Knowledge Base CLI with Google Gemini 2.5 Flash

A command-line tool to create, populate, index, and query a MindsDB Knowledge Base using the Google Gemini 2.5 Flash model for semantic embeddings and reranking.

---

## Features

- Create a MindsDB Knowledge Base with Gemini 2.5 Flash embedding and reranking models  
- Ingest CSV data into the knowledge base  
- Create semantic search index on the knowledge base  
- Perform semantic search queries with relevance filtering  
- Supports MindsDB projects for organizing knowledge bases  
- Robust error handling and logging  

---

## Prerequisites

- Python 3.8+  
- MindsDB Python SDK (`mindsdb-sdk`)  
- MindsDB Cloud account with API key ([Get your MindsDB API key](https://mdb.ai/))  
- Google Gemini API key for Gemini 2.5 Flash model  
- CSV data file to ingest  

---

## Installation

1. Clone this repository or copy the CLI script `kb_cli_gemini.py`.  
2. Install dependencies:

```bash
pip install mindsdb-sdk pandas
```

---

## Usage

### 1. Ingest Data into Knowledge Base

```bash
python kb_cli_gemini.py \
  --api_key YOUR_MINDSDB_API_KEY \
  --gemini_api_key YOUR_GOOGLE_GEMINI_API_KEY \
  --kb_name your_kb_name \
  --input_file your_data.csv
```

- Creates the Gemini ML engine (if not exists)  
- Creates the knowledge base with Gemini embedding and reranking models  
- Inserts data from the CSV file  
- Creates a semantic index  

---

### 2. Perform Semantic Search Queries

```bash
python kb_cli_gemini.py \
  --api_key YOUR_MINDSDB_API_KEY \
  --kb_name your_kb_name \
  --query "Your semantic search query here" \
  --limit 5 \
  --relevance_threshold 0.6
```

- Returns up to 5 most relevant results matching the query  
- Filters results by a minimum relevance threshold  

---

### 3. Optional Arguments

- `--project`: Specify MindsDB project name to organize knowledge bases  
- `--limit`: Maximum number of results to return (default: 10)  
- `--relevance_threshold`: Minimum relevance score for filtering results (default: 0.5)  

---

## CSV Data Format

Your CSV file should contain:

- A unique identifier column (default `"id"`, or first column if `"id"` not present)  
- One or more content columns (default `"content"`, or all columns except ID and metadata)  
- Optional metadata columns  

Example:

```csv
id,content,category
1,"How to reset password?","support"
2,"Pricing plans and billing info","sales"
3,"Troubleshooting login issues","support"
```

---

## Environment Variables (Recommended)

For security, consider storing API keys in environment variables instead of passing via CLI:

```bash
export MINDSDB_API_KEY="your_mindsdb_api_key"
export GOOGLE_GEMINI_API_KEY="your_google_gemini_api_key"
```

Modify the script to read these variables with `os.getenv()`.

---

## Troubleshooting

- **"Already exists" errors:** The app logs warnings if the engine or knowledge base already exists and continues.  
- **API key issues:** Ensure your MindsDB and Google Gemini API keys are valid and have proper permissions.  
- **CSV loading errors:** Verify the CSV format and encoding.

---

## License

MIT License

---

## Contact

For questions or support, please open an issue or contact the maintainer.