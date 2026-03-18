import sys
import os

# Ensure src/ is on the path when running directly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import uvicorn
from mcp_gateway.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "mcp_gateway.app:app",
        host="0.0.0.0",
        port=settings.port,
        reload=settings.env == "development",
        log_level=settings.log_level.lower(),
    )
