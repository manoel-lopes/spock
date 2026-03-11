from src.infra.adapters.analysis.implementations.heuristic_transparency_analyzer import (
    HeuristicTransparencyAnalyzer,
)


def test_analyze_detects_all_metrics():
    text = """
    A vacância física do fundo ficou em 5%. A vacância financeira foi de 3%.
    O WALT médio é de 5 anos. Os principais inquilinos são empresas de logística.
    A carteira de ativos imóveis inclui 10 propriedades. A inadimplência está em 2%.
    O cap rate médio é de 8%. O pipeline de aquisição inclui 3 novos ativos.
    A dívida total representa 15% do patrimônio. O comentário gerencial apresenta
    perspectiva positiva para o próximo trimestre.
    """
    analyzer = HeuristicTransparencyAnalyzer()
    result = analyzer.analyze(text)

    assert result.quality_score == 1.0
    assert all(result.detected_metrics.values())
    assert all(w == 1.0 for w in result.weights.values())


def test_analyze_empty_text():
    analyzer = HeuristicTransparencyAnalyzer()
    result = analyzer.analyze("")

    assert result.quality_score == 0.0
    assert not any(result.detected_metrics.values())


def test_analyze_partial_metrics():
    text = "A vacância física do fundo ficou em 5%. O cap rate é de 8%."
    analyzer = HeuristicTransparencyAnalyzer()
    result = analyzer.analyze(text)

    assert result.detected_metrics["vacancia_fisica"] is True
    assert result.detected_metrics["cap_rate"] is True
    assert result.detected_metrics["walt"] is False
    assert result.quality_score == 0.2


def test_version():
    analyzer = HeuristicTransparencyAnalyzer()
    assert analyzer.get_version() == "1.0.0"
