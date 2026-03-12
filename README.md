# Spock — FII Transparency Analysis API

Spock analyzes the transparency of Brazilian FIIs (Fundos de Investimento Imobiliário) by collecting monthly management reports, extracting their content, and scoring transparency quality using heuristic metrics.

## Architecture

Spock uses a **modular event-driven architecture** with three top-level packages:

```
src/
├── main.py                    # FastAPI app entry — registers modules
├── shared/                    # Code used by all modules
│   ├── core/                  # Base Entity, UseCase, pagination
│   ├── domain/                # Entities, repository interfaces, shared use cases
│   ├── errors/                # ResourceNotFoundError, DuplicateJobError
│   ├── events/                # Event bus, domain events, analyzer registry
│   ├── infra/                 # Adapters, persistence, queue, auth, env
│   └── workers/               # Celery app + report analysis task
├── equity/                    # Equity REIT (tijolo) module
│   ├── analyzer.py            # 10 equity-specific metrics
│   ├── content_validator.py   # Fato Relevante rejection
│   ├── routes.py              # /equity/* endpoints
│   ├── dependencies.py        # FastAPI DI wiring
│   ├── usecases/              # Discover + Submit for equity
│   └── module.py              # register_equity_module()
└── mortgage/                  # Mortgage REIT (papel/agro) module
    ├── analyzer.py            # 15 mortgage-specific metrics
    ├── content_validator.py   # Mortgage document validation
    ├── routes.py              # /mortgage/* endpoints
    ├── dependencies.py        # FastAPI DI wiring
    ├── usecases/              # Discover + Submit for mortgage
    └── module.py              # register_mortgage_module()
```

Modules are **totally decoupled** — anything used by more than one module lives in `shared/`.

## Event-Driven Flow

```
[API Request] → [Submit Use Case] → [Celery Queue]
                                         │
                                    ┌────┴────┐
                                    │  Worker  │
                                    └────┬────┘
                                         │
                    ┌────────────────────┤
                    ▼                    ▼
            report.submitted    report.downloaded
                    │                    │
                    ▼                    ▼
            report.extracted    report.analyzed
                                         │
                                         ▼
                                   report.scored
```

The **EventBus** is an in-process pub/sub system. Each module registers its analyzer and content validator at startup via the **Analyzer Registry**.

The Celery worker reads `fundType` from the job payload and dispatches to the correct analyzer:

```python
analyzer = get_analyzer(fund_type)   # "equity" → EquityTransparencyAnalyzer
validator = get_content_validator(fund_type)  # "equity" → EquityContentValidator
```

## Equity Metrics (10)

| Metric | Keywords |
|--------|----------|
| vacancia_fisica | vacância física, taxa de vacância |
| vacancia_financeira | vacância financeira |
| walt | walt, prazo médio dos contratos |
| inquilinos | inquilinos, locatários, concentração |
| ativos_imoveis | carteira, portfólio, imóveis, ativos |
| inadimplencia | inadimplência, inadimplencia |
| cap_rate | cap rate, capitalização |
| pipeline | pipeline, aquisição, desinvestimento |
| divida_alavancagem | dívida, endividamento, alavancagem, amortização |
| comentario_gerencial | perspectiva, comentário, análise gerencial |

**Score** = detected_count / 10

## Mortgage Metrics (15)

| Metric | Keywords |
|--------|----------|
| cri_ratings | rating, classificação de risco, operações de cri |
| portfolio_movements | movimentação da carteira, aquisição de cri, venda de cri |
| stratified_dre | dre, demonstração de resultado, receitas, despesas, não recorrente |
| accumulated_periods | acumulado, 12 meses, year to date, últimos 12 |
| cost_of_leverage | custo de alavancagem, custo da dívida, cdi +, ipca + |
| fii_book | book de fiis, posição em fiis, cotas de fii, preço médio |
| sector_diversification | diversificação setorial, securitizadora, concentração por setor |
| accumulated_reserves | reserva acumulada, resultado acumulado, reserva de contingência |
| pdd_cris | pdd, provisão para devedores duvidosos, inadimplência de cri |
| dividend_guidance | distribuição de rendimento, dividendo, guidance, projeção de dividendo |
| nonperforming_comments | inadimplência, reestruturação, renegociação, default, não performado |
| grace_period | carência, período de carência, carência de juros, carência de amortização |
| risk_exposure | pulverizado, concentrado, exposição ao risco, granular |
| subordination | subordinação, sênior, mezanino, cota subordinada |
| fii_position_return | retorno da posição em fii, rentabilidade de fiis, gráfico de retorno |

**Score** = detected_count / 15

## API Endpoints

All endpoints require `x-api-key` header.

### Equity (`/equity`)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/equity/funds/{ticker}/discover` | Discover and submit equity fund reports |
| POST | `/equity/reports/analyze` | Submit a single equity report for analysis |
| GET | `/equity/funds/{ticker}/transparency` | Get latest transparency score |
| GET | `/equity/funds/{ticker}/transparency/history` | Get score history (paginated) |
| GET | `/equity/reports/{report_id}` | Get analysis result for a report |
| POST | `/equity/reports/reprocess` | Reprocess a failed report |
| GET | `/equity/reports/jobs/{job_id}` | Get processing job status |

### Mortgage (`/mortgage`)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/mortgage/funds/{ticker}/discover` | Discover and submit mortgage fund reports |
| POST | `/mortgage/reports/analyze` | Submit a single mortgage report for analysis |
| GET | `/mortgage/funds/{ticker}/transparency` | Get latest transparency score |
| GET | `/mortgage/funds/{ticker}/transparency/history` | Get score history (paginated) |
| GET | `/mortgage/reports/{report_id}` | Get analysis result for a report |
| POST | `/mortgage/reports/reprocess` | Reprocess a failed report |
| GET | `/mortgage/reports/jobs/{job_id}` | Get processing job status |

### Shared

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check (DB + Redis) |

## How to Add a New Fund Type Module

1. Create `src/<module_name>/` with:
   - `analyzer.py` — implement `TransparencyAnalyzer` with your metrics
   - `content_validator.py` — implement `ContentValidator` for document rejection
   - `usecases/` — `discover_<type>_reports.py` and `submit_<type>_analysis.py`
   - `dependencies.py` — FastAPI DI wiring
   - `routes.py` — API routes with `/<module_name>` prefix
   - `module.py` — `register_<type>_module(app, event_bus)` function

2. In `module.py`, register your analyzer and validator:
   ```python
   register_analyzer("my_type", MyAnalyzer())
   register_content_validator("my_type", MyContentValidator())
   ```

3. In `src/main.py`, add:
   ```python
   from src.<module_name>.module import register_<type>_module
   register_<type>_module(app, event_bus)
   ```

4. Create an alembic migration if schema changes are needed.

## Tech Stack

- **Python 3.12** + **FastAPI** (async REST API)
- **SQLAlchemy 2** (async ORM) + **PostgreSQL 16**
- **Celery 5** + **Redis 7** (task queue)
- **PyMuPDF** (PDF text extraction)
- **Alembic** (database migrations)
- **Pydantic v2** (validation + settings)
- **Sentry** (error tracking)

## Setup

```bash
# Install dependencies
pip install -e ".[dev]"

# Configure environment
cp .env.example .env  # Edit with your DB/Redis credentials

# Run migrations
alembic upgrade head

# Start API server
python -m src.main

# Start Celery worker (separate terminal)
celery -A src.shared.workers.celery_app worker --loglevel=info -Q report-analysis
```

## Database

The `funds` table has a `fund_type` column (`VARCHAR NOT NULL DEFAULT 'equity'`). All existing funds default to equity. The `report_analyses` table stores metrics as JSONB, so no schema change is needed for different metric sets.

### Migration

```bash
alembic upgrade head  # Applies 001_add_fund_type migration
```

## Testing

```bash
pytest tests/ -v
```

## Deploy

See `render.yaml` for Render deployment configuration. The app runs as two services:
- **Web**: FastAPI server (`src.main:app`)
- **Worker**: Celery worker processing report analysis tasks
