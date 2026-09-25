# RepoAudit MCP

An MCP server that gives an AI coding agent real tools to check Python code for problems — lint issues, security holes, and overly tangled functions — before any of it gets merged.

Built on Anthropic's official [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk), tested end-to-end with the official [MCP Inspector](https://github.com/modelcontextprotocol/inspector).

## Why this exists

[MCP](https://modelcontextprotocol.io) is quickly becoming the standard way AI apps like Claude and Cursor connect to real tools and data instead of just guessing at answers. I wanted to understand it at the protocol level — not just use someone else's MCP server, but build one myself and see exactly how a tool call travels from an AI agent, through the SDK, into real code, and back.

So instead of a toy example, I built something with an actual use case: a server that hands an AI agent the same checks a senior engineer would run before approving a pull request.

## What it does

Five tools, each backed by a real, widely-used analysis library:

| Tool | What it checks | Powered by |
|---|---|---|
| `lint_code` | Style and correctness issues | [ruff](https://docs.astral.sh/ruff/) |
| `security_scan` | Known vulnerability patterns (SQL injection, shell injection, etc.) | [bandit](https://bandit.readthedocs.io/) |
| `complexity_report` | Functions that have gotten too tangled to safely change | [radon](https://radon.readthedocs.io/) |
| `git_diff_summary` | What changed between two commits, with risk flags | [GitPython](https://gitpython.readthedocs.io/) |
| `audit_repo` | Runs everything above and returns **one combined risk score (0–100)** | — |

Every tool returns structured text an AI agent can reason about — not just a wall of output to print at a human.

## Seeing it work

Run it against a deliberately risky file and a deliberately clean one, and the score reflects it accurately:

```
$ audit_repo(path="examples/risky.py")
=== RISK SCORE: 50/100 ===
--- Security ---
>> Issue: Starting a process with a shell, possible injection detected.
   Severity: High   Confidence: High

$ audit_repo(path="examples/clean.py")
=== RISK SCORE: 0/100 ===
All checks passed.
```

## Getting started

```bash
git clone https://github.com/Aite09/repoaudit-mcp.git
cd repoaudit-mcp

python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install "mcp[cli]" ruff bandit radon GitPython
```

Run the server directly:

```bash
python3 server.py
```

Or poke at it interactively with the official Inspector:

```bash
npx @modelcontextprotocol/inspector python3 server.py
```

Try it against the sample files in `examples/` — `risky.py` has a planted security issue, `tangled.py` has deliberately nested logic, `clean.py` should come back spotless.

## Wiring it into Claude Desktop

```json
{
  "mcpServers": {
    "repoaudit": {
      "command": "python3",
      "args": ["/absolute/path/to/repoaudit-mcp/server.py"]
    }
  }
}
```

Restart Claude Desktop, then try: *"Use repoaudit to check this file before I commit it."*

## A bug worth mentioning

While building `audit_repo`, my first version of the scoring logic returned **95/100** for a 3-line file with a single issue — obviously wrong. Rather than trust a number that looked plausible, I worked the math backwards by hand and found two separate false positives: the scorer was matching the word *"Medium"* inside bandit's zero-count summary table (not an actual finding), and matching radon's *function-type* letter (`F` for "this is a function") instead of its *complexity grade* letter. Tightening both checks to match on more specific text brought the score back to the mathematically correct **50/100** — and a genuinely clean file now correctly scores **0**.

Small bug, but it's a reminder that code running without an error isn't the same as code being *correct*.

## What's next

- A `pytest` suite around the tool functions (they're plain Python functions under the decorators, directly testable)
- Deploy over `streamable-http` instead of `stdio`, so it's usable remotely, not just as a local subprocess
- Read the [contributing guide](https://github.com/modelcontextprotocol/servers/blob/main/CONTRIBUTING.md) for the official reference servers repo — a merged PR there is a stronger signal than a solo project, and the natural next step from here

## License

MIT