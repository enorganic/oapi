from __future__ import annotations

import os
from collections import deque

from gittable.download import download

PROJECT_PATH: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GIT_URL: str = "https://github.com/OAI/OpenAPI-Specification.git"


def main() -> None:
    files: list[str] = download(
        GIT_URL,
        files=("schemas/v2.*/**", "schemas/v3.*/**"),
        directory=PROJECT_PATH,
    )
    if not files:
        message: str = f"Could not download schemas from {GIT_URL}"
        raise RuntimeError(message)
    deque(map(print, files), maxlen=0)


if __name__ == "__main__":
    main()
