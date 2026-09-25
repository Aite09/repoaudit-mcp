import subprocess
import os
import git
from mcp.server.mcpserver import MCPServer


server = MCPServer(name='repoaudit')


@server.tool()
def lint_code(path: str) -> str:
    """Checks a Python file for style and correctness issues using ruff."""
    path = path.strip()
    result = subprocess.run(['ruff', 'check', path], capture_output=True, text=True)
    return f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}\nExit code: {result.returncode}"

@server.tool()
def security_scan(path: str) -> str:
    """Checks a Python file for common security vulnerabilities using bandit."""
    path = path.strip()
    result = subprocess.run(['bandit', path], capture_output=True, text=True)
    return f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}\nExit code: {result.returncode}"

@server.tool()
def complexity_report(path: str) -> str:
    """Reports cyclomatic complexity for functions in a Python file using radon."""
    path = path.strip()
    result = subprocess.run(['radon', 'cc', path, '-s'], capture_output=True, text=True)
    return f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}\nExit code: {result.returncode}"

@server.tool()
def git_diff_summary(repo_path: str, base: str = "HEAD~1", head: str = "HEAD") -> str:
    """Summarizes what changed between two commits in a git repo."""
    repo_path = os.path.expanduser(repo_path.strip())
    repo = git.Repo(repo_path)
    diff_output = repo.git.diff(base, head, "--stat")
    return diff_output

@server.tool()
def audit_repo(path: str, repo_path: str | None = None) -> str:
    """Runs lint, security, and complexity checks (and git diff if a repo is given), then returns one combined risk score from 0-100."""
    lint_result = lint_code(path)
    security_result = security_scan(path)
    complexity_result = complexity_report(path)

    score = 0
    if "error" in lint_result.lower() or "warning" in lint_result.lower():
        score += 10
    if "Severity: High" in security_result:
        score += 40
    if "Severity: Medium" in security_result:
        score += 20
    if "- B (" in complexity_result or "- C (" in complexity_result:
        score += 10
    if "- D (" in complexity_result or "- E (" in complexity_result or "- F (" in complexity_result:
        score += 25

    diff_result = ""
    if repo_path:
        diff_result = git_diff_summary(repo_path)

    return (
        f"=== RISK SCORE: {min(score, 100)}/100 ===\n\n"
        f"--- Lint ---\n{lint_result}\n\n"
        f"--- Security ---\n{security_result}\n\n"
        f"--- Complexity ---\n{complexity_result}\n\n"
        f"--- Git Diff ---\n{diff_result}"
    )

if __name__ == "__main__":
    server.run(transport='stdio')
    