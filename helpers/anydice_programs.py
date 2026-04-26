#!/usr/bin/env python3
"""
Manage a local SQLite cache of AnyDice programs and their computed outputs.

Subcommands
-----------
fetch URL [URL ...]
    Extract a program's source from each URL and insert it into the database.
    Each URL must contain a hex program ID in the path (e.g. /program/1a2b or
    /program/1a2b.html).  On duplicate program text the lower program_id wins.
    URL may be http://, https://, file://, or a bare local path.

compute [--all | HEX_ID ...]
    POST each program to https://anydice.com/calculator_limited.php and store
    the JSON result in the output column.  By default only rows with no output
    are processed.  Pass --force to re-fetch existing outputs; when the new
    result differs from the stored one it is reported as "changed" and updated.

Common options: --db PATH, --debug, --delay SECONDS (compute only).

Usage::

    python anydice_programs.py [--db PATH] [--debug] fetch URL [URL ...]
    python anydice_programs.py [--db PATH] [--debug] compute [--all] [--force] [--delay N] [HEX_ID ...]
"""

import argparse
import re
import sqlite3
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

_DB_DEFAULT = Path(__file__).parent / "anydice_programs.db"
_CALCULATOR_URL = "https://anydice.com/calculator_limited.php"

_ID_RE = re.compile(r"/program/([0-9a-fA-F]+)(?:\.html)?(?:[?#]|$)")
_SRC_RE = re.compile(r'var loadedProgram = "((?:[^"\\]|\\.)*)";')


# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------


def _open_db(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS programs (
            program_id  INTEGER NOT NULL,
            program     TEXT    NOT NULL UNIQUE,
            output      TEXT
        )
        """
    )
    conn.commit()
    return conn


# ---------------------------------------------------------------------------
# Fetch helpers
# ---------------------------------------------------------------------------


def _program_id_from_url(url: str) -> int | None:
    parsed = urlparse(url)
    m = _ID_RE.search(parsed.path)
    if m is None:
        return None
    return int(m.group(1), 16)


def _fetch_html(url: str) -> str:
    # Treat bare paths as file:// URLs.
    if not urlparse(url).scheme:
        url = Path(url).resolve().as_uri()
    with urllib.request.urlopen(url) as resp:  # noqa: S310
        raw = resp.read()
    return raw.decode("utf-8", errors="replace")


def _extract_program(html: str) -> str | None:
    m = _SRC_RE.search(html)
    if m is None:
        return None
    # The captured group is the JS string literal content; json.loads decodes
    # escape sequences (\n, \\, \", etc.) exactly as JavaScript would.
    # strict=False accepts literal control characters embedded in the string.
    import json

    return json.loads(f'"{m.group(1)}"', strict=False)


def _upsert_program(conn: sqlite3.Connection, program_id: int, program: str) -> str:
    """Return 'added', 'updated' (lower ID found), or 'duplicate'."""
    row = conn.execute(
        "SELECT program_id FROM programs WHERE program = ?", (program,)
    ).fetchone()

    if row is None:
        conn.execute(
            "INSERT INTO programs (program_id, program) VALUES (?, ?)",
            (program_id, program),
        )
        conn.commit()
        return "added"

    existing_id: int = row[0]
    if program_id < existing_id:
        conn.execute(
            "UPDATE programs SET program_id = ? WHERE program = ?",
            (program_id, program),
        )
        conn.commit()
        return "updated"

    return "duplicate"


# ---------------------------------------------------------------------------
# Compute helpers
# ---------------------------------------------------------------------------


def _post_program(program: str) -> str:
    data = urllib.parse.urlencode({"program": program}).encode()
    req = urllib.request.Request(_CALCULATOR_URL, data=data, method="POST")
    with urllib.request.urlopen(req) as resp:  # noqa: S310
        return resp.read().decode("utf-8")


def _store_output(
    conn: sqlite3.Connection, program_id: int, output: str, *, force: bool
) -> tuple[str, str | None]:
    """
    Store output for the given program_id and return (status, old_output).

    status is one of 'computed', 'skipped', 'unchanged', or 'changed'.
    old_output is the previous value when status is 'changed', else None.
    'changed' means --force was set and the new result differs from the stored one.
    """
    row = conn.execute(
        "SELECT output FROM programs WHERE program_id = ?", (program_id,)
    ).fetchone()

    if row is None:
        # Shouldn't happen if the caller resolved IDs from the DB, but be safe.
        return "skipped", None

    existing_output: str | None = row[0]

    if existing_output is not None and not force:
        return "skipped", None

    if existing_output == output:
        return "unchanged", None

    conn.execute(
        "UPDATE programs SET output = ? WHERE program_id = ?",
        (output, program_id),
    )
    conn.commit()
    status = "changed" if existing_output is not None else "computed"
    return status, existing_output


# ---------------------------------------------------------------------------
# Subcommand implementations
# ---------------------------------------------------------------------------


def cmd_fetch(urls: list[str], db_path: Path, *, debug: bool) -> None:
    conn = _open_db(db_path)

    for url in urls:
        if debug:
            print(f"debug: processing {url}", file=sys.stderr)

        try:
            program_id = _program_id_from_url(url)
            if program_id is None:
                print(f"warning: no hex program ID in URL, skipping: {url}")
                continue

            html = _fetch_html(url)

            program = _extract_program(html)
            if program is None:
                print(f"warning: loadedProgram not found in page: {url}")
                continue

            status = _upsert_program(conn, program_id, program)
            hex_id = f"{program_id:x}"
            print(f"{status}: program_id={hex_id} ({url})")
        except Exception as exc:  # noqa: BLE001
            print(f"error: {type(exc).__name__}: {exc} ({url})")

    conn.close()


def cmd_compute(  # noqa: C901
    ids: list[str],
    db_path: Path,
    *,
    all_missing: bool,
    force: bool,
    delay: float,
    debug: bool,
) -> None:
    conn = _open_db(db_path)

    if ids:
        int_ids = [int(h, 16) for h in ids]
        rows = conn.execute(
            "SELECT program_id, program FROM programs WHERE program_id IN "  # noqa: S608
            f"({','.join('?' * len(int_ids))})",
            int_ids,
        ).fetchall()
        found_ids = {r[0] for r in rows}
        for h, i in zip(ids, int_ids, strict=True):
            if i not in found_ids:
                print(f"warning: program_id={h} not found in database")
    elif all_missing:
        if force:
            rows = conn.execute("SELECT program_id, program FROM programs").fetchall()
        else:
            rows = conn.execute(
                "SELECT program_id, program FROM programs WHERE output IS NULL"
            ).fetchall()
    else:
        print("error: specify HEX_ID(s) or pass --all", file=sys.stderr)
        conn.close()
        sys.exit(1)

    first = True
    for program_id, program in rows:
        hex_id = f"{program_id:x}"

        if not first and delay > 0:
            time.sleep(delay)
        first = False

        if debug:
            print(f"debug: computing program_id={hex_id}", file=sys.stderr)

        try:
            output = _post_program(program)
            status, old_output = _store_output(conn, program_id, output, force=force)
            print(f"{status}: program_id={hex_id}")
            if status == "changed":
                print(f"  old: {old_output}")
                print(f"  new: {output}")
        except Exception as exc:  # noqa: BLE001
            print(f"error: {type(exc).__name__}: {exc} (program_id={hex_id})")

    conn.close()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Manage a local SQLite cache of AnyDice programs and outputs."
    )
    parser.add_argument(
        "--db",
        metavar="PATH",
        type=Path,
        default=_DB_DEFAULT,
        help=f"SQLite database path (default: {_DB_DEFAULT})",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="print extra diagnostic info to stderr while processing",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # -- fetch ---------------------------------------------------------------
    fetch_parser = subparsers.add_parser(
        "fetch",
        help="extract program source from URLs and store in database",
    )
    fetch_parser.add_argument(
        "urls", metavar="URL", nargs="+", help="AnyDice program URL(s)"
    )

    # -- compute -------------------------------------------------------------
    compute_parser = subparsers.add_parser(
        "compute",
        help="POST programs to AnyDice and store computed outputs",
    )
    compute_parser.add_argument(
        "--all",
        dest="all_missing",
        action="store_true",
        help="process all rows with missing output (or all rows with --force)",
    )
    compute_parser.add_argument(
        "--force",
        action="store_true",
        help="re-fetch output even for rows that already have one",
    )
    compute_parser.add_argument(
        "--delay",
        metavar="SECONDS",
        type=float,
        default=0.0,
        help="pause between requests (default: 0)",
    )
    compute_parser.add_argument(
        "ids",
        metavar="HEX_ID",
        nargs="*",
        help="hex program ID(s) to compute (mutually exclusive with --all)",
    )

    args = parser.parse_args()

    if args.command == "fetch":
        cmd_fetch(args.urls, args.db, debug=args.debug)
    elif args.command == "compute":
        if args.ids and args.all_missing:
            parser.error("HEX_ID arguments and --all are mutually exclusive")
        cmd_compute(
            args.ids,
            args.db,
            all_missing=args.all_missing,
            force=args.force,
            delay=args.delay,
            debug=args.debug,
        )


if __name__ == "__main__":
    main()
