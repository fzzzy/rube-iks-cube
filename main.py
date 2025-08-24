

import asyncio
from rich.console import Console
#from introspection import introspect_composio_client
from hackernews_integration import get_hackernews_frontpage
# from openai_integration import query_openai_for_city


async def main():
    """Main function to test Composio integrations."""
    console = Console()
    
    console.print("[bold green]Testing Composio SDK Integration...[/bold green]")
        
    # Try to get HackerNews front page
    await get_hackernews_frontpage(console)


if __name__ == "__main__":
    asyncio.run(main())


