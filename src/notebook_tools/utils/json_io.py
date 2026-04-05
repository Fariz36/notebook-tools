import json
import sys
from pathlib import Path

from notebook_tools.utils.errors import DomainError


def load_json_request(args):
    if getattr(args, "stdin_json", False):
        try:
            return json.load(sys.stdin)
        except json.JSONDecodeError as exc:
            raise DomainError(
                "invalid_request", f"Invalid JSON from stdin: {exc}"
            ) from exc

    if getattr(args, "input", None):
        input_path = Path(args.input)
        try:
            return json.loads(input_path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise DomainError(
                "invalid_request", f"Input file not found: {input_path}"
            ) from exc
        except json.JSONDecodeError as exc:
            raise DomainError(
                "invalid_request", f"Invalid JSON in input file: {exc}"
            ) from exc

    return {}


def dump_json(payload, *, pretty=False):
    if pretty:
        text = json.dumps(payload, indent=2, sort_keys=False)
    else:
        text = json.dumps(payload, separators=(",", ":"), sort_keys=False)
    sys.stdout.write(text)
    sys.stdout.write("\n")
