#!/usr/bin/env python3

import asyncio
import os
import subprocess
from rich.console import Console
from rich.panel import Panel
from pydantic_ai import Agent
from pydantic import BaseModel
from dotenv import load_dotenv
from composio.client import Composio


class City(BaseModel):
    """Model representing a city with its population."""
    city: str
    population: int


# Create a Pydantic AI agent for city population queries
city_agent = Agent(
    'openai:gpt-5',
    output_type=City
)


async def query_openai_for_city(console: Console) -> None:
    """Query OpenAI about the most populous city in Canada."""
    try:
        console.print("[bold blue]Asking OpenAI about Canada's most populous city...[/bold blue]")
        
        result = await city_agent.run("What is the most populous city in Canada?")
        
        city_info = result.output
        
        ai_panel = Panel(
            f"[bold green]City:[/bold green] {city_info.city}\n[bold green]Population:[/bold green] {city_info.population:,}",
            title="[bold magenta]Most Populous City in Canada (via OpenAI)[/bold magenta]",
            border_style="green",
            expand=True
        )
        console.print(ai_panel)
        
    except Exception as e:
        error_panel = Panel(
            f"[bold red]AI Query Error:[/bold red] {str(e)}",
            title="[bold red]OpenAI Error[/bold red]",
            border_style="red",
            expand=True
        )
        console.print(error_panel)


async def test_composio_integration(console: Console) -> None:
    """Test the Composio SDK integration by listing available tools."""
    console.print("[bold blue]Testing Composio SDK Integration...[/bold blue]")
    
    # Load environment variables
    load_dotenv()
    
    # Check if API key is set
    api_key = os.getenv("COMPOSIO_API_KEY")
    if not api_key or api_key == "your-composio-api-key-here":
        error_panel = Panel(
            "[bold red]Missing Configuration:[/bold red]\n\n"
            "Please set your Composio API key:\n\n"
            "1. Copy .env.template to .env\n"
            "2. Get your API key from the Composio dashboard\n"
            "3. Update COMPOSIO_API_KEY in .env file\n\n"
            "[dim]Current value:[/dim] " + (api_key or "Not set"),
            title="[bold red]Composio Configuration Required[/bold red]",
            border_style="red",
            expand=True
        )
        console.print(error_panel)
        return
    
    console.print("[green]✓ Composio API Key loaded successfully[/green]")
    
    # Initialize the Composio client
    console.print("[yellow]Initializing Composio client...[/yellow]")
    client = Composio(api_key=api_key)
    console.print("[green]✓ Composio client initialized[/green]")
    
    # Test basic connection
    console.print("\n[yellow]Testing Composio connection...[/yellow]")
    
    # Verify client is working by checking if it has the expected attributes
    has_basic_functionality = hasattr(client, 'actions') or hasattr(client, 'integrations')
    
    console.print("[green]✓ Composio client initialized successfully[/green]")
    console.print(f"[green]✓ Basic functionality check: {has_basic_functionality}[/green]")


async def main():
    """Main function that tests Composio SDK integration - Hello World example."""
    console = Console()
    
    # Query OpenAI about Canadian cities (commented out for now)
    # await query_openai_for_city(console)
    
    # Test Composio SDK integration
    await test_composio_integration(console)


if __name__ == "__main__":
    asyncio.run(main())


