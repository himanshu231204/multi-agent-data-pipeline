import requests

REPO_OWNER = "harshitboots"
REPO_NAME = "multi-agent-data-pipeline"

_BASE = "https://api.github.com"
_HEADERS = {"Accept": "application/vnd.github+json"}


def _get(url: str) -> requests.Response:
    return requests.get(url, headers=_HEADERS, timeout=5)


def get_repo_stats() -> dict:
    try:
        r = _get(f"{_BASE}/repos/{REPO_OWNER}/{REPO_NAME}")
        if r.status_code == 200:
            data = r.json()
            return {"stars": data.get("stargazers_count", 0),
                    "forks": data.get("forks_count", 0)}
    except Exception:
        pass
    return {"stars": 0, "forks": 0}


def has_starred(username: str) -> bool:
    try:
        r = _get(f"{_BASE}/users/{username}/starred/{REPO_OWNER}/{REPO_NAME}")
        return r.status_code == 204
    except Exception:
        return False


def has_forked(username: str) -> bool:
    try:
        r = _get(f"{_BASE}/repos/{REPO_OWNER}/{REPO_NAME}/forks")
        if r.status_code != 200:
            return False
        forks = r.json()
        return any(f.get("owner", {}).get("login", "").lower() == username.lower()
                   for f in forks)
    except Exception:
        return False


def has_followed(username: str, target: str = "harshitboots") -> bool:
    try:
        r = _get(f"{_BASE}/users/{username}/following/{target}")
        return r.status_code == 204
    except Exception:
        return False


def validate_username(username: str) -> bool:
    try:
        r = _get(f"{_BASE}/users/{username}")
        return r.status_code == 200
    except Exception:
        return False
