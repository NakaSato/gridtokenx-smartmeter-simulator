## Plan: Redesign Project Structure and Template

Restructure the flat Python project into a modular, scalable layout following best practices (e.g., PEP 518/621), separating code, tests, docs, and assets. Create reusable templates for meters, configs, and reports to standardize additions. This improves maintainability, testing, and deployment for the Smart Meter Simulator's complex features like P2P trading and multi-output channels.

### Steps
1. Review current flat structure in root and categorize files into modules (e.g., core simulation, services, utils).
2. Design new layout: `src/smart_meter_simulator/` for package, `tests/` for pytest, `docs/` for Sphinx, `scripts/` for deployment.
3. Create templates: `templates/meter_template.py` for new meter types, `templates/config_template.yaml` for env configs, `templates/report_template.md` for analytics.
4. Update `pyproject.toml` for new paths and add build scripts for packaging.
5. Document migration guide in `docs/migration.md` with file moves and import updates.

### Further Considerations
1. Adopt specific structure? Option A: Standard Python (src-layout) / Option B: Django-inspired (apps/) / Option C: Custom modular.
2. Include CI/CD templates? Yes for GitHub Actions / No, keep minimal.
3. Preserve existing features? Ensure WebSocket, FastAPI, and multi-outputs remain intact.
