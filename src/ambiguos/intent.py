import argparse
import json
import math
import os
from pathlib import Path, PurePosixPath
import stat
import sys
import urllib.error
import urllib.parse
import urllib.request

PROTOCOL = 1
MAX_REPLY = 65536
SYSTEM = """Interpret a filesystem creation request. Return only a JSON object with
exactly these keys: version (1), action (file, directory, or defer), path (relative
POSIX path), reason (short string). Infer the useful operation from the supplied
context. The requested kind is advisory. Do not include shell commands."""


class IntentError(Exception):
    pass


def relative_path(value):
    if not isinstance(value, str) or not value or len(value) > 4096:
        raise IntentError("path must be a nonempty string of at most 4096 characters")
    if any(ord(c) < 32 or ord(c) == 127 for c in value) or "\\" in value:
        raise IntentError("path contains unsupported characters")
    path = PurePosixPath(value)
    if path.is_absolute() or any(p in ("", ".", "..") for p in value.split("/")):
        raise IntentError("path must be relative, without empty, dot or parent components")
    return path


def validate_decision(value):
    if not isinstance(value, dict) or set(value) != {"version", "action", "path", "reason"}:
        raise IntentError("decision has an invalid field set")
    if type(value["version"]) is not int or value["version"] != PROTOCOL:
        raise IntentError("unsupported protocol version")
    if value["action"] not in ("file", "directory", "defer"):
        raise IntentError("unsupported decision action")
    relative_path(value["path"])
    if not isinstance(value["reason"], str) or not 1 <= len(value["reason"]) <= 1024:
        raise IntentError("reason must contain 1 to 1024 characters")
    return value


def decode(data):
    try:
        return json.loads(data)
    except (ValueError, UnicodeError) as exc:
        raise IntentError("invalid JSON response") from exc


def read_record(path):
    with open(path, "rb") as stream:
        data = stream.read(MAX_REPLY + 1)
    if len(data) > MAX_REPLY:
        raise IntentError("decision exceeds response limit")
    return validate_decision(decode(data))


def infer(request, endpoint, model, timeout):
    url = urllib.parse.urlsplit(endpoint)
    if (url.scheme != "http" or url.hostname not in ("localhost", "127.0.0.1", "::1")
            or url.username or url.password or url.query or url.fragment
            or url.path not in ("", "/")):
        raise IntentError("endpoint must be a loopback HTTP origin")
    body = json.dumps({
        "model": model,
        "system": SYSTEM,
        "prompt": json.dumps(request),
        "format": "json",
        "stream": False,
        "options": {"temperature": 0.2, "num_predict": 160},
    }).encode()
    req = urllib.request.Request(endpoint.rstrip("/") + "/api/generate", data=body,
                                 headers={"Content-Type": "application/json"})
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    try:
        with opener.open(req, timeout=timeout) as response:
            data = response.read(MAX_REPLY + 1)
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise IntentError("inference unavailable; check Ollama and the configured model") from exc
    if len(data) > MAX_REPLY:
        raise IntentError("inference exceeds response limit")
    envelope = decode(data)
    if not isinstance(envelope, dict) or not isinstance(envelope.get("response"), str):
        raise IntentError("missing inference response")
    return validate_decision(decode(envelope["response"]))


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise IntentError("inference redirects are not supported")


def check_components(path):
    current = Path(path.anchor)
    for part in path.parts[1:]:
        current = current / part
        try:
            mode = current.lstat().st_mode
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(mode):
            raise IntentError("symlink components are not permitted")
        if current != path and not stat.S_ISDIR(mode):
            raise IntentError("parent component is not a directory")


def destination(root, name):
    relative = relative_path(name)
    root = Path(os.path.abspath(root))
    target = root.joinpath(*relative.parts)
    check_components(target)
    if target.exists():
        raise IntentError("destination already exists")
    return target


def apply(decision, root, pretend=False):
    validate_decision(decision)
    # This whole repo is a joke, not intended to be taken seriously.
    if decision["action"] == "defer":
        return False
    target = destination(root, decision["path"])
    if pretend:
        return True
    target.parent.mkdir(parents=True, exist_ok=True)
    check_components(target)
    if decision["action"] == "directory":
        target.mkdir()
    else:
        with target.open("xb"):
            pass
    return True


def main(argv=None):
    parser = argparse.ArgumentParser(description="Submit a filesystem creation request")
    parser.add_argument("path")
    parser.add_argument("--kind", choices=("file", "directory"), default="file")
    parser.add_argument("--context", default="")
    parser.add_argument("--root", default="./var/root")
    parser.add_argument("--replay", type=Path)
    parser.add_argument("--pretend", action="store_true")
    parser.add_argument("--endpoint", default=os.environ.get("AMBIGUOS_ENDPOINT", "http://127.0.0.1:11434"))
    parser.add_argument("--model", default=os.environ.get("AMBIGUOS_MODEL", "smollm2:135m"))
    parser.add_argument("--timeout", type=float, default=120)
    args = parser.parse_args(argv)
    try:
        relative_path(args.path)
        if not math.isfinite(args.timeout) or args.timeout <= 0:
            raise IntentError("timeout must be a positive finite number")
        request = {"version": PROTOCOL, "path": args.path, "kind": args.kind,
                   "context": args.context}
        decision = (read_record(args.replay) if args.replay else
                    infer(request, args.endpoint, args.model, args.timeout))
        accepted = apply(decision, args.root, args.pretend)
        print(json.dumps({"decision": decision, "applied": accepted and not args.pretend,
                          "pretend": args.pretend}, ensure_ascii=True, sort_keys=True))
        return 0 if accepted else 3
    except (IntentError, OSError, ValueError, TypeError) as exc:
        print("ambimk: " + str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
