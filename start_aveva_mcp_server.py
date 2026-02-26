#!/usr/bin/env python3
"""
AVEVA SimCentral MCP Server Launcher

This is the entry point for the compiled MCP server.
Run this script to start the server with your preferred transport.

Usage:
    python start_aveva_mcp_server.py              # Default: stdio transport
    python start_aveva_mcp_server.py sse          # SSE transport on port 8000
    python start_aveva_mcp_server.py http         # Streamable HTTP on port 8000
    python start_aveva_mcp_server.py sse --port 9000   # Custom port

Transport options:
    stdio  - Standard I/O (default, for Claude Desktop/Cursor)
    sse    - Server-Sent Events (for web clients)
    http   - Streamable HTTP (for modern clients)
"""

import argparse
import sys
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("aveva_mcp_launcher")


def main():
    parser = argparse.ArgumentParser(
        description="AVEVA SimCentral MCP Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        "transport",
        nargs="?",
        default="stdio",
        choices=["stdio", "sse", "http"],
        help="Transport protocol: stdio (default), sse, or http"
    )
    parser.add_argument(
        "--host",
        default="localhost",
        help="Host address for sse/http transports (default: localhost)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port for sse/http transports (default: 8000)"
    )
    
    args = parser.parse_args()
    
    # Map 'http' shorthand to 'streamable-http'
    transport = "streamable-http" if args.transport == "http" else args.transport
    
    logger.info(f"Starting AVEVA SimCentral MCP Server")
    logger.info(f"Transport: {transport}")
    if transport != "stdio":
        logger.info(f"Endpoint: {args.host}:{args.port}")
    
    # Import the compiled MCP server module
    try:
        from aveva_mcp_server import mcp
    except ImportError as e:
        logger.error(f"Failed to import aveva_mcp_server: {e}")
        logger.error("Make sure you have built the project with: python setup.py build_ext --inplace")
        sys.exit(1)
    
    # Run the server with selected transport
    if transport == "stdio":
        mcp.run(transport="stdio")
    elif transport == "sse":
        mcp.run(transport="sse", host=args.host, port=args.port)
    elif transport == "streamable-http":
        mcp.run(transport="streamable-http", host=args.host, port=args.port)


if __name__ == "__main__":
    main()
