"""
Convenience launcher for the LUNA-AI Ground Control API server.

Usage:
    python run_server.py              # development mode (auto-reload)
    python run_server.py --port 9000  # custom port
    python run_server.py --no-reload  # production-like
"""

import argparse
import sys


def main() -> None:
    parser = argparse.ArgumentParser(description="Start the LUNA-AI Ground Control API")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--no-reload", action="store_true")
    args = parser.parse_args()

    try:
        import uvicorn
    except ImportError:
        print("uvicorn not installed. Run: pip install fastapi uvicorn", file=sys.stderr)
        sys.exit(1)

    uvicorn.run(
        "apps.ground_control.api.main:app",
        host=args.host,
        port=args.port,
        reload=not args.no_reload,
    )


if __name__ == "__main__":
    main()
