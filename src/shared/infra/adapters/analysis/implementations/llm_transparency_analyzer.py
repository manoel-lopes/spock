from __future__ import annotations

import json
import logging
from dataclasses import dataclass

from google import genai

from src.shared.infra.adapters.analysis.ports.transparency_analyzer import (
    AnalysisResult,
    TransparencyAnalyzer,
)

logger = logging.getLogger(__name__)

TEXT_TRUNCATE_LIMIT = 100_000
ALGORITHM_VERSION = "3.0.0-llm"


@dataclass
class MetricDefinition:
    key: str
    keywords: list[str]
    description: str = ""
    scoring_rubric: str = ""


class LlmTransparencyAnalyzer(TransparencyAnalyzer):
    def __init__(
        self,
        metrics: list[MetricDefinition],
        api_key: str,
        model: str,
        fallback_analyzer: TransparencyAnalyzer,
        fund_type_label: str = "FII",
    ) -> None:
        self._metrics = metrics
        self._model = model
        self._fallback = fallback_analyzer
        self._client = genai.Client(api_key=api_key)
        self._system_prompt = self._build_system_prompt(fund_type_label)

    def analyze(self, text: str) -> AnalysisResult:
        try:
            return self._analyze_with_llm(text)
        except Exception:
            logger.exception("LLM analysis failed, falling back to heuristic")
            return self._fallback.analyze(text)

    def _analyze_with_llm(self, text: str) -> AnalysisResult:
        truncated = text[:TEXT_TRUNCATE_LIMIT]
        user_prompt = self._build_user_prompt(truncated)

        response = self._client.models.generate_content(
            model=self._model,
            contents=user_prompt,
            config={
                "system_instruction": self._system_prompt,
                "response_mime_type": "application/json",
                "temperature": 0.1,
                "http_options": {"timeout": 30_000},
            },
        )

        raw = json.loads(response.text)
        return self._parse_response(raw)

    def _build_system_prompt(self, fund_type_label: str) -> str:
        metric_sections = []
        for m in self._metrics:
            hints = ", ".join(m.keywords)
            section = f'### {m.key} — Keywords: [{hints}]'
            if m.description:
                section += f"\n{m.description}"
            if m.scoring_rubric:
                section += f"\n**Scoring guidance:**\n{m.scoring_rubric}"
            metric_sections.append(section)

        metrics_block = "\n\n".join(metric_sections)

        return f"""You are a senior analyst specializing in Brazilian FIIs (Fundos de Investimento Imobiliário).
You are evaluating a {fund_type_label} fund's monthly report ("relatório gerencial").

## Scoring Scale
- 0.0: Completely absent — no mention whatsoever
- 0.3: Mentioned in passing or section title only, no substantive data
- 0.7: Discussed with specific data points, percentages, or quantitative context
- 1.0: Thoroughly covered with detailed breakdowns, time-series, or stratified data

## Metrics to Evaluate

{metrics_block}

## Output Format
Return JSON with this exact structure:
{{"metrics": {{"metric_key": {{"detected": true/false, "confidence": 0.0}}}}}}

Set "detected" to true if confidence >= 0.3."""

    def _build_user_prompt(self, text: str) -> str:
        return f"""Analyze the following monthly report text and evaluate each metric according to the scoring scale.

Report text:
\"\"\"
{text}
\"\"\""""

    def _parse_response(self, raw: dict) -> AnalysisResult:
        metrics_data = raw.get("metrics", {})
        detected_metrics: dict[str, bool] = {}
        weights: dict[str, float] = {}

        for m in self._metrics:
            entry = metrics_data.get(m.key, {})
            confidence = float(entry.get("confidence", 0.0))
            confidence = max(0.0, min(1.0, confidence))
            detected = entry.get("detected", confidence >= 0.3)

            detected_metrics[m.key] = bool(detected)
            weights[m.key] = confidence

        quality_score = sum(weights.values()) / len(self._metrics) if self._metrics else 0.0

        return AnalysisResult(
            detected_metrics=detected_metrics,
            weights=weights,
            quality_score=quality_score,
        )

    def get_version(self) -> str:
        return ALGORITHM_VERSION
