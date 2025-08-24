"""
OpenAI and Pydantic AI integration module.
"""

from pydantic_ai import Agent
from pydantic import BaseModel
from rich.console import Console
from rich.panel import Panel


class City(BaseModel):
    """Model representing a city with its population."""
    city: str
    population: int


async def query_openai_for_city(console: Console) -> None:
    """Query OpenAI about the most populous city in Canada."""
    city_agent = Agent(
        'openai:gpt-5',
        output_type=City
    )
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
