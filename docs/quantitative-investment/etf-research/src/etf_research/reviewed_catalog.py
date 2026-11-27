"""Release only the catalog changes covered by sealed notice-level review."""
from pathlib import Path

from .publication import inside, read, sha, verify_bundle

DECISION_FILE = 'reports/notice-decisions/20261127T062240Z-3bb44a30/decision.json'
DECISION_SHA256 = 'f3799afc4958c9ffa3bb7d9e7ed98358563391b49c8508fbd4da643824217859'
REVIEWED_IDS = frozenset({
    'a9b46d456168f5140d58e1bdc1254a831a8f8f630d2e9b6b804a5ca669f86155',
    '8ed81a736d731796342e10f694f534b90dc2df81e38934996711552ef33aec36',
})


def reviewed_catalog_proof(root):
    """Return the evidence paths checked before these additions may pass admission."""
    # Import here because the review packet reconstructs the frozen catalog via admission.
    from .notice_workflow import validate_decision, validate_packet

    decision_file = inside(root, DECISION_FILE)
    verify_bundle(decision_file.parent)
    if sha(decision_file) != DECISION_SHA256:
        raise ValueError('Released catalog decision fingerprint differs')
    record = read(decision_file)
    folder = inside(root, record['packet_folder'])
    verify_bundle(folder)
    packet_file = folder / 'packet.json'
    if sha(packet_file) != record['packet_file_sha256']:
        raise ValueError('Released catalog packet fingerprint differs')
    packet = read(packet_file)
    validate_packet(root, packet)
    reviews = validate_decision(root, packet, record['decision'])
    if ({r['change_id'] for r in reviews} != REVIEWED_IDS
            or any(r['conclusion'] != 'no_account_effect' for r in reviews)):
        raise ValueError('Released notices require a matching no-account-effect decision')
    requests = {r['change_id']: r for r in read(folder / 'evidence_requests.json')}
    for item in packet['changes']:
        request = requests[item['change_id']]
        response = folder / (request['name'] + '.body')
        if (item['kind'] != 'added' or item['symbol'] != '510300'
                or request['url'] != item['official_url'] or request['final_url'] != request['url']
                or request['status'] != 200 or request.get('error') or request['curl_exit']
                or not response.read_bytes().startswith(b'%PDF-') or sha(response) != request['sha256']
                or not any(e['sha256'] == request['sha256'] and inside(root,e['path']) == response
                           for r in reviews if r['change_id'] == item['change_id'] for e in r['evidence'])):
            raise ValueError('Released notice has no matching official PDF evidence')
    manifests = (decision_file.parent / 'manifest.json', folder / 'manifest.json')
    paths = {p for m in manifests for p in (m, *(m.parent / name for name in read(m)))}
    paths.update(inside(root, e['path']) for r in reviews for e in r['evidence'])
    return tuple(sorted(paths))


def accepted_catalog_changes(root, changes):
    """Unknown or revised catalog entries retain the original fail-closed behavior."""
    reviewed = [change['change_id'] for change in changes if change['change_id'] in REVIEWED_IDS]
    if reviewed:
        reviewed_catalog_proof(Path(root))
    return reviewed
