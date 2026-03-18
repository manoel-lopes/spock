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

TEXT_TRUNCATE_LIMIT = 4000
ALGORITHM_VERSION = "2.0.0-llm"


@dataclass
class MetricDefinition:
    key: str
    keywords: list[str]


class LlmTransparencyAnalyzer(TransparencyAnalyzer):
    def __init__(
        self,
        metrics: list[MetricDefinition],
        api_key: str,
        model: str,
        fallback_analyzer: TransparencyAnalyzer,
    ) -> None:
        self._metrics = metrics
        self._model = model
        self._fallback = fallback_analyzer
        self._client = genai.Client(api_key=api_key)

    def analyze(self, text: str) -> AnalysisResult:
        try:
            return self._analyze_with_llm(text)
        except Exception:
            logger.exception("LLM analysis failed, falling back to heuristic")
            return self._fallback.analyze(text)

    def _analyze_with_llm(self, text: str) -> AnalysisResult:
        truncated = text[:TEXT_TRUNCATE_LIMIT]
        prompt = self._build_prompt(truncated)

        response = self._client.models.generate_content(
            model=self._model,
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "temperature": 0.1,
                "http_options": {"timeout": 15_000},
            },
        )

        raw = json.loads(response.text)
        return self._parse_response(raw)

    def _build_prompt(self, text: str) -> str:
        metric_lines = []
        for m in self._metrics:
            hints = ", ".join(m.keywords)
            metric_lines.append(f'- "{m.key}": keywords hint: [{hints}]')

        metrics_block = "\n".join(metric_lines)

        return f"""You are an analyst evaluating a Brazilian FII (Fundo de Investimento Imobiliário) monthly report.

For each metric below, determine whether the report text **meaningfully discusses** that metric (not just mentions a keyword in passing). Return a confidence score from 0.0 to 1.0 where:
- 0.0 = metric is completely absent
- 0.3 = metric is briefly mentioned without substance
- 0.7 = metric is discussed with some data or context
- 1.0 = metric is thoroughly covered with detailed data

Metrics to evaluate:
{metrics_block}

Return JSON with this exact structure:
{{"metrics": {{"metric_key": {{"detected": true/false, "confidence": 0.0}}}}}}

Set "detected" to true if confidence >= 0.3.

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
