# AVEVA SimCentral MCP Server

A **Model Context Protocol (MCP)** server that exposes AVEVA SimCentral simulation tools to AI applications like Claude Desktop, Cursor, and other MCP-compatible clients.

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install fastmcp>=2.0.0
```

> **Note:** AVEVA dependencies must be installed separately from the AVEVA SDK.

### 2. Run the MCP Server

```bash
# For local development (stdio transport)
python aveva_mcp_server.py

# For web-based clients (SSE transport)
python aveva_mcp_server.py sse --port 8000

# For modern clients (Streamable HTTP transport)
python aveva_mcp_server.py streamable-http --port 8000
```

### 3. Configure Claude Desktop

Add the following to your Claude Desktop configuration file. Update the paths to match your environment:

```json
{
  "mcpServers": {
    "aveva": {
      "command": "C:/Users/xxxx/AppData/Local/miniconda3/envs/xxxx/python.exe",
      "args": [
        "C:/path/to/aveva_mcp_server.py"
      ]
    }
  }
}
```
### 4. Try It on Claude Desktop

![Demo of Claude Desktop integration](./demo_claudedesktop.png)

You can see the claude agent use the tool "Aps connect" and "Sim create" for the task.

## 🤝 Contributing

Contributions are welcome! Key areas for improvement:

1. Additional AVEVA API coverage
2. Enhanced error handling
3. Performance optimizations
4. More prompt templates
5. Advanced AI integrations

## 📚 Learn More

- [Model Context Protocol Specification](https://spec.modelcontextprotocol.io/)
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [AVEVA Process Simulation Documentation](https://aveva.com)

---

**Citation:** Liang, Jingkang, Niklas Groll, and Gürkan Sin. "Large Language Model Agent for User-friendly Chemical Process Simulations." *arXiv preprint arXiv:2601.11650* (2026).