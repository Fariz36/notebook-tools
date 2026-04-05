import hashlib
import json


def stable_hash(value):
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha1(encoded).hexdigest()[:12]


def source_revision(source):
    return stable_hash({"source": source})


def output_revision(outputs):
    return stable_hash({"outputs": outputs})
