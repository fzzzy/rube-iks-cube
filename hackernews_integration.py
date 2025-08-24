"""
HackerNews integration module using Composio SDK.
"""

from composio import Composio
from rich.console import Console
from dotenv import load_dotenv
import os


async def get_hackernews_frontpage(console: Console) -> None:
    """Get HackerNews front page stories using Composio SDK."""
    console.print("[bold blue]Getting HackerNews front page stories...[/bold blue]")
    
    load_dotenv()
    api_key = os.getenv("COMPOSIO_API_KEY", "")
    client: Composio = Composio(api_key=api_key)

    result = client.tools.execute(
        slug="HACKERNEWS_GET_FRONTPAGE",
        arguments={"min_points": 40}
    )
    
    # We know the structure: result['data']['response']['hits']
    hits = result['data']['response']['hits']
    console.print(f"[green]Found {len(hits)} HackerNews stories:[/green]")
    
    for i, story in enumerate(hits, 1):
        title = story['title']
        points = story['points']
        console.print(f"{i}. {title} [dim]({points} points)[/dim]")
