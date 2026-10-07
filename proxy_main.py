from fastmcp import Client
from fastmcp.server import create_proxy


REMOTE_URL = "https://icy-maroon-bird.fastmcp.app/mcp"

remote_client = Client(
    REMOTE_URL,
    auth = "oauth",
)

mcp = create_proxy(
    remote_client,
    name = "expense tracker BRIDGE",
)


if __name__ == "__main__":
    mcp.run()
