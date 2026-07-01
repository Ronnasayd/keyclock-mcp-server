import json
from pathlib import Path

from keycloak_mcp.openapi.parser import parse_spec

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "sample_spec.json"


def load_fixture() -> dict:
    return json.loads(FIXTURE_PATH.read_text())


def test_named_operation_id_preserved():
    operations = parse_spec(load_fixture())
    get_realms = next(op for op in operations if op.operation_id == "getRealms")
    assert not get_realms.operation_id_synthesized
    assert get_realms.method == "get"
    assert get_realms.path == "/admin/realms"


def test_missing_operation_id_synthesized(caplog):
    operations = parse_spec(load_fixture())
    post_realms = next(
        op for op in operations if op.path == "/admin/realms" and op.method == "post"
    )
    assert post_realms.operation_id == "post_admin_realms"
    assert post_realms.operation_id_synthesized
    assert "synthesized" in caplog.text.lower()


def test_request_body_parsed():
    operations = parse_spec(load_fixture())
    post_realms = next(
        op for op in operations if op.path == "/admin/realms" and op.method == "post"
    )
    assert post_realms.request_body is not None
    assert post_realms.request_body.required is True
    assert post_realms.request_body.content_type == "application/json"


def test_malformed_operation_does_not_crash_parse(caplog):
    operations = parse_spec(load_fixture())
    paths = {(op.path, op.method) for op in operations}
    assert ("/admin/realms/{realm}/broken", "get") not in paths
    assert "skip" in caplog.text.lower()


def test_total_valid_operations_extracted():
    operations = parse_spec(load_fixture())
    assert len(operations) == 2
