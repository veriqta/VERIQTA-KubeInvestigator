import re

from fastapi import HTTPException

from .schemas import ToolArgs


class Policy:
    def __init__(self, settings):
        self.s = settings

    def namespace(self, namespace):
        if namespace not in self.s.namespaces:
            raise HTTPException(403, "Namespace is not authorised by KI_NAMESPACES")

    def tool(self, args: ToolArgs):
        self.namespace(args.namespace)
        if args.resource == "logs" and (not self.s.logs or not args.name or not args.container):
            raise ValueError("Log collection is disabled or pod/container is missing")


PATTERNS = [
    (
        r"(?s)-----BEGIN (?:[A-Z]+ )?PRIVATE KEY-----.*?-----END (?:[A-Z]+ )?PRIVATE KEY-----",
        "[PRIVATE KEY REDACTED]",
    ),
    (
        r"(?im)^(\s*(?:password|token|secret|api[_-]?key)\s*:\s*[|>][-+]?\s*\n)(?:[ \t]+[^\n]*(?:\n|$))+",
        r"\1  [REDACTED]\n",
    ),
    (
        r"(?is)((?:password|passwd|token|api[_-]?key|secret)\s*[:=]\s*)(['\"])(.*?)\2",
        r"\1[REDACTED]",
    ),
    (
        r"(?i)\b(?:postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis|amqps?)://[^\s]+",
        "[CONNECTION STRING REDACTED]",
    ),
    (r"(?i)(bearer\s+)[\w.\-]+", r"\1[REDACTED]"),
    (
        r"(?i)((?:password|passwd|token|api[_-]?key|secret|authorization)\s*[:=]\s*)[^\s,;]+",
        r"\1[REDACTED]",
    ),
    (r"sk-[a-zA-Z0-9_-]{12,}", "[REDACTED]"),
    (r"https?://[^\s]+", "[URL REDACTED]"),
]


def redact(value):
    if isinstance(value, dict):
        return {
            str(k): "[REDACTED]"
            if re.search(r"(?i)(password|passwd|token|api[_-]?key|secret|authorization)", str(k))
            else redact(v)
            for k, v in value.items()
        }
    if isinstance(value, list):
        return [redact(v) for v in value]
    if not isinstance(value, str):
        return value
    for pattern, replacement in PATTERNS:
        value = re.sub(pattern, replacement, value)
    return value
