#!/usr/bin/env python3

import asyncio
from rich.console import Console
from rich.panel import Panel
from pydantic_ai import Agent
from pydantic import BaseModel


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


async def main():
    """Main function that coordinates OpenAI queries."""
    console = Console()
    
    # Query OpenAI about Canadian cities
    await query_openai_for_city(console)


if __name__ == "__main__":
    asyncio.run(main())


