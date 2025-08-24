

import asyncio
from composio.client import Composio
from dotenv import load_dotenv
import os
from rich.console import Console
# from introspection import introspect_composio_client
# from openai_integration import query_openai_for_city


async def test_composio_integration(console: Console) -> None:
    """Test the Composio SDK integration by listing available apps."""
    console.print("[bold blue]Testing Composio SDK Integration...[/bold blue]")
    
    load_dotenv()
    
    api_key = os.getenv("COMPOSIO_API_KEY", "")
    
    console.print("[yellow]Initializing Composio client...[/yellow]")
    client = Composio(api_key=api_key)
    console.print("[green]✓ Client initialized[/green]")
    
    # console.print("[yellow]Validating API key...[/yellow]")
    # client.validate_api_key(api_key)
    # console.print("[green]✓ API Key validation passed[/green]")
    
    console.print("[yellow]Creating entity...[/yellow]")
    client.get_entity()
    console.print("[green]✓ Entity created successfully[/green]")
    
    # Get and display all available apps
    console.print("\n[bold cyan]=== Available Composio Apps ===[/bold cyan]")
    console.print("[yellow]Retrieving all available apps...[/yellow]")
    
    apps_obj = client.apps
    all_apps = apps_obj.get()
    
    console.print(f"[green]✓ Found {len(all_apps)} available apps[/green]\n")
    
    # Display all apps
    for i, app in enumerate(all_apps, 1):
        if hasattr(app, 'name') and hasattr(app, 'key'):
            console.print(f"{i:3d}. {app.name} (key: {app.key})")
        elif hasattr(app, 'name'):
            console.print(f"{i:3d}. {app.name}")
        else:
            console.print(f"{i:3d}. {app}")
    
    console.print(f"\n[green]✓ Listed all {len(all_apps)} apps successfully[/green]")


async def main():
    """Main function that tests Composio SDK integration - Hello World example."""
    console = Console()
    
    # Query OpenAI about Canadian cities (available in openai_integration module)
    # await query_openai_for_city(console)
    
    # Test Composio SDK
    await test_composio_integration(console)


if __name__ == "__main__":
    asyncio.run(main())


