import pytest
import pandas as pd
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models import (
    CleanerResult,
    ValidatorResult,
    TransformerResult,
    AnomalyResult,
    SummariserResult,
    PipelineResult
)

SAMPLE_CSV = """transaction_id,date,customer_id,product_name,quantity,unit_price,total
TXN001,2024-01-15,CUST_001,Product A,2,10.00,20.00
TXN002,2024-01-16,CUST_002,Product B,1,15.00,15.00
TXN003,2024-01-17,,Product C,3,5.00,15.00
TXN004,2024-01-18,CUST_004,Product D,1,999.99,999.99
TXN005,2024-01-19,CUST_005,Product E,2,8.00,16.00"""


class TestModels:

    def test_cleaner_result_creation(self):
        result = CleanerResult(
            issues_fixed=["Fixed null values", "Standardised dates"],
            rows_affected=3,
            cleaned_columns=["date", "customer_id"]
        )
        assert result.rows_affected == 3
        assert len(result.issues_fixed) == 2
        assert "date" in result.cleaned_columns

    def test_validator_result_creation(self):
        result = ValidatorResult(
            schema_ok=True,
            violations=["Missing customer_id in row 3"],
            passed_checks=["Date format valid", "No duplicate IDs"],
            completeness_score=85.5
        )
        assert result.schema_ok is True
        assert result.completeness_score == 85.5
        assert len(result.violations) == 1

    def test_transformer_result_creation(self):
        result = TransformerResult(
            transformations_applied=["Standardised date format"],
            new_columns=["year", "month"],
            rows_transformed=5
        )
        assert result.rows_transformed == 5
        assert "year" in result.new_columns

    def test_anomaly_result_creation(self):
        result = AnomalyResult(
            anomalies=["Price outlier in TXN004 — £999.99"],
            anomaly_count=1,
            anomaly_score=8.5,
            flagged_rows=[4]
        )
        assert result.anomaly_count == 1
        assert result.anomaly_score == 8.5
        assert 4 in result.flagged_rows

    def test_summariser_result_creation(self):
        result = SummariserResult(
            summary="Dataset contains 5 retail transactions.",
            key_stats={"Total Rows": "5", "Categories": "1"},
            recommendations=["Review TXN004 price anomaly"]
        )
        assert len(result.recommendations) == 1
        assert "Total Rows" in result.key_stats

    def test_pipeline_result_creation(self):
        cleaner = CleanerResult(
            issues_fixed=["Fixed nulls"],
            rows_affected=1,
            cleaned_columns=["customer_id"]
        )
        result = PipelineResult(
            file_name="test.csv",
            total_rows=5,
            cleaner=cleaner,
            status="complete"
        )
        assert result.file_name == "test.csv"
        assert result.total_rows == 5
        assert result.status == "complete"
        assert result.cleaner.rows_affected == 1


class TestCSVLoading:

    def test_csv_loads_correctly(self, tmp_path):
        csv_file = tmp_path / "test.csv"
        csv_file.write_text(SAMPLE_CSV)
        df = pd.read_csv(csv_file)
        assert len(df) == 5
        assert "transaction_id" in df.columns
        assert "customer_id" in df.columns

    def test_csv_preview_generation(self, tmp_path):
        csv_file = tmp_path / "test.csv"
        csv_file.write_text(SAMPLE_CSV)
        df = pd.read_csv(csv_file)
        preview = df.head(20).to_csv(index=False)
        assert "TXN001" in preview
        assert "transaction_id" in preview

    def test_demo_csv_exists(self):
        assert os.path.exists("demo/sample_data.csv"), \
            "Demo CSV file missing from demo/ folder"

    def test_demo_csv_has_correct_columns(self):
        df = pd.read_csv("demo/sample_data.csv")
        expected_columns = [
            "transaction_id", "date", "customer_id",
            "product_name", "quantity", "unit_price", "total"
        ]
        for col in expected_columns:
            assert col in df.columns, f"Missing column: {col}"

    def test_demo_csv_has_rows(self):
        df = pd.read_csv("demo/sample_data.csv")
        assert len(df) > 0, "Demo CSV is empty"


class TestDuckDBConnector:

    @pytest.fixture
    def duckdb_file(self, tmp_path):
        import duckdb
        db_path = str(tmp_path / "test.duckdb")
        conn = duckdb.connect(db_path)
        conn.execute("""
            CREATE TABLE transactions (
                transaction_id VARCHAR,
                product_name VARCHAR,
                unit_price DOUBLE
            )
        """)
        conn.execute("""
            INSERT INTO transactions VALUES
            ('TXN001', 'Product A', 10.00),
            ('TXN002', 'Product B', 15.00),
            ('TXN003', 'Product C', 5.00)
        """)
        conn.close()
        return db_path

    def test_list_tables(self, duckdb_file):
        from src.connectors.duckdb_conn import list_tables
        tables = list_tables(duckdb_file)
        assert "transactions" in tables

    def test_fetch_table(self, duckdb_file):
        from src.connectors.duckdb_conn import fetch_table
        df = fetch_table(duckdb_file, "transactions")
        assert len(df) == 3
        assert "transaction_id" in df.columns
        assert "unit_price" in df.columns

    def test_fetch_table_limit(self, duckdb_file):
        from src.connectors.duckdb_conn import fetch_table
        df = fetch_table(duckdb_file, "transactions", limit=2)
        assert len(df) == 2


class TestPDFExists:

    def test_demo_pdf_exists(self):
        assert os.path.exists("demo/sample_report.pdf"), \
            "Demo PDF file missing from demo/ folder"


class TestEnvironment:

    def test_api_key_exists(self):
        from dotenv import load_dotenv
        load_dotenv()
        api_key = os.getenv("ANTHROPIC_API_KEY")
        assert api_key is not None, "ANTHROPIC_API_KEY not set in .env"
        assert api_key.startswith("sk-ant-"), \
            "ANTHROPIC_API_KEY does not look valid"

    def test_venv_packages_installed(self):
        import anthropic
        import pandas
        import pydantic
        import typer
        import rich
        import streamlit
        assert True