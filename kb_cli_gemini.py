import argparse
import logging
import pandas as pd
from mindsdb_sdk import MindsDB
from mindsdb_sdk.exceptions import MindsDBException

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

class MindsDBGeminiKBCLI:
    def __init__(self, api_key, project=None):
        self.api_key = api_key
        self.project = project
        self.client = MindsDB(api_key=api_key)
        if project:
            self.project_obj = self.client.projects.get(project)
        else:
            self.project_obj = None

    def create_gemini_engine(self, engine_name: str, gemini_api_key: str):
        """
        Create a MindsDB ML engine for Google Gemini 2.5 Flash.
        """
        logging.info(f"Creating Gemini ML engine '{engine_name}'...")
        create_engine_sql = f"""
        CREATE ML_ENGINE {engine_name}
        FROM google_gemini
        USING api_key = '{gemini_api_key}';
        """
        try:
            self.client.query(create_engine_sql)
            logging.info(f"Gemini ML engine '{engine_name}' created successfully.")
        except MindsDBException as e:
            if "already exists" in str(e).lower():
                logging.warning(f"Gemini ML engine '{engine_name}' already exists.")
            else:
                logging.error(f"Failed to create Gemini ML engine: {e}")
                raise

    def create_knowledge_base(self, kb_name, engine_name,
                              metadata_columns=None,
                              content_columns=None,
                              id_column="id"):
        """
        Create a MindsDB knowledge base using Gemini 2.5 Flash engine.
        """
        metadata_columns = metadata_columns or []
        content_columns = content_columns or ["content"]
        full_kb_name = f"{self.project}.{kb_name}" if self.project else kb_name

        logging.info(f"Creating knowledge base '{full_kb_name}' with Gemini engine '{engine_name}'...")

        create_kb_sql = f"""
        CREATE KNOWLEDGE_BASE {full_kb_name}
        USING
        embedding_model = {{
            "provider": "google_gemini",
            "engine": "{engine_name}",
            "model_name": "gemini-2-5-flash"
        }},
        reranking_model = {{
            "provider": "google_gemini",
            "engine": "{engine_name}",
            "model_name": "gemini-2-5-flash"
        }},
        metadata_columns = {metadata_columns},
        content_columns = {content_columns},
        id_column = '{id_column}';
        """

        try:
            self.client.query(create_kb_sql)
            logging.info(f"Knowledge base '{full_kb_name}' created successfully.")
        except MindsDBException as e:
            if "already exists" in str(e).lower():
                logging.warning(f"Knowledge base '{full_kb_name}' already exists.")
            else:
                logging.error(f"Failed to create knowledge base: {e}")
                raise

    def insert_data(self, kb_name, df: pd.DataFrame):
        """
        Insert data from a pandas DataFrame into the knowledge base.
        """
        full_kb_name = f"{self.project}.{kb_name}" if self.project else kb_name
        logging.info(f"Inserting {len(df)} rows into knowledge base '{full_kb_name}'...")

        try:
            kb = self.client.knowledge_bases.get(full_kb_name)
            kb.insert(df)
            logging.info("Data inserted successfully.")
        except MindsDBException as e:
            logging.error(f"Failed to insert data: {e}")
            raise

    def create_index(self, kb_name):
        """
        Create an index on the knowledge base.
        """
        full_kb_name = f"{self.project}.{kb_name}" if self.project else kb_name
        logging.info(f"Creating index on knowledge base '{full_kb_name}'...")
        try:
            self.client.query(f"CREATE INDEX ON KNOWLEDGE_BASE {full_kb_name}")
            logging.info("Index created successfully.")
        except MindsDBException as e:
            if "already exists" in str(e).lower():
                logging.warning(f"Index on knowledge base '{full_kb_name}' already exists.")
            else:
                logging.error(f"Failed to create index: {e}")
                raise

    def semantic_search(self, kb_name, query, limit=10, relevance_threshold=0.5):
        """
        Perform a semantic search query on the knowledge base.
        """
        full_kb_name = f"{self.project}.{kb_name}" if self.project else kb_name
        logging.info(f"Performing semantic search on '{full_kb_name}' for query: {query}")

        # Escape single quotes in query
        query_escaped = query.replace("'", "''")

        sql = f"""
        SELECT *
        FROM {full_kb_name}
        WHERE content LIKE '{query_escaped}'
        AND relevance_threshold = {relevance_threshold}
        LIMIT {limit};
        """

        try:
            result = self.client.query(sql)
            if not result or len(result) == 0:
                logging.info("No results found.")
                return []
            return result
        except MindsDBException as e:
            logging.error(f"Search query failed: {e}")
            raise

def load_csv(input_file):
    try:
        df = pd.read_csv(input_file)
        logging.info(f"Loaded {len(df)} rows from '{input_file}'.")
        return df
    except Exception as e:
        logging.error(f"Failed to load CSV file: {e}")
        raise

def main():
    parser = argparse.ArgumentParser(description="MindsDB Knowledge Base CLI with Gemini 2.5 Flash")

    parser.add_argument('--api_key', required=True, help='MindsDB API key')
    parser.add_argument('--kb_name', required=True, help='Knowledge base name')
    parser.add_argument('--project', default=None, help='MindsDB project name (optional)')
    parser.add_argument('--gemini_api_key', required=True, help='Google Gemini API key')
    parser.add_argument('--input_file', help='CSV file path to ingest data')
    parser.add_argument('--query', help='Semantic query string')
    parser.add_argument('--limit', type=int, default=10, help='Max results to return for query')
    parser.add_argument('--relevance_threshold', type=float, default=0.5, help='Relevance threshold for query filtering')

    args = parser.parse_args()

    kb_cli = MindsDBGeminiKBCLI(api_key=args.api_key, project=args.project)

    engine_name = "google_gemini_engine"

    # Create Gemini engine (idempotent)
    kb_cli.create_gemini_engine(engine_name, args.gemini_api_key)

    if args.input_file:
        df = load_csv(args.input_file)

        # Heuristically determine columns
        id_column = "id" if "id" in df.columns else df.columns[0]
        content_columns = ["content"] if "content" in df.columns else [col for col in df.columns if col != id_column]
        metadata_columns = [col for col in df.columns if col not in content_columns + [id_column]]

        # Create Knowledge Base with Gemini 2.5 Flash
        kb_cli.create_knowledge_base(
            kb_name=args.kb_name,
            engine_name=engine_name,
            metadata_columns=metadata_columns,
            content_columns=content_columns,
            id_column=id_column
        )

        # Insert data and create index
        kb_cli.insert_data(args.kb_name, df)
        kb_cli.create_index(args.kb_name)

    if args.query:
        results = kb_cli.semantic_search(
            kb_name=args.kb_name,
            query=args.query,
            limit=args.limit,
            relevance_threshold=args.relevance_threshold
        )
        if results:
            print("Search Results:")
            for row in results:
                print(row)

if __name__ == "__main__":
    main()
