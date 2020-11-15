import os
from typing import Optional
from urllib.parse import urlparse


def is_windows_operating_system() -> bool:
    return os.name == "nt"


def coalesce_domain(url: Optional[str]) -> str:
    if url is not None and not url.startswith("http"):
        return coalesce_domain(f"http://{url}")
    return "app.terraform.io" if url is None else urlparse(url).netloc
