"""``blog-editor`` — run the editor, or rebuild the blog from the command line."""

from __future__ import annotations

import argparse
import sys
import threading
import webbrowser
from pathlib import Path

from .site import Site, find_site_root


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="blog-editor", description=__doc__)
    ap.add_argument("--site", type=Path, help="the site folder (default: the repo this tool is in)")
    sub = ap.add_subparsers(dest="command")
    serve = sub.add_parser("serve", help="run the editor in the browser (the default)")
    serve.add_argument("--port", type=int, default=8765)
    serve.add_argument("--no-browser", action="store_true", help="don't open a browser tab")
    sub.add_parser("build", help="rebuild every published post, the index, feed and sitemap "
                                 "(after changing a template, say)")
    args = ap.parse_args(argv)

    try:
        root = find_site_root(args.site.resolve()) if args.site else find_site_root(Path(__file__).resolve(), Path.cwd())
    except FileNotFoundError as e:
        print(f"blog-editor: {e}", file=sys.stderr)
        return 2
    site = Site(root)

    if args.command == "build":
        report = site.build()
        for path in report.changed:
            print(f"  wrote {path}")
        for e in report.errors:
            print(f"error: {e}", file=sys.stderr)
        if report.check:
            print(report.check)
        if not report.changed and not report.errors:
            print("nothing changed")
        return 1 if report.errors or report.check_ok is False else 0

    from .server import create_app

    port = getattr(args, "port", 8765)
    url = f"http://127.0.0.1:{port}/_editor/"
    print(f"Hexmonger blog editor for {root}\n  {url}\n(Ctrl+C to stop)")
    if not getattr(args, "no_browser", False):
        threading.Timer(0.8, webbrowser.open, [url]).start()
    create_app(site).run(host="127.0.0.1", port=port, debug=False, threaded=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
