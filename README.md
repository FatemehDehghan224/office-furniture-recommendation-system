# Office Furniture Recommender

A rule-based office furniture recommendation system. The application collects a user's requirements, filters incompatible products, scores the remaining catalog entries, and returns the closest matches. It exposes the original deterministic recommendation engine through a Django web application and REST API while keeping the legacy command-line flow available.

The scoring engine is intentionally independent from Django, the database, and the language model. This keeps the original project behavior reproducible and makes the core logic easy to test and extend.

## Features

- Deterministic `if/then` recommendation rules with score-based fallback.
- Exact-budget and budget-range requests.
- Preference matching for capacity, style, and color.
- Optional fabric and body material fields preserved in the domain model and API contract.
- Django REST API with persisted requests, ranked results, and feedback.
- Persian, responsive web interface backed by the same API.
- Optional Persian conversational adapter using an OpenAI-compatible AvalAI endpoint.
- Product catalog import command that is safe to run repeatedly.
- SQLite for local development and PostgreSQL for production.
- OpenAPI schema, Swagger UI, health check, Docker Compose, and CI checks.

## How recommendations are calculated

For every request, the engine applies the following rules in order:

1. Products for a different audience (`manager`, `employee`, or `guest`) are excluded.
2. Products with a different product type are excluded.
3. Capacity adds one point when `product.number_of_person >= request.number_of_person`.
4. With a budget range, a product inside the range adds two points; a product below the maximum but below the minimum adds one point.
5. With an exact budget, a product at or below the budget adds one point. It receives one additional point when its price is within 20% of the requested budget.
6. A matching style adds one point.
7. A matching color adds one point.

Products are sorted by descending score and then by ascending distance from the budget target. For a range, the target is the midpoint; for an exact budget, it is the requested value. The API returns the first `top_k` products (default: 5, maximum: 20).

Material fields are validated, stored, and returned, but they do not currently contribute points because that would change the original scoring behavior. They can be added to the scoring rules later under a separately tested change.

## Architecture

The request flow is:

```text
Web client or API client
        |
        v
Django serializer (validation)
        |
        v
Database query: active products for the requested audience and type
        |
        v
Domain mapping -> deterministic recommendation engine
        |
        v
Ranked results -> database history -> API response
```

The conversational endpoint is an adapter around this flow. The LLM only extracts structured requirements from Persian text; it does not select products or calculate scores. Once the state is complete, the same deterministic engine is called.

## Repository structure

```text
.
├── apps/
│   ├── products/
│   │   ├── models.py                         # Product catalog model
│   │   ├── admin.py                           # Catalog admin configuration
│   │   ├── migrations/                        # Product schema
│   │   └── management/commands/import_products.py
│   └── recommendations/
│       ├── models.py                          # Requests, results, feedback
│       ├── serializers.py                     # API input/output validation
│       ├── services.py                        # ORM orchestration
│       ├── views.py                           # REST endpoints
│       ├── urls.py                            # Versioned API routes
│       ├── chat_service.py                    # Stateless LLM adapter
│       ├── admin.py
│       ├── tests.py                           # Django/API tests
│       └── migrations/
├── config/
│   ├── settings.py                            # Environment-aware Django settings
│   ├── urls.py                                # Web, API, docs, and health routes
│   ├── asgi.py
│   └── wsgi.py
├── recommendation/
│   ├── agents/                                # Legacy CLI conversational agents
│   ├── data/sofa.json                         # Source catalog (70 products)
│   ├── models/sofa_model.py                   # Pydantic domain models/enums
│   ├── recommend/recommender.py               # Pure scoring and ranking engine
│   ├── tests/test_golden_recommender.py       # Golden behavior tests
│   ├── main.py                                # CLI entry point
│   └── utils/                                 # Loading, LLM, and CLI helpers
├── templates/recommendations/index.html       # Persian web page
├── static/recommendations/                    # Web CSS and JavaScript
├── legacy/prototype-tests/                    # Archived pre-Django prototype
├── docs/                                      # Architecture, API, and roadmap notes
├── manage.py
├── Dockerfile
├── compose.yaml
├── requirements.txt
└── .github/workflows/test.yml
```

## Requirements

- Python 3.13 or newer (the project is tested in CI with Python 3.13).
- `pip` and `venv` for a local installation.
- PostgreSQL 17 or Docker Compose when running the production-style database setup.
- An AvalAI/OpenAI-compatible API key only when using the conversational LLM features.

## Local setup

Run all commands from the repository root, the directory containing `manage.py`.

### Windows PowerShell

```powershell
python -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### Linux/macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Create an environment file if you need to customize settings or use chat:

```powershell
Copy-Item recommendation\\.env.example recommendation\\.env
```

The equivalent Linux/macOS command is:

```bash
cp recommendation/.env.example recommendation/.env
```

Never commit the real `.env` file or an API key. The file is ignored by Git.

## Environment variables

Settings load `.env` from the repository root and then `recommendation/.env`. The following variables are supported:

| Variable | Default | Purpose |
| --- | --- | --- |
| `DJANGO_SECRET_KEY` | Development-only value | Django signing key; mandatory when `DJANGO_DEBUG=false` |
| `DJANGO_DEBUG` | `true` | Enables development behavior; set to `false` for production checks |
| `DJANGO_ALLOWED_HOSTS` | `127.0.0.1,localhost` | Comma-separated allowed host names |
| `OPENAI_API_KEY` | unset | Required only by the CLI chat and `/api/v1/chat/` |
| `LLM_INPUT_MODEL` | `gpt-4o` | Model used by the API conversational adapter |
| `API_ANON_RATE` | `120/minute` | Anonymous DRF throttle rate |
| `POSTGRES_DB` | unset | If set, enables PostgreSQL instead of SQLite |
| `POSTGRES_USER` | `postgres` | PostgreSQL username |
| `POSTGRES_PASSWORD` | empty | PostgreSQL password |
| `POSTGRES_HOST` | `127.0.0.1` | PostgreSQL host |
| `POSTGRES_PORT` | `5432` | PostgreSQL port |
| `DJANGO_HSTS_SECONDS` | `31536000` | HSTS duration when production mode is enabled |

When `POSTGRES_DB` is not set, the application uses `db.sqlite3`. The SQLite file is local and ignored by Git.

## Initialize the database and catalog

For a fresh checkout, run migrations and import the catalog before starting the server:

```bash
python manage.py migrate
python manage.py import_products
```

The import command reads `recommendation/data/sofa.json`, creates or updates products by their stable `legacy_id`, and can be run repeatedly without creating duplicates. A custom catalog path can be supplied:

```bash
python manage.py import_products path/to/catalog.json
```

The current source catalog contains 70 products. If migrations are skipped, requests fail because the database tables do not exist. If the catalog is not imported, the application starts but has no candidates to rank.

## Run the application

### Django web application

```bash
python manage.py runserver
```

Open [http://127.0.0.1:8000/](http://127.0.0.1:8000/) for the Persian web interface.

Useful pages:

- `/` — recommendation form and results.
- `/admin/` — Django admin (create a superuser with `python manage.py createsuperuser`).
- `/health/` — database-aware health check.
- `/api/docs/` — interactive Swagger UI.
- `/api/schema/` — generated OpenAPI schema.

### Command-line interface

The supported CLI entry point is module-based:

```bash
python -m recommendation.main
```

The CLI starts the Persian conversational flow and therefore requires `OPENAI_API_KEY`. `python main.py` is from the old project layout and is not a supported entry point.

## REST API

All versioned endpoints are under `/api/v1/`. JSON field names and enum values follow the existing domain contract.

Recommendation input fields:

| Field | Required | Accepted values or constraints |
| --- | --- | --- |
| `person` | Yes | `manager`, `employee`, `guest` |
| `productType` | Yes | `office desk`, `office chair`, `file cabinet`, `bookshelf`, `reception counter`, `waiting area sofa` |
| `number_of_person` | Yes | Positive integer |
| `budget` | No | Non-negative integer amount in the catalog's currency (Toman) |
| `budget_min`, `budget_max` | No | Non-negative integers; send both together for a range |
| `style` | No | `modern`, `classic`, `minimal`, `industrial` |
| `color` | No | `black`, `white`, `gray`, `brown`, `cream` |
| `fabric_material` | No | `leather`, `linen`, or an empty value |
| `body_material` | No | `wood`, `aluminum`, or an empty value |
| `top_k` | No | Integer from 1 to 20; defaults to 5 |

The API currently allows anonymous access and applies the configured anonymous throttle (`API_ANON_RATE`). Authentication and per-user history isolation are planned before a public multi-user deployment.

### Create recommendations

`POST /api/v1/recommendations/`

Example request using an exact budget:

```json
{
  "person": "manager",
  "productType": "office desk",
  "number_of_person": 1,
  "budget": 15000000,
  "style": "modern",
  "color": "white",
  "body_material": "wood",
  "top_k": 1
}
```

Use `budget_min` and `budget_max` together instead of `budget` for a range. The serializer rejects incomplete ranges, a minimum greater than the maximum, and requests that provide both an exact budget and a range.

Successful responses have status `201 Created` and this shape:

```json
{
  "request_id": "20f4c0f5-4d85-4f62-9ea1-7f6d6c9a7a42",
  "count": 1,
  "recommendations": [
    {
      "rank": 1,
      "score": 4,
      "price_difference": 9500000.0,
      "product": {
        "id": 2,
        "person": "manager",
        "productType": "office desk",
        "number_of_person": 1,
        "budget": 14750000,
        "style": "modern",
        "color": "white",
        "fabric_material": "",
        "body_material": "wood"
      }
    }
  ]
}
```

The values in this example are illustrative; the exact result depends on the imported catalog.

### Other endpoints

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/api/v1/products/` | Paginated list of active products |
| `GET` | `/api/v1/products/?person=manager&productType=office%20desk&style=modern&color=white` | Product filters |
| `POST` | `/api/v1/chat/` | Convert one Persian message into structured state; when complete, also create recommendations |
| `GET` | `/api/v1/recommendation-requests/{request_id}/` | Retrieve a saved request and its ranked results |
| `POST` | `/api/v1/recommendation-requests/{request_id}/feedback/` | Create or update `was_helpful` and an optional comment |
| `GET` | `/health/` | Execute `SELECT 1` and return `{"status":"ok"}` |

The chat request accepts `message`, an optional structured `state`, and up to 20 recent `history` items. It depends on the configured LLM provider and may return `502` for an invalid model response or `503` when the provider is unavailable.

## Database models

`Product` stores the imported catalog and includes a compound index on `(audience, product_type, is_active)` for the recommendation candidate query.

`RecommendationRequest` stores the normalized input and receives a public UUID. `RecommendationResult` stores each ranked product, score, rank, and price distance. `RecommendationFeedback` is a one-to-one record attached to a request and can be updated by posting again.

Products are protected from deletion while referenced by results (`PROTECT`); request results and feedback are removed when their request is deleted (`CASCADE`).

## Frontend behavior

The page in `templates/recommendations/index.html` is a Persian, responsive interface using the static assets in `static/recommendations/`. Alongside the existing form, it offers a conversational flow that sends the current message, structured state, and up to 20 recent turns to `/api/v1/chat/`. The browser retains that state and history for the current session, fills the form from collected requirements, and renders the same deterministic recommendations as soon as the conversation is complete. The form remains available without an LLM key. The chat surface shows distinct Persian messages for an unavailable/invalid API key and an invalid model response.

## Docker Compose

The compose setup starts PostgreSQL and the Django application. The web container migrates the database, imports products, collects static files, and starts Gunicorn:

```bash
docker compose up --build
```

Open [http://127.0.0.1:8000/](http://127.0.0.1:8000/). The credentials in `compose.yaml` are for local development only and must be replaced before any real deployment. The default compose environment does not configure `OPENAI_API_KEY`, so the normal form works but the conversational endpoint is unavailable until a key is supplied.

To stop the stack:

```bash
docker compose down
```

Add `-v` only when you intentionally want to remove the local PostgreSQL volume and its data.

## Production checklist

Before deploying with `DJANGO_DEBUG=false`:

- Set a long, unique `DJANGO_SECRET_KEY`.
- Set `DJANGO_ALLOWED_HOSTS` to the real host names.
- Configure PostgreSQL through the `POSTGRES_*` variables.
- Run `python manage.py migrate` and `python manage.py import_products`.
- Run `python manage.py collectstatic --noinput`.
- Serve `config.wsgi:application` with Gunicorn behind an HTTPS reverse proxy.
- Confirm that HTTPS termination and `SECURE_SSL_REDIRECT` are configured consistently.
- Keep `.env`, database credentials, and API keys out of source control.
- Add authentication and authorization before exposing admin, history, or feedback data to untrusted users.

Production mode intentionally redirects plain HTTP to HTTPS and enables secure cookies and HSTS. Running it locally with `python manage.py runserver` over plain HTTP can therefore look like a broken application; use the default development mode for local testing.

## Testing and quality checks

Run the deterministic engine tests:

```bash
python -m unittest recommendation.tests.test_golden_recommender -v
```

Run Django, API, and integration tests:

```bash
python manage.py test recommendation.tests apps.recommendations -v 1
```

Useful checks before a commit or deployment:

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py spectacular --file schema.yaml --validate
python manage.py collectstatic --noinput
python manage.py check --deploy
```

The GitHub Actions workflow runs the migration check, Django tests, OpenAPI validation, static collection, and production deployment checks on pushes and pull requests.

## Development notes

- Keep recommendation rules in `recommendation/recommend/recommender.py` pure and framework-independent.
- Add or update golden tests before changing scoring behavior.
- Keep Django-specific orchestration in `apps/recommendations/services.py` and views/serializers in their respective modules.
- Use `import_products` for catalog changes instead of editing the database manually.
- Preserve the public API contract unless a versioned API change is intentional.
- Do not add Redis, Celery, or a separate recommendation microservice until profiling demonstrates a real need.

The archived material in `legacy/prototype-tests/` is retained for historical reference and is not part of the Django test or runtime path.

## Roadmap

The current foundation is ready for incremental product work. Planned improvements include authentication and authorization, staging deployment, load testing, and introducing background processing only when measured traffic justifies it. Any new scoring criterion should be introduced with explicit golden tests so the original recommendation behavior remains stable.
