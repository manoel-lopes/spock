from src.mortgage.analyzer import MortgageTransparencyAnalyzer


def test_analyze_detects_all_metrics():
    text = """
    O rating dos CRIs da carteira é majoritariamente AA. A classificação de risco
    mostra operações de CRI sólidas. A movimentação da carteira inclui aquisição de CRI
    e venda de CRI no período. O DRE apresenta demonstração de resultado com receitas,
    despesas e itens não recorrente. O acumulado dos últimos 12 meses mostra crescimento.
    O custo de alavancagem é CDI + 2%. O book de FIIs inclui posição em FIIs com
    preço médio atualizado. A diversificação setorial mostra exposição por securitizadora
    e concentração por setor. A reserva acumulada e resultado acumulado são positivos.
    O PDD e provisão para devedores duvidosos está controlado. A distribuição de rendimento
    e guidance de dividendo são transparentes. A inadimplência e reestruturação de operações
    são comentadas. O período de carência de juros está detalhado. A exposição ao risco
    é pulverizado. A subordinação entre cotas sênior e mezanino está clara.
    O retorno da posição em FII e rentabilidade de FIIs são apresentados.
    """
    analyzer = MortgageTransparencyAnalyzer()
    result = analyzer.analyze(text)

    assert result.quality_score == 1.0
    assert all(result.detected_metrics.values())
    assert all(w == 1.0 for w in result.weights.values())


def test_analyze_empty_text():
    analyzer = MortgageTransparencyAnalyzer()
    result = analyzer.analyze("")

    assert result.quality_score == 0.0
    assert not any(result.detected_metrics.values())


def test_analyze_partial_metrics():
    text = "O rating dos CRIs é AA. A inadimplência está em 1%."
    analyzer = MortgageTransparencyAnalyzer()
    result = analyzer.analyze(text)

    assert result.detected_metrics["cri_ratings"] is True
    assert result.detected_metrics["nonperforming_comments"] is True
    assert result.detected_metrics["portfolio_movements"] is False
    assert 0.1 <= result.quality_score <= 0.2


def test_version():
    analyzer = MortgageTransparencyAnalyzer()
    assert analyzer.get_version() == "1.0.0-mortgage"
