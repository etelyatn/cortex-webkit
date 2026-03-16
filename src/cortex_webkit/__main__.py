"""Entry point: python -m cortex_webkit or cortex-web CLI."""

import argparse
import uvicorn

from cortex_webkit.config import CortexWebConfig


def main() -> None:
    parser = argparse.ArgumentParser(description="Cortex Web Kit server")
    sub = parser.add_subparsers(dest="command")
    serve_parser = sub.add_parser("serve", help="Start the web server")
    serve_parser.add_argument("--port", type=int, default=None)
    serve_parser.add_argument("--host", type=str, default=None)
    args = parser.parse_args()

    if args.command != "serve":
        parser.print_help()
        return

    config = CortexWebConfig()
    host = args.host or config.host
    port = args.port or config.port

    uvicorn.run(
        "cortex_webkit.app:create_app",
        factory=True,
        host=host,
        port=port,
        workers=1,
        log_level="info",
    )


if __name__ == "__main__":
    main()
