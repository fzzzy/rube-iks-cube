

import asyncio
from rich.console import Console
from hackernews_integration import get_hackernews_frontpage


async def main():
    """Main function to test Composio integrations."""
    console = Console()
    
    console.print("[bold green]Testing Composio SDK Integration...[/bold green]")
        
    # Try to get HackerNews front page
    await get_hackernews_frontpage(console)


if __name__ == "__main__":
    asyncio.run(main())


