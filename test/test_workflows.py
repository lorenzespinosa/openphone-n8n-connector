"""Contract tests for the n8n workflow JSON files in openphone-n8n-connector.

The suite reads every workflows/*.json file under the repo root. The repo
root comes from the REPO environment variable and defaults to the canonical
local checkout:

    REPO=/path/to/openphone-n8n-connector python -m pytest test/

What the suite checks, following the template contract the repo states in
its own README quick start (importers replace placeholder URLs, IDs and
keys with their own values):

- every workflow file parses as JSON and carries a name and a nodes list
- every node has a type, a name and an id, with no duplicate ids or names
- every credential reference that appears also carries a name string
- connections only reference node names that exist in the same workflow
- http request nodes point at placeholders, never at a real production
  endpoint: the host is a placeholder domain such as example.com or
  webhook.test, or every instance specific value in the request is an
  explicit YOUR_... placeholder, an env reference, or a masked run of
  placeholder characters
- authorization values are placeholders or env references, never literals

The suite only reads files. It makes no network requests and writes nothing.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from urllib.parse import urlparse

import pytest

REPO = Path(os.environ.get("REPO", str(Path(__file__).resolve().parents[1]))).resolve()
WORKFLOWS_DIR = REPO / "workflows"

# Domains reserved for documentation and testing. A URL on one of these
# hosts can never reach a production system.
PLACEHOLDER_DOMAINS = (
    "example.com",
    "example.org",
    "example.net",
    "webhook.test",
    "webhook.site",
    "httpbin.org",
    "postman-echo.com",
    "mockbin.org",
    "requestbin.com",
    "local.test",
    "localhost",
    "127.0.0.1",
)
PLACEHOLDER_TLDS = (".test", ".invalid", ".example", ".localhost")

# Explicit placeholder spellings used by the workflow templates. Found in
# the URL or anywhere in the request parameters, they mark the node as a
# template whose instance specific values still need replacing.
PLACEHOLDER_MARKER_RE = re.compile(
    r"(?i)your[_/\- ]|\$env\.|placeholder|change_?me|replace_?me|x{6,}"
)

# Tokens that would identify a real account if they appeared in a URL.
REAL_ID_PATTERNS = (
    ("airtable base id", re.compile(r"app[A-Za-z0-9]{14,}")),
    ("airtable access token", re.compile(r"pat[A-Za-z0-9]{14,}")),
    ("airtable table id", re.compile(r"tbl[A-Za-z0-9]{14,}")),
    ("slack webhook path", re.compile(r"/services/[A-Za-z0-9]{6,}/[A-Za-z0-9]{6,}/[A-Za-z0-9]{6,}")),
)

TRIGGER_HINTS = ("Trigger", "webhook", "cron", "formTrigger")


def _workflow_paths() -> list[Path]:
    if not WORKFLOWS_DIR.is_dir():
        return []
    return sorted(WORKFLOWS_DIR.glob("*.json"))


WORKFLOW_PATHS = _workflow_paths()
# Sentinel keeps parametrized tests collectable when the directory is
# missing or empty; the existence test below fails the run in that case.
WORKFLOW_PARAMS = WORKFLOW_PATHS or [
    WORKFLOWS_DIR / "MISSING-no-workflow-json-files.json"
]


def _load_workflow(path: Path) -> dict:
    if not path.is_file():
        pytest.fail(
            f"workflow file not found: {path}. Set REPO to the repo root."
        )
    try:
        with path.open(encoding="utf-8") as handle:
            data = json.load(handle)
    except json.JSONDecodeError as error:
        pytest.fail(f"{path.name} is not valid JSON: {error}")
    if not isinstance(data, dict):
        pytest.fail(f"{path.name} must hold a JSON object at the top level")
    return data


def _nodes(data: dict) -> list[dict]:
    nodes = data.get("nodes", [])
    if not isinstance(nodes, list):
        pytest.fail(f"{data.get('name', '<unnamed>')} has a non-list nodes field")
    bad = [node for node in nodes if not isinstance(node, dict)]
    if bad:
        pytest.fail(f"workflow has {len(bad)} non-object node entries")
    return list(nodes)


def _http_nodes(data: dict) -> list[dict]:
    return [
        node
        for node in _nodes(data)
        if str(node.get("type", "")).endswith("httpRequest")
    ]


def _node_url(node: dict) -> str:
    url = node.get("parameters", {}).get("url", "")
    return str(url).lstrip("=").strip()


def _string_values(value) -> list[str]:
    """Collect every string inside a parameters tree."""
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        collected: list[str] = []
        for item in value.values():
            collected.extend(_string_values(item))
        return collected
    if isinstance(value, list):
        collected = []
        for item in value:
            collected.extend(_string_values(item))
        return collected
    return []


def _is_placeholder_host(host: str) -> bool:
    host = host.lower().rstrip(".")
    if host in PLACEHOLDER_DOMAINS:
        return True
    if any(host.endswith("." + domain) for domain in PLACEHOLDER_DOMAINS):
        return True
    return any(host.endswith(tld) for tld in PLACEHOLDER_TLDS)


def _http_node_is_placeholder_safe(node: dict) -> tuple[bool, str]:
    """One http node passes when it cannot reach a real account.

    Either the host is a documentation or test domain, or the request
    carries an explicit placeholder or env reference where instance
    specific values would go. A production host with real looking values
    and no markers fails.
    """
    url = _node_url(node)
    parsed = urlparse(url)
    host = (parsed.netloc.split("@")[-1].split(":")[0] or "").strip()
    if host and _is_placeholder_host(host):
        return True, f"host {host} is a placeholder domain"
    if PLACEHOLDER_MARKER_RE.search(url):
        return True, "url carries an explicit placeholder marker"
    for value in _string_values(node.get("parameters", {})):
        if PLACEHOLDER_MARKER_RE.search(value):
            return True, "request parameters carry an explicit placeholder"
    return False, f"production endpoint without any placeholder marker: {url or '<no url>'}"


def _is_uniform_run(fragment: str) -> bool:
    return len(fragment) > 0 and len(set(fragment)) == 1


def _real_id_findings(url: str) -> list[str]:
    findings: list[str] = []
    for label, pattern in REAL_ID_PATTERNS:
        for match in pattern.finditer(url):
            token = match.group(0)
            body = token
            for prefix in ("app", "pat", "tbl", "/services/"):
                if body.startswith(prefix):
                    body = body[len(prefix):]
                    break
            if _is_uniform_run(body):
                continue
            findings.append(f"{label} looks real: {token}")
    return findings


def _credential_references(node: dict) -> list[tuple[str, object]]:
    """Find every credential mapping anywhere inside a node."""
    found: list[tuple[str, object]] = []

    def walk(value) -> None:
        if isinstance(value, dict):
            for key, item in value.items():
                if "credential" in str(key).lower() and isinstance(item, (dict, str)):
                    found.append((str(key), item))
                walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)

    walk(node)
    return found


def _collect_http_cases() -> list:
    cases = []
    for path in WORKFLOW_PATHS:
        try:
            with path.open(encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(data, dict):
            continue
        for node in _http_nodes(data):
            name = str(node.get("name", "unnamed"))
            cases.append(pytest.param(path.name, name, id=f"{path.stem}:{name}"))
    # Sentinel keeps collection alive when nothing can be read; the
    # workflow files existence test fails the run in that case.
    return cases or [pytest.param(None, None, id="no-http-nodes-found")]


HTTP_CASES = _collect_http_cases()


def _find_node(data: dict, node_name: str) -> dict:
    for node in _nodes(data):
        if str(node.get("name", "")) == node_name:
            return node
    pytest.fail(f"node {node_name!r} not found while collecting http cases")


# ---------------------------------------------------------------------------
# File level structure
# ---------------------------------------------------------------------------


def test_workflow_json_files_exist():
    """The workflows directory exists and holds at least one json file."""
    assert WORKFLOWS_DIR.is_dir(), (
        f"workflows directory not found at {WORKFLOWS_DIR}. "
        "Set REPO to the openphone-n8n-connector checkout root."
    )
    assert WORKFLOW_PATHS, "no *.json files found in the workflows directory"


@pytest.mark.parametrize("path", WORKFLOW_PARAMS, ids=lambda p: p.name)
def test_every_workflow_file_is_valid_json(path: Path):
    data = _load_workflow(path)
    assert isinstance(data.get("nodes"), list), f"{path.name} has no nodes list"


@pytest.mark.parametrize("path", WORKFLOW_PARAMS, ids=lambda p: p.name)
def test_every_workflow_has_a_name(path: Path):
    data = _load_workflow(path)
    name = data.get("name")
    assert isinstance(name, str) and name.strip(), (
        f"{path.name} is missing a workflow name"
    )


# ---------------------------------------------------------------------------
# Node level structure
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("path", WORKFLOW_PARAMS, ids=lambda p: p.name)
def test_every_node_has_a_type(path: Path):
    data = _load_workflow(path)
    nodes = _nodes(data)
    assert nodes, f"{path.name} has no nodes"
    for node in nodes:
        node_type = node.get("type")
        assert isinstance(node_type, str) and node_type.strip(), (
            f"{path.name}: node {node.get('name', '<unnamed>')!r} has no type"
        )
        assert re.fullmatch(r"[\w@.\-]+\.[\w@.\-]+", node_type), (
            f"{path.name}: node {node.get('name', '<unnamed>')!r} type "
            f"{node_type!r} is not a namespaced n8n node type"
        )


@pytest.mark.parametrize("path", WORKFLOW_PARAMS, ids=lambda p: p.name)
def test_every_node_has_a_name(path: Path):
    data = _load_workflow(path)
    for node in _nodes(data):
        name = node.get("name")
        assert isinstance(name, str) and name.strip(), (
            f"{path.name}: a node is missing a name"
        )


@pytest.mark.parametrize("path", WORKFLOW_PARAMS, ids=lambda p: p.name)
def test_every_node_has_an_id(path: Path):
    data = _load_workflow(path)
    for node in _nodes(data):
        node_id = node.get("id")
        assert isinstance(node_id, (str, int)) and str(node_id).strip(), (
            f"{path.name}: node {node.get('name', '<unnamed>')!r} has no id"
        )


@pytest.mark.parametrize("path", WORKFLOW_PARAMS, ids=lambda p: p.name)
def test_no_duplicate_node_ids(path: Path):
    data = _load_workflow(path)
    ids = [str(node.get("id")) for node in _nodes(data)]
    duplicates = {node_id for node_id in ids if ids.count(node_id) > 1}
    assert not duplicates, f"{path.name} repeats node ids: {sorted(duplicates)}"


@pytest.mark.parametrize("path", WORKFLOW_PARAMS, ids=lambda p: p.name)
def test_no_duplicate_node_names(path: Path):
    data = _load_workflow(path)
    names = [str(node.get("name")) for node in _nodes(data)]
    duplicates = {name for name in names if names.count(name) > 1}
    assert not duplicates, (
        f"{path.name} repeats node names, which breaks connections: "
        f"{sorted(duplicates)}"
    )


@pytest.mark.parametrize("path", WORKFLOW_PARAMS, ids=lambda p: p.name)
def test_nodes_declare_a_type_version(path: Path):
    data = _load_workflow(path)
    for node in _nodes(data):
        version = node.get("typeVersion")
        assert isinstance(version, (int, float)), (
            f"{path.name}: node {node.get('name', '<unnamed>')!r} has no "
            "numeric typeVersion"
        )


# ---------------------------------------------------------------------------
# Credentials
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("path", WORKFLOW_PARAMS, ids=lambda p: p.name)
def test_credential_references_carry_name_strings(path: Path):
    """Every credential reference that appears has a matching name string.

    n8n exports reference credentials as mappings such as
    credentials: {httpHeaderAuth: {id: ..., name: ...}}. A reference
    without a name string cannot be resolved when the workflow is
    imported, so any reference found on a node must carry one, and the
    name must appear in the workflow document.
    """
    data = _load_workflow(path)
    problems = []
    for node in _nodes(data):
        node_label = str(node.get("name", "<unnamed>"))
        for key, reference in _credential_references(node):
            names: list[str] = []
            if isinstance(reference, dict):
                for entry in reference.values():
                    # only an explicit name string counts; other string
                    # values such as ids are not resolvable credential names
                    if isinstance(entry, dict) and isinstance(
                        entry.get("name"), str
                    ):
                        names.append(entry["name"])
                if not reference:
                    problems.append(f"{node_label}: {key} is empty")
            elif isinstance(reference, str):
                if reference.strip():
                    names.append(reference)
                else:
                    problems.append(f"{node_label}: {key} is an empty string")
            for name in names:
                if not name.strip():
                    problems.append(f"{node_label}: {key} has an empty name")
            if isinstance(reference, dict) and not names:
                problems.append(
                    f"{node_label}: {key} has no entry with a name string"
                )
    assert not problems, f"{path.name} credential reference problems: {problems}"


# ---------------------------------------------------------------------------
# Http request nodes and placeholders
# ---------------------------------------------------------------------------


def test_http_request_nodes_exist():
    """Guard against a vacuous pass: the repo must exercise http nodes."""
    total = 0
    for path in WORKFLOW_PATHS:
        data = _load_workflow(path)
        total += len(_http_nodes(data))
    assert total > 0, "no httpRequest nodes found in any workflow"


@pytest.mark.parametrize("filename,node_name", HTTP_CASES)
def test_http_nodes_use_placeholder_targets(filename, node_name):
    """Http nodes must point at placeholders, never real production data.

    A node passes when its host is a placeholder domain such as
    example.com or webhook.test, or when the request keeps an explicit
    YOUR_... placeholder or an env reference where instance specific
    values belong. Pointing at a public API host is acceptable only in
    that template form, which is the contract this repo documents.
    """
    if filename is None:
        pytest.fail("no http request nodes were found to check")
    data = _load_workflow(WORKFLOWS_DIR / filename)
    node = _find_node(data, node_name)
    safe, reason = _http_node_is_placeholder_safe(node)
    assert safe, f"{filename} node {node_name!r}: {reason}"


def _authorization_values(node: dict) -> list[str]:
    headers = (
        node.get("parameters", {})
        .get("headerParameters", {})
        .get("parameters", [])
    )
    values = []
    for header in headers:
        if not isinstance(header, dict):
            continue
        if str(header.get("name", "")).lower() == "authorization":
            values.append(str(header.get("value", "")))
    return values


@pytest.mark.parametrize("filename,node_name", HTTP_CASES)
def test_authorization_values_are_placeholder_or_env(filename, node_name):
    """Authorization headers carry placeholders or env reads, never tokens."""
    if filename is None:
        pytest.fail("no http request nodes were found to check")
    data = _load_workflow(WORKFLOWS_DIR / filename)
    node = _find_node(data, node_name)
    for value in _authorization_values(node):
        assert PLACEHOLDER_MARKER_RE.search(value), (
            f"{filename} node {node_name!r} sends an Authorization value "
            f"with no placeholder or env reference: {value!r}"
        )


@pytest.mark.parametrize("filename,node_name", HTTP_CASES)
def test_no_real_production_identifiers_in_urls(filename, node_name):
    """Urls must not embed real account ids or webhook paths."""
    if filename is None:
        pytest.fail("no http request nodes were found to check")
    data = _load_workflow(WORKFLOWS_DIR / filename)
    node = _find_node(data, node_name)
    findings = _real_id_findings(_node_url(node))
    assert not findings, f"{filename} node {node_name!r}: {findings}"


def test_placeholder_checker_flags_a_real_production_url():
    """Guard the guard: a fully real endpoint must fail the check."""
    node = {
        "name": "Synthetic real endpoint",
        "type": "n8n-nodes-base.httpRequest",
        "parameters": {
            "method": "POST",
            "url": "https://api.airtable.com/v0/appFakeBase0000000/CallLog",
            "headerParameters": {
                "parameters": [
                    {
                        "name": "Authorization",
                        "value": "Bearer patFakeToken000000000",
                    }
                ]
            },
        },
    }
    safe, _reason = _http_node_is_placeholder_safe(node)
    assert not safe, "checker accepted a production url with fake but real-looking ids"
    assert _real_id_findings(_node_url(node)), "id detector missed a real-looking token"


def test_placeholder_checker_accepts_the_template_form():
    """Guard the guard: the documented template form must pass."""
    node = {
        "name": "Synthetic template node",
        "type": "n8n-nodes-base.httpRequest",
        "parameters": {
            "method": "GET",
            "url": "https://api.openphone.com/v1/calls",
            "headerParameters": {
                "parameters": [
                    {
                        "name": "Authorization",
                        "value": "Bearer YOUR_OPENPHONE_API_KEY",
                    }
                ]
            },
        },
    }
    safe, _reason = _http_node_is_placeholder_safe(node)
    assert safe, "checker rejected the template form used across this repo"


# ---------------------------------------------------------------------------
# Connections
# ---------------------------------------------------------------------------


def _connection_endpoints(data: dict) -> list[tuple[str, str]]:
    endpoints = []
    connections = data.get("connections")
    assert isinstance(connections, dict), (
        f"{data.get('name', '<unnamed>')} has a non-object connections field"
    )
    for source, groups in connections.items():
        assert isinstance(groups, dict), (
            f"connection source {source!r} does not map to connection groups"
        )
        for outputs in groups.values():
            assert isinstance(outputs, list), (
                f"connection source {source!r} has a non-list output group"
            )
            for output in outputs:
                for connection in output or []:
                    assert isinstance(connection, dict), (
                        f"connection source {source!r} has a malformed entry"
                    )
                    endpoints.append((source, str(connection.get("node"))))
    return endpoints


@pytest.mark.parametrize("path", WORKFLOW_PARAMS, ids=lambda p: p.name)
def test_connection_sources_reference_existing_nodes(path: Path):
    data = _load_workflow(path)
    names = {str(node.get("name")) for node in _nodes(data)}
    sources = {source for source, _target in _connection_endpoints(data)}
    unknown = sorted(sources - names)
    assert not unknown, f"{path.name} connections start at unknown nodes: {unknown}"


@pytest.mark.parametrize("path", WORKFLOW_PARAMS, ids=lambda p: p.name)
def test_connection_targets_reference_existing_nodes(path: Path):
    data = _load_workflow(path)
    names = {str(node.get("name")) for node in _nodes(data)}
    targets = {target for _source, target in _connection_endpoints(data)}
    unknown = sorted(targets - names)
    assert not unknown, f"{path.name} connections point at unknown nodes: {unknown}"


# ---------------------------------------------------------------------------
# Workflow level checks
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("path", WORKFLOW_PARAMS, ids=lambda p: p.name)
def test_every_workflow_has_a_trigger(path: Path):
    data = _load_workflow(path)
    trigger_names = [
        str(node.get("name", "<unnamed>"))
        for node in _nodes(data)
        if any(hint in str(node.get("type", "")) for hint in TRIGGER_HINTS)
    ]
    assert trigger_names, (
        f"{path.name} has no trigger node; a workflow cannot start itself"
    )


@pytest.mark.parametrize("path", WORKFLOW_PARAMS, ids=lambda p: p.name)
def test_workflows_ship_inactive(path: Path):
    """Templates ship inactive; importers activate them on purpose."""
    data = _load_workflow(path)
    assert data.get("active") is False, (
        f"{path.name} must ship with active set to false"
    )
