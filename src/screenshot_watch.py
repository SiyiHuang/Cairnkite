"""Watch one local directory for images published under their final filenames."""
from collections.abc import Iterator
from contextlib import closing
import os
from pathlib import Path
import select
import stat
from time import monotonic


def visible_images(folder: Path, suffixes: set[str]) -> dict[Path, int]:
    images = {}
    for path in folder.iterdir():
        if path.name.startswith(".") or path.suffix.lower() not in suffixes:
            continue
        try:
            info = path.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISREG(info.st_mode):
            images[path] = info.st_ino
    return images


def new_images(folder: Path, suffixes: set[str], timeout: float | None = None) -> Iterator[Path]:
    """Yield newly added or atomically replaced regular image files."""
    deadline = None if timeout is None else monotonic() + timeout
    gone = select.KQ_NOTE_DELETE | select.KQ_NOTE_RENAME | select.KQ_NOTE_REVOKE
    previous = visible_images(folder, suffixes)
    handle = os.open(folder, os.O_RDONLY)
    try:
        with closing(select.kqueue()) as queue:
            notice = select.kevent(handle, filter=select.KQ_FILTER_VNODE,
                                   flags=select.KQ_EV_ADD | select.KQ_EV_CLEAR,
                                   fflags=select.KQ_NOTE_WRITE | gone)
            queue.control([notice], 0)
            while True:
                current = visible_images(folder, suffixes)
                for path, inode in sorted(current.items()):
                    if previous.get(path) != inode:
                        yield path
                previous = current
                remaining = None if deadline is None else max(0, deadline - monotonic())
                if remaining == 0:
                    return
                events = queue.control(None, 1, remaining)
                if not events:
                    return
                if events[0].fflags & gone:
                    raise OSError("The watched folder moved, was removed, or became unavailable.")
    finally:
        os.close(handle)
