from fastmcp.server import create_proxy


REMOTE_URL = "https://icy-maroon-bird.fastmcp.app/mcp"

mcp = create_proxy(
    REMOTE_URL,
    name = "expense tracker BRIDGE",
)


if __name__ == "__main__":
    mcp.run()
