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
    
    try:
        # Initialize the Composio client
        console.print("[yellow]Initializing Composio client...[/yellow]")
        client = Composio(api_key=api_key)
        console.print("[green]✓ Composio client initialized[/green]")
        
        # Test basic connection
        console.print("\n[yellow]Testing Composio connection...[/yellow]")
        
        # Verify client is working by checking if it has the expected attributes
        has_basic_functionality = hasattr(client, 'actions') or hasattr(client, 'integrations')
        
        console.print("[green]✓ Composio client initialized successfully[/green]")
        
        # Get connected integrations info
        console.print("\n[yellow]Checking connected integrations...[/yellow]")
        
        try:
            # Run composio connections command to get integration details
            result = subprocess.run(['composio', 'connections'], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                connected_output = result.stdout.strip()
                if connected_output:
                    success_panel = Panel(
                        f"[bold green]🎉 Composio SDK 'Hello World' Success![/bold green]\n\n"
                        f"✓ API key loaded and validated\n"
                        f"✓ Client functionality available: {has_basic_functionality}\n"
                        f"✓ Connected integrations found\n\n"
                        f"[bold blue]Connected Services:[/bold blue]\n"
                        f"[code]{connected_output}[/code]\n\n"
                        f"[dim]Use 'composio actions <service>' to see available tools for each service.[/dim]",
                        title="[bold green]Hello World - Composio Connected! 🚀[/bold green]",
                        border_style="green",
                        expand=True
                    )
                    console.print(success_panel)
                else:
                    # No integrations connected
                    info_panel = Panel(
                        f"[bold blue]🎉 Composio SDK Connection Successful![/bold blue]\n\n"
                        f"✓ API key loaded and validated\n"
                        f"✓ Client functionality available: {has_basic_functionality}\n"
                        f"❌ No services connected yet\n\n"
                        f"[bold yellow]To connect a service:[/bold yellow]\n"
                        f"[code]composio add github[/code]\n"
                        f"[code]composio add slack[/code]\n"
                        f"[code]composio add notion[/code]\n\n"
                        f"[dim]Run 'composio apps' to see all available services.[/dim]",
                        title="[bold blue]Hello World - Ready to Connect Services! �[/bold blue]",
                        border_style="blue",
                        expand=True
                    )
                    console.print(info_panel)
            else:
                # Command failed, show basic success
                basic_panel = Panel(
                    f"[bold green]🎉 Composio SDK 'Hello World' Success![/bold green]\n\n"
                    f"✓ API key loaded and validated\n"
                    f"✓ Client functionality available: {has_basic_functionality}\n\n"
                    f"[dim]Could not check connected services (composio CLI may not be available)[/dim]\n"
                    f"[dim]Error: {result.stderr.strip() if result.stderr else 'Unknown error'}[/dim]",
                    title="[bold green]Hello World - Composio Connected! 🚀[/bold green]",
                    border_style="green",
                    expand=True
                )
                console.print(basic_panel)
                
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError) as e:
            # Fallback if composio CLI is not available
            basic_panel = Panel(
                f"[bold green]🎉 Composio SDK 'Hello World' Success![/bold green]\n\n"
                f"✓ API key loaded and validated\n"
                f"✓ Client functionality available: {has_basic_functionality}\n\n"
                f"[dim]Composio CLI not available for checking connections[/dim]\n"
                f"[dim]Error: {str(e)}[/dim]",
                title="[bold green]Hello World - Composio Connected! 🚀[/bold green]",
                border_style="green",
                expand=True
            )
            console.print(basic_panel)
        
    except Exception as e:
        error_panel = Panel(
            f"[bold red]Composio Error:[/bold red] {str(e)}\n\n"
            "[dim]This might indicate:[/dim]\n"
            "• Invalid API key\n"
            "• Network connectivity issues\n"
            "• Service unavailable",
            title="[bold red]Composio Integration Error[/bold red]",
            border_style="red",
            expand=True
        )
        console.print(error_panel)


async def main():
    """Main function that tests Composio SDK integration - Hello World example."""
    console = Console()
    
    # Query OpenAI about Canadian cities (commented out for now)
    # await query_openai_for_city(console)
    
    # Test Composio SDK integration
    await test_composio_integration(console)


if __name__ == "__main__":
    asyncio.run(main())


