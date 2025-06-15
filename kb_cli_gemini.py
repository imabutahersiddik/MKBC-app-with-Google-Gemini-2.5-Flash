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

    def insert_data_with_job(self, kb_name, df: pd.DataFrame):
        """
        Insert data asynchronously using MindsDB JOB mechanism.
        """
        full_kb_name = f"{self.project}.{kb_name}" if self.project else kb_name
        logging.info(f"Starting async data ingestion job for knowledge base '{full_kb_name}' with {len(df)} rows...")

        try:
            kb = self.client.knowledge_bases.get(full_kb_name)
            job = kb.insert(df, async_mode=True)
            logging.info(f"Job {job.id} started for data ingestion.")
            job.wait()  # Wait for job completion; remove or adjust for non-blocking
            logging.info(f"Job {job.id} completed with status: {job.status}")
        except MindsDBException as e:
            logging.error(f"Failed to insert data with job: {e}")
            raise

    def create_index_with_job(self, kb_name):
        """
        Create index asynchronously using MindsDB JOB.
        """
        full_kb_name = f"{self.project}.{kb_name}" if self.project else kb_name
        logging.info(f"Starting async index creation job for knowledge base '{full_kb_name}'...")

        try:
            job = self.client.query_async(f"CREATE INDEX ON KNOWLEDGE_BASE {full_kb_name}")
            logging.info(f"Job {job.id} started for index creation.")
            job.wait()
            logging.info(f"Job {job.id} completed with status: {job.status}")
        except MindsDBException as e:
            logging.error(f"Failed to create index with job: {e}")
            raise

    def semantic_search(self, kb_name, query, limit=10, relevance_threshold=0.5):
        full_kb_name = f"{self.project}.{kb_name}" if self.project else kb_name
        logging.info(f"Performing semantic search on '{full_kb_name}' for query: {query}")

        query_escaped = query.replace("'", "''")

        # Example: using LAST_VALUE window function on a metadata column 'updated_at' to get latest metadata per id
        sql = f"""
        SELECT id, content,
          LAST_VALUE(updated_at) OVER (PARTITION BY id ORDER BY updated_at ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) AS latest_update,
          relevance_score
        FROM {full_kb_name}
        WHERE content LIKE '{query_escaped}'
          AND relevance_score >= {relevance_threshold}
        ORDER BY relevance_score DESC
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

    def create_ai_table(self, ai_table_name, source_table, task_type, input_columns, output_column):
        """
        Create an AI Table for tasks like summarization, classification, or generation.
        """
        full_ai_table_name = f"{self.project}.{ai_table_name}" if self.project else ai_table_name
        logging.info(f"Creating AI Table '{full_ai_table_name}' for task '{task_type}'...")

        input_cols_str = ", ".join(input_columns)

        create_ai_table_sql = f"""
        CREATE AI TABLE {full_ai_table_name}
        AS SELECT {input_cols_str}
        FROM {source_table}
        PREDICT {output_column}
        USING task = '{task_type}';
        """

        try:
            self.client.query(create_ai_table_sql)
            logging.info(f"AI Table '{full_ai_table_name}' created successfully.")
        except MindsDBException as e:
            if "already exists" in str(e).lower():
                logging.warning(f"AI Table '{full_ai_table_name}' already exists.")
            else:
                logging.error(f"Failed to create AI Table: {e}")
                raise

    def query_ai_table(self, ai_table_name, query_filter=None, limit=10):
        full_ai_table_name = f"{self.project}.{ai_table_name}" if self.project else ai_table_name
        logging.info(f"Querying AI Table '{full_ai_table_name}'...")

        where_clause = f"WHERE {query_filter}" if query_filter else ""
        sql = f"SELECT * FROM {full_ai_table_name} {where_clause} LIMIT {limit};"

        try:
            result = self.client.query(sql)
            if not result or len(result) == 0:
                logging.info("No AI Table results found.")
                return []
            return result
        except MindsDBException as e:
            logging.error(f"Failed to query AI Table: {e}")
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
    parser = argparse.ArgumentParser(description="Advanced MindsDB Knowledge Base CLI with Jobs, Metadata, and AI Tables")

    parser.add_argument('--api_key', required=True, help='MindsDB API key')
    parser.add_argument('--kb_name', help='Knowledge base name')
    parser.add_argument('--project', default=None, help='MindsDB project name (optional)')
    parser.add_argument('--gemini_api_key', help='Google Gemini API key')
    parser.add_argument('--input_file', help='CSV file path to ingest data')
    parser.add_argument('--query', help='Semantic query string')
    parser.add_argument('--limit', type=int, default=10, help='Max results to return for queries')
    parser.add_argument('--relevance_threshold', type=float, default=0.5, help='Relevance threshold for semantic search')
    parser.add_argument('--create_ai_table', action='store_true', help='Flag to create an AI Table')
    parser.add_argument('--ai_table_name', help='Name of AI Table to create or query')
    parser.add_argument('--source_table', help='Source table for AI Table creation')
    parser.add_argument('--task_type', choices=['summarization', 'classification', 'generation'], help='AI task type')
    parser.add_argument('--input_columns', nargs='+', help='Input columns for AI Table')
    parser.add_argument('--output_column', help='Output prediction column for AI Table')
    parser.add_argument('--query_ai_table', action='store_true', help='Flag to query an AI Table')
    parser.add_argument('--ai_query_filter', help='Filter condition for querying AI Table')

    args = parser.parse_args()

    kb_cli = MindsDBGeminiKBCLI(api_key=args.api_key, project=args.project)
    engine_name = "google_gemini_engine"

    # Create Gemini engine if Gemini API key provided
    if args.gemini_api_key:
        kb_cli.create_gemini_engine(engine_name, args.gemini_api_key)

    # Knowledge base ingestion and indexing with Jobs
    if args.kb_name and args.input_file:
        df = load_csv(args.input_file)

        id_column = "id" if "id" in df.columns else df.columns[0]
        content_columns = ["content"] if "content" in df.columns else [col for col in df.columns if col != id_column]
        metadata_columns = [col for col in df.columns if col not in content_columns + [id_column]]

        kb_cli.create_knowledge_base(
            kb_name=args.kb_name,
            engine_name=engine_name,
            metadata_columns=metadata_columns,
            content_columns=content_columns,
            id_column=id_column
        )

        kb_cli.insert_data_with_job(args.kb_name, df)
        kb_cli.create_index_with_job(args.kb_name)

    # Semantic search query
    if args.kb_name and args.query:
        results = kb_cli.semantic_search(
            kb_name=args.kb_name,
            query=args.query,
            limit=args.limit,
            relevance_threshold=args.relevance_threshold
        )
        if results:
            print("Semantic Search Results:")
            for row in results:
                print(row)

    # AI Table creation
    if args.create_ai_table:
        if not all([args.ai_table_name, args.source_table, args.task_type, args.input_columns, args.output_column]):
            logging.error("AI Table creation requires --ai_table_name, --source_table, --task_type, --input_columns, and --output_column.")
            return
        kb_cli.create_ai_table(
            ai_table_name=args.ai_table_name,
            source_table=args.source_table,
            task_type=args.task_type,
            input_columns=args.input_columns,
            output_column=args.output_column
        )

    # AI Table query
    if args.query_ai_table and args.ai_table_name:
        results = kb_cli.query_ai_table(
            ai_table_name=args.ai_table_name,
            query_filter=args.ai_query_filter,
            limit=args.limit
        )
        if results:
            print("AI Table Query Results:")
            for row in results:
                print(row)

if __name__ == "__main__":
    main()
