"""Manual re-fetch of the vendored Keycloak Admin REST API OpenAPI spec (FR-9)."""

import argparse
import difflib
import sys
import urllib.request
from pathlib import Path

SPEC_URL = "https://www.keycloak.org/docs-api/latest/rest-api/openapi.json"
VENDORED_PATH = (
    Path(__file__).resolve().parent.parent / "spec" / "keycloak-openapi.json"
)


def fetch_spec(url: str = SPEC_URL) -> str:
    with urllib.request.urlopen(url) as response:
        return response.read().decode("utf-8")


def sync(
    dry_run: bool, vendored_path: Path = VENDORED_PATH, url: str = SPEC_URL
) -> str:
    remote_text = fetch_spec(url)
    current_text = vendored_path.read_text() if vendored_path.exists() else ""

    if dry_run:
        diff = "".join(
            difflib.unified_diff(
                current_text.splitlines(keepends=True),
                remote_text.splitlines(keepends=True),
                fromfile=str(vendored_path),
                tofile="remote",
            )
        )
        return diff or "No differences.\n"

    vendored_path.write_text(remote_text)
    return f"Updated {vendored_path}\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run", action="store_true", help="show diff without writing"
    )
    args = parser.parse_args()

    output = sync(dry_run=args.dry_run)
    sys.stdout.write(output)


if __name__ == "__main__":
    main()
