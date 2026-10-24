"""Final local entry point for the Market Brief API.

Usage:
    python run_market_agent.py

The API itself remains in market_agent.py so the PRD's single-source runtime
architecture is preserved. This wrapper keeps launch configuration explicit and
uses one worker, as required for the prototype's in-process limits.
"""

from __future__ import annotations

import os

import uvicorn


if __name__ == "__main__":
    uvicorn.run(
        "market_agent:app",
        host=os.getenv("MARKET_AGENT_HOST", "127.0.0.1"),
        port=int(os.getenv("MARKET_AGENT_PORT", "8000")),
        workers=1,
        log_level=os.getenv("LOG_LEVEL", "info").lower(),
    )
