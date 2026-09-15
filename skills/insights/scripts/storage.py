"""User-owned report storage, independent of the checkout and Codex data root."""

from datetime import datetime
import os
from pathlib import Path
import tempfile


def report_root():
    base = Path(os.environ.get("TREEFOLK_HOME") or (Path.home() / ".treefolk")).expanduser().absolute()
    # Resolve parent aliases such as macOS /var -> /private/var. Keep the
    # product directory itself unresolved so a redirected output is rejected.
    base = base.parent.resolve() / base.name
    root = base / "insights"
    for path in (base, root):
        if path.is_symlink():
            raise ValueError("report storage directory must not be a symlink: " + str(path))
    return root


def ensure_report_root():
    root = report_root()
    # Preserve existing directories and permissions. Reject symlinks at the
    # product/report boundary instead of silently redirecting output.
    for path in [*reversed(root.parents), root]:
        if path.is_symlink():
            raise ValueError("report storage directory must not be a symlink: " + str(path))
        if path.exists():
            if not path.is_dir():
                raise ValueError("report storage is not a directory: " + str(path))
        else:
            path.mkdir(mode=0o700)
    return root


def create_report_dir():
    root = ensure_report_root()
    prefix = datetime.now().astimezone().strftime("%Y-%m-%d_%H%M%S-")
    return Path(tempfile.mkdtemp(prefix=prefix, dir=root))


def new_file(path, text):
    # O_EXCL preserves existing files, including dangling symlinks.
    fd = os.open(Path(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as stream:
        stream.write(text)
