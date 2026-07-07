"""Integration tests for the multi-agent data pipeline.

These tests mock LLM calls to verify pipeline orchestration,
router logic, and guardrail execution without requiring a real API key.
"""

import os
import sys
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestRouterLogic:
    """Test the model routing logic."""

    def test_simple_agents_route_to_haiku(self):
        from src.router import route

        result = route("cleaner", total_rows=100, routing_enabled=True)
        assert "haiku" in result.model.lower()
        assert result.model_label == "Haiku"

    def test_complex_agents_route_to_sonnet(self):
        from src.router import route

        result = route("validator", total_rows=100, routing_enabled=True)
        assert "sonnet" in result.model.lower()
        assert result.model_label == "Sonnet"

    def test_routing_disabled_uses_sonnet(self):
        from src.router import route

        result = route("cleaner", total_rows=100, routing_enabled=False)
        assert "sonnet" in result.model.lower()
        assert result.routing_enabled is False

    def test_pii_anonymiser_routes_to_haiku(self):
        from src.router import route

        result = route("pii_anonymiser", total_rows=100, routing_enabled=True)
        assert "haiku" in result.model.lower()

    def test_all_csv_agents_have_routing(self):
        from src.router import route

        csv_agents = [
            "cleaner",
            "pii_anonymiser",
            "validator",
            "transformer",
            "anomaly",
            "summariser",
        ]
        for agent in csv_agents:
            result = route(agent, total_rows=50, routing_enabled=True)
            assert result.model is not None, f"No model assigned for {agent}"
            assert result.agent_name == agent


class TestGuardrailLogic:
    """Test guardrail engine behavior."""

    def test_budget_check_passes_under_limit(self):
        from src.observability.guardrails import GuardrailEngine

        engine = GuardrailEngine(budget_cap_gbp=1.0)
        result = engine.check_budget(0.5)
        assert result.passed is True
        assert result.action == "continue"

    def test_budget_check_fails_over_limit(self):
        from src.observability.guardrails import GuardrailEngine

        engine = GuardrailEngine(budget_cap_gbp=0.5)
        result = engine.check_budget(0.6)
        assert result.passed is False
        assert result.action == "stop"

    def test_parse_failure_check_passes(self):
        from src.observability.guardrails import GuardrailEngine

        engine = GuardrailEngine(max_parse_failures=3)
        result = engine.check_parse_failures(2)
        assert result.passed is True

    def test_parse_failure_check_fails(self):
        from src.observability.guardrails import GuardrailEngine

        engine = GuardrailEngine(max_parse_failures=3)
        result = engine.check_parse_failures(3)
        assert result.passed is False
        assert result.action == "stop"

    def test_anomaly_score_warning(self):
        from src.observability.guardrails import GuardrailEngine

        engine = GuardrailEngine(anomaly_score_warn=9.0)
        result = engine.check_anomaly_score(9.5)
        assert result.action == "warn"

    def test_anomaly_score_pass(self):
        from src.observability.guardrails import GuardrailEngine

        engine = GuardrailEngine(anomaly_score_warn=9.0)
        result = engine.check_anomaly_score(7.0)
        assert result.action == "continue"


class TestPipelineOrchestration:
    """Test pipeline orchestration with mocked LLM calls."""

    def _make_mock_response(self, text):
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=text)]
        mock_response.usage = MagicMock()
        mock_response.usage.input_tokens = 100
        mock_response.usage.output_tokens = 50
        return mock_response

    def _mock_all_agents(self):
        """Set up mocks for all 5 agents with correct per-agent JSON responses."""
        cleaner_json = '{"issues_fixed": [], "rows_affected": 0, "cleaned_columns": []}'
        validator_json = '{"schema_ok": true, "violations": [], "passed_checks": ["schema"], "completeness_score": 100.0}'
        transformer_json = (
            '{"transformations_applied": [], "new_columns": [], "rows_transformed": 0}'
        )
        anomaly_json = '{"anomalies": [], "anomaly_count": 0, "anomaly_score": 0.0, "flagged_rows": []}'
        summariser_json = '{"summary": "Test summary.", "key_stats": {"Total Rows": "15"}, "recommendations": []}'

        patches = {
            "src.agents.cleaner.Anthropic": cleaner_json,
            "src.agents.validator.Anthropic": validator_json,
            "src.agents.transformer.Anthropic": transformer_json,
            "src.agents.anomaly.Anthropic": anomaly_json,
            "src.agents.summariser.Anthropic": summariser_json,
        }
        mocks = {}
        for path, json_text in patches.items():
            mock_cls = MagicMock()
            mock_instance = MagicMock()
            mock_instance.messages.create.return_value = self._make_mock_response(
                json_text
            )
            mock_cls.return_value = mock_instance
            mocks[path] = mock_cls
        return mocks

    def test_csv_pipeline_end_to_end(self):
        """Test full CSV pipeline with mocked LLM responses."""
        mocks = self._mock_all_agents()
        with (
            patch(
                "src.agents.cleaner.Anthropic", mocks["src.agents.cleaner.Anthropic"]
            ),
            patch(
                "src.agents.validator.Anthropic",
                mocks["src.agents.validator.Anthropic"],
            ),
            patch(
                "src.agents.transformer.Anthropic",
                mocks["src.agents.transformer.Anthropic"],
            ),
            patch(
                "src.agents.anomaly.Anthropic", mocks["src.agents.anomaly.Anthropic"]
            ),
            patch(
                "src.agents.summariser.Anthropic",
                mocks["src.agents.summariser.Anthropic"],
            ),
        ):
            from src.pipeline import run_pipeline

            result = run_pipeline("demo/sample_data.csv")

        assert result.status == "complete"
        assert result.cleaner is not None
        assert result.validator is not None
        assert result.transformer is not None
        assert result.anomaly is not None
        assert result.summariser is not None

    def test_pipeline_records_telemetry(self):
        """Test that pipeline records telemetry for each agent."""
        mocks = self._mock_all_agents()
        with (
            patch(
                "src.agents.cleaner.Anthropic", mocks["src.agents.cleaner.Anthropic"]
            ),
            patch(
                "src.agents.validator.Anthropic",
                mocks["src.agents.validator.Anthropic"],
            ),
            patch(
                "src.agents.transformer.Anthropic",
                mocks["src.agents.transformer.Anthropic"],
            ),
            patch(
                "src.agents.anomaly.Anthropic", mocks["src.agents.anomaly.Anthropic"]
            ),
            patch(
                "src.agents.summariser.Anthropic",
                mocks["src.agents.summariser.Anthropic"],
            ),
        ):
            from src.pipeline import run_pipeline

            result = run_pipeline("demo/sample_data.csv")

        assert len(result.telemetry) > 0
        assert result.total_cost_gbp >= 0
        assert result.total_latency_ms >= 0

    def test_pipeline_handles_missing_file(self):
        """Test pipeline gracefully handles missing CSV file."""
        from src.pipeline import run_pipeline

        # The pipeline catches FileNotFoundError and returns an error result
        try:
            result = run_pipeline("nonexistent.csv")
            # If it returns a result, check it's an error
            assert result.status == "error" or result.cleaner is None
        except FileNotFoundError:
            # If it raises FileNotFoundError, that's also acceptable behavior
            pass


class TestCLIImports:
    """Test that CLI and app entry points import without errors."""

    def test_cli_app_imports(self):
        from main import app

        assert app is not None

    def test_pipeline_imports(self):
        from src.pipeline import run_pipeline

        assert callable(run_pipeline)

    def test_router_imports(self):
        from src.router import route

        assert callable(route)

    def test_guardrails_imports(self):
        from src.observability.guardrails import GuardrailEngine

        assert GuardrailEngine is not None

    def test_models_imports(self):
        from src.models import CleanerResult, PipelineResult, ValidatorResult

        assert PipelineResult is not None
        assert CleanerResult is not None
        assert ValidatorResult is not None
