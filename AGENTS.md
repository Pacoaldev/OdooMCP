# AGENTS.md — OdooMCP

## Entorno de desarrollo local

Odoo 19 corre en Docker (`docker-compose.yml` + `Dockerfile.odoo`).

```bash
docker-compose up -d     # arrancar (BD y addons persisten)
docker-compose down      # parar
curl -s http://localhost:8069/mcp/health
```

Variables en `.env`: `ODOO_URL`, `ODOO_DB`, `ODOO_USER`, `ODOO_PASSWORD`, `ODOO_API_KEY`.

Tests contra Odoo real: `uv run pytest -m "yolo or mcp"` (exportar antes las `ODOO_*`; pytest no lee `.env`).

## Terminología Odoo (importante al traducir preguntas del usuario a modelos)

En español "empresa" es ambigua. Resolver siempre así:

| El usuario dice | Modelo / filtro |
| --- | --- |
| "empresa", "cliente", "proveedor", "partner" | `res.partner` con `is_company = true` |
| "compañía", "razón social" | `res.company` (la sociedad del propio ERP) |
| "persona", "contacto", "individuo" | `res.partner` con `is_company = false` |
| "contacto" (sin matiz) | `res.partner` (ambos tipos) |

- Para contar "empresas" usa `aggregate_records(model="res.partner", groupby=["is_company"])`, **no** `res.company`.
- Ante ambigüedad, responde con ambos números y di cuál es cuál.

## Restricciones MCP actuales

- `res.partner`: read ✅, write ✅, create ❌, unlink ❌
- `res.company`: permisos completos
- `res.users`: **no expuesto** (los tests exigen que la lectura sea denegada)
- `res.country`: no expuesto

Si una tool devuelve `Access denied: Operation 'X' not allowed on model 'Y'`, es la configuración de `Settings > MCP Server > MCP Models` en Odoo, no un bug del MCP.