"""
HackerNews integration module using Composio SDK.
"""

from composio import Composio
from rich.console import Console
from rich.table import Table
from dotenv import load_dotenv
import os


async def test_hackernews_integration(console: Console) -> None:
    """Test the HackerNews integration by enabling it and checking available actions."""
    console.print("[bold blue]Testing HackerNews Integration...[/bold blue]")
    
    load_dotenv()
    api_key = os.getenv("COMPOSIO_API_KEY", "")
    
    console.print("[yellow]Initializing Composio client...[/yellow]")
    client = Composio(api_key=api_key)
    console.print("[green]✓ Client initialized[/green]")
    
    # Get entity
    console.print("[yellow]Getting entity...[/yellow]")
    client.get_entity()
    console.print("[green]✓ Entity retrieved[/green]")
    
    # Try to get the HackerNews app
    console.print("[yellow]Getting HackerNews app...[/yellow]")
    try:
        # Get all apps and find HackerNews
        apps_obj = client.apps
        all_apps = apps_obj.get()
        
        hackernews_app = None
        for app in all_apps:
            if hasattr(app, 'key') and app.key == 'hackernews':
                hackernews_app = app
                break
        
        if hackernews_app:
            console.print(f"[green]✓ HackerNews app found: {hackernews_app.name}[/green]")
            
            # Get available actions for HackerNews
            console.print("[yellow]Getting available actions for HackerNews...[/yellow]")
            actions_obj = client.actions
            all_actions = actions_obj.get()
            
            # Filter actions for HackerNews
            hackernews_actions = []
            for action in all_actions:
                # Try different ways to identify HackerNews actions
                
                # Check if this action belongs to HackerNews
                is_hackernews = False
                action_info = {}
                
                for attr in ['app_name', 'app', 'name', 'key']:
                    if hasattr(action, attr):
                        value = getattr(action, attr)
                        action_info[attr] = value
                        if 'hackernews' in str(value).lower():
                            is_hackernews = True
                
                if is_hackernews:
                    hackernews_actions.append((action, action_info))
            
            console.print(f"[green]✓ Found {len(hackernews_actions)} available actions for HackerNews[/green]")
            
            # Display available actions in a table
            if hackernews_actions:
                table = Table(title="HackerNews Available Actions")
                table.add_column("Action Name", style="cyan")
                table.add_column("Action Info", style="green")
                
                for action, info in hackernews_actions[:10]:  # Show first 10 actions
                    action_name = str(info.get('name', action))
                    action_details = str(info)
                    table.add_row(action_name, action_details)
                
                console.print(table)
                
                if len(hackernews_actions) > 10:
                    console.print(f"[dim]... and {len(hackernews_actions) - 10} more actions[/dim]")
            else:
                # If no actions found, let's try a different approach
                console.print("[yellow]No HackerNews-specific actions found. Trying to get actions by app key...[/yellow]")
                
                # Try to get actions by filtering all actions
                potential_actions = []
                for action in all_actions[:20]:  # Check first 20 actions
                    action_str = str(action)
                    if 'hackernews' in action_str.lower():
                        potential_actions.append(action)
                
                if potential_actions:
                    console.print(f"[green]Found {len(potential_actions)} potential HackerNews actions by string matching[/green]")
                    for action in potential_actions:
                        console.print(f"  - {action}")
                else:
                    console.print("[yellow]No specific HackerNews actions found, but the app exists[/yellow]")
                    console.print("[yellow]This might mean we need to enable the integration first[/yellow]")
        else:
            console.print("[red]✗ HackerNews app not found in available apps[/red]")
            return
        
    except Exception as e:
        console.print(f"[red]✗ Error getting HackerNews app: {e}[/red]")
        console.print(f"[red]Error details: {type(e).__name__}: {str(e)}[/red]")
        return
    
    console.print("[green]✓ HackerNews integration test completed successfully[/green]")


async def get_hackernews_frontpage(console: Console) -> None:
    """Get HackerNews front page stories using Composio SDK."""
    console.print("[bold blue]Getting HackerNews front page stories...[/bold blue]")
    
    load_dotenv()
    api_key = os.getenv("COMPOSIO_API_KEY", "")
    client = Composio(api_key=api_key)

    try:
        # Using the new 0.8.8 API - tools.execute with slug and arguments
        console.print("[yellow]Using new Composio 0.8.8 API with tools.execute...[/yellow]")
        
        # Execute using the new API - no need for Action enums or entities
        result = client.tools.execute(
            slug="HACKERNEWS_GET_FRONTPAGE",
            arguments={"min_points": 40}
        )
        console.print("[green]✓ Action executed successfully with new API![/green]")        # Display the results without truncation
        console.print("[green]✓ Successfully retrieved front page data[/green]")
        
        if isinstance(result, dict):
            # Try to find stories in various possible keys
            possible_keys = ['stories', 'data', 'items', 'posts', 'results']
            stories_data = None
            
            for key in possible_keys:
                if key in result:
                    stories_data = result[key]
                    break
            
            if stories_data is None:
                # Just show the full result without truncation
                console.print(f"[yellow]Full result: {result}[/yellow]")
            else:
                # Extract and display just the titles
                if isinstance(stories_data, dict) and 'response' in stories_data and 'hits' in stories_data['response']:
                    hits = stories_data['response']['hits']
                    console.print(f"[green]Found {len(hits)} HackerNews stories:[/green]")
                    for i, story in enumerate(hits, 1):
                        title = story.get('title', 'No title')
                        points = story.get('points', 0)
                        console.print(f"[cyan]{i}. {title}[/cyan] [dim]({points} points)[/dim]")
                elif isinstance(stories_data, list):
                    console.print(f"[green]Found {len(stories_data)} items:[/green]\n")
                    
                    # Display first few stories
                    for i, story in enumerate(stories_data[:5], 1):
                        if isinstance(story, dict):
                            title = story.get('title', story.get('text', 'No title'))
                            url = story.get('url', 'No URL')
                            score = story.get('score', 0)
                            story_id = story.get('id', 'No ID')
                            console.print(f"[bold cyan]{i}. {title}[/bold cyan]")
                            console.print(f"   [dim]Score: {score} | ID: {story_id}[/dim]")
                            if url != 'No URL':
                                console.print(f"   [dim]URL: {url}[/dim]")
                            console.print()
                        else:
                            console.print(f"{i}. {story}")
                else:
                    console.print(f"[yellow]Unexpected data structure: {stories_data}[/yellow]")
        else:
            console.print(f"[yellow]Result: {result}[/yellow]")
        
    except Exception as e:
        console.print(f"[red]✗ Error getting front page: {e}[/red]")
        console.print(f"[red]Error type: {type(e).__name__}[/red]")
        console.print(f"[red]Error details: {str(e)}[/red]")
