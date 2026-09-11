"""Export the API schema without requiring a running server or database."""

import argparse
import json
from pathlib import Path

from backend.main import app


def main() -> None:
    """Write or verify the checked-in React API contract."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    target = Path("frontend/react/openapi.json")
    schema = json.dumps(app.openapi(), indent=2) + "\n"
    if args.check:
        if not target.exists() or target.read_text() != schema:
            raise SystemExit("OpenAPI drift: run python -m scripts.export_openapi and npm run api:generate in frontend/react")
    else:
        target.write_text(schema)


if __name__ == "__main__":
    main()
