"""Artifact and evidence checks for bounded documentation tasks; no code approval."""
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re


RUNTIME_FILES = {'state.json', 'telemetry.json', '.vault_key', 'incident_summary.json'}
DEFAULT_SECTIONS = ['Overview', 'Components', 'Relationships', 'Limitations']
PATH_PATTERN = re.compile(r'(?<![\w./-])(?:[\w.-]+/)*[\w.-]+\.(?:kt|kts|java|xml|gradle|md|json|toml|properties|py|js|ts|tsx|jsx|yaml|yml|txt|sh|bat|sql|cpp|h|cs)(?![\w.-])', re.IGNORECASE)


def relative_path(value):
    if not isinstance(value, str) or not value or '\\' in value or ':' in value:
        raise ValueError('Use a relative path with forward slashes.')
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {'', '.', '..'} for part in value.split('/')):
        raise ValueError('Path must stay inside the workspace.')
    return path.as_posix()


def documentation_contract(state):
    contract = state.get('documentation_contract')
    if contract is None:
        names = set(re.findall(r'[\w./-]+\.md\b', state['task']))
        if len(names) != 1:
            raise ValueError('Documentation task must name exactly one Markdown artifact.')
        contract = {'artifact': names.pop(), 'sections': DEFAULT_SECTIONS}
    if not isinstance(contract, dict):
        raise ValueError('Invalid documentation contract.')
    artifact = relative_path(contract.get('artifact'))
    if not artifact.endswith('.md'):
        raise ValueError('Documentation artifact must be Markdown.')
    sections = contract.get('sections', DEFAULT_SECTIONS)
    if (not isinstance(sections, list) or not 2 <= len(sections) <= 8
            or any(not isinstance(s, str) or not s.strip() or len(s) > 80 for s in sections)
            or len({s.casefold() for s in sections}) != len(sections)):
        raise ValueError('Specify 2-8 distinct required section headings.')
    queries = contract.get('retrieval_queries', [state['task'][:1000]])
    if (not isinstance(queries, list) or not 1 <= len(queries) <= 4
            or any(not isinstance(q, str) or not q.strip() or len(q) > 1000 for q in queries)):
        raise ValueError('Specify 1-4 bounded retrieval queries.')
    return {'artifact': artifact, 'sections': sections, 'retrieval_queries': queries}


def project_evidence(project_id, hits):
    if not isinstance(project_id, str) or not project_id:
        raise ValueError('Documentation requires a registered project_id.')
    result = []
    seen = set()
    for hit in hits:
        if hit.get('scope') not in {'project-code', 'project-snapshot'}:
            continue
        metadata = hit.get('metadata') or {}
        if metadata.get('project_id', project_id) != project_id:
            raise ValueError('Retrieved evidence belongs to a different project.')
        source = relative_path(hit.get('source'))
        text = hit.get('text', '')
        if not isinstance(text, str) or not text.strip():
            continue
        key = (source, text[:6000])
        if key in seen:
            continue
        seen.add(key)
        result.append({'source': source, 'text': text[:6000], 'scope': hit['scope'],
                       'trust': hit.get('trust', 'project code'), 'module': hit.get('module', '')})
        if len(result) == 12:
            break
    return {'project_id': project_id, 'hits': result}


def section_bodies(content):
    headings = list(re.finditer(r'^##\s+(.+?)\s*#*\s*$', content, re.MULTILINE))
    bodies = {}
    for i, heading in enumerate(headings):
        name = heading.group(1).strip().casefold()
        if name in bodies:
            raise ValueError('Duplicate section heading: ' + name)
        end = headings[i+1].start() if i+1 < len(headings) else len(content)
        bodies[name] = content[heading.end():end].strip()
    return bodies


@dataclass
class ArtifactCheck:
    content: str
    sha256: str
    citations: list
    sections: dict


def check_documentation_content(content, contract, evidence):
    if not isinstance(content, str) or len(content.encode('utf-8')) > 50 * 1024:
        raise ValueError('Requested Markdown is missing or exceeds 50KB.')
    bodies = section_bodies(content)
    sources = {hit['source'] for hit in evidence['hits']}
    if not sources:
        raise ValueError('No project evidence is available; documentation cannot complete.')
    citations = set(PATH_PATTERN.findall(content))
    citations.discard(contract['artifact'])
    if not citations:
        raise ValueError('Cite exact retrieved source paths next to factual claims.')
    unknown = citations - sources
    if unknown:
        raise ValueError('Paths not present in retrieved evidence: ' + ', '.join(sorted(unknown)))
    for heading in contract['sections']:
        body = bodies.get(heading.casefold(), '')
        if len(body) < 20:
            raise ValueError('Missing or empty required section: ' + heading)
    return sorted(citations), bodies


def check_artifact(storage, user_id, contract, evidence):
    workspace = storage._get_user_dir(user_id)
    artifact = contract['artifact']
    target = storage.resolve_workspace_path(user_id, artifact)
    parents = {p.as_posix() for p in PurePosixPath(artifact).parents if p.as_posix() != '.'}
    count = 0
    for directory, dirs, files in os.walk(workspace, followlinks=False):
        for name in dirs + files:
            entry = Path(directory) / name
            count += 1
            if count > 128:
                raise ValueError('Workspace contains too many entries.')
            if entry.is_symlink() or getattr(entry.lstat(), 'st_file_attributes', 0) & 0x400:
                raise ValueError('Linked entries are not allowed in documentation workspaces.')
            path = entry.relative_to(workspace).as_posix()
            if name in dirs:
                if path not in parents:
                    raise ValueError('Unexpected directory: ' + path)
            elif path != artifact and path not in RUNTIME_FILES:
                raise ValueError('Unexpected file: ' + path)
    if not target.is_file() or target.stat().st_size > 50 * 1024:
        raise ValueError('Requested Markdown is missing or exceeds 50KB.')
    raw = target.read_bytes()
    content = raw.decode('utf-8')
    citations, bodies = check_documentation_content(content, contract, evidence)
    return ArtifactCheck(content, hashlib.sha256(raw).hexdigest(), citations, bodies)


def check_review(answer):
    """Require an explicit verdict and explanation; semantic review is model judgment."""
    try:
        review = json.loads(answer)
    except (TypeError, ValueError):
        raise ValueError('Reviewer must return a JSON verdict with a reason.')
    if not isinstance(review, dict) or review.get('decision') != 'APPROVE':
        reason = review.get('reason', 'Reviewer rejected the document.') if isinstance(review, dict) else 'Invalid review.'
        raise ValueError(str(reason))
    if not isinstance(review.get('reason'), str) or len(review['reason'].strip()) < 20:
        raise ValueError('Reviewer must explain coverage, factual support and remaining limitations.')
    return review
