#!/usr/bin/env python3

import asyncio
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from pydantic_ai import Agent
from pydantic import BaseModel
from mcp_client import MCPClient
from oauth_client import OAuth2Client


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


async def authenticate_with_oauth(console: Console) -> str | None:
    """Handle OAuth authentication flow and return access token."""
    console.print("\n[bold yellow]🔐 OAuth Authentication Required[/bold yellow]")
    console.print("The MCP server requires authentication via OAuth 2.0")
    
    # Ask user if they want to proceed with OAuth
    proceed = Prompt.ask("\n[bold green]Do you want to proceed with OAuth authentication?[/bold green]", 
                        choices=["y", "n"], default="y")
    
    if proceed.lower() != "y":
        console.print("[dim]OAuth authentication cancelled.[/dim]")
        return None
    
    # Get email from user
    email = Prompt.ask("\n[bold green]Enter your email address for login[/bold green]")
    if not email.strip():
        console.print("[red]No email provided. Cannot proceed with OAuth.[/red]")
        return None
    
    # Initialize OAuth client with Composio endpoints
    oauth_client = OAuth2Client(
        authorization_endpoint="https://login.composio.dev/oauth2/authorize",
        token_endpoint="https://login.composio.dev/oauth2/token"
    )
    
    console.print("\n[dim]Starting OAuth flow...[/dim]")
    
    # Run interactive auth flow
    access_token = await oauth_client.interactive_auth_flow(email=email)
    
    if access_token:
        console.print(f"\n[green]🎉 OAuth Success! Access token obtained[/green]")
        return access_token
    else:
        console.print("\n[red]❌ OAuth authentication failed[/red]")
        return None


async def query_mcp_server(console: Console) -> None:
    """Try to connect to the MCP server and introspect tools."""
    console.print("\n[bold blue]Now trying MCP server connection...[/bold blue]")
    
    # Create MCP client
    mcp_client = MCPClient("https://rube.app/mcp")
    
    # First attempt without authentication
    try:
        tools = await mcp_client.introspect_tools()
        
        console.print(f"[green]Initialization successful! Session ID: {mcp_client.session_id}[/green]")
        
        # Create a nice panel with the tools information
        tools_text = ""
        if tools:
            for i, tool in enumerate(tools, 1):
                tool_name = tool.get('name', 'Unknown')
                tool_desc = tool.get('description', 'No description')
                tools_text += f"[bold yellow]{i}. {tool_name}[/bold yellow]\n   {tool_desc}\n\n"
        else:
            tools_text = "[dim]No tools available[/dim]"
        
        content = f"[bold green]Found {len(tools)} tools:[/bold green]\n\n{tools_text}"
        panel = Panel(
            content,
            title="[bold magenta]Available Tools from rube.app MCP Server[/bold magenta]",
            border_style="cyan",
            expand=True
        )
        console.print(panel)
        return
        
    except Exception as e:
        import traceback
        error_msg = str(e)
        traceback_str = traceback.format_exc()
        
        # Check for 401 Unauthorized error
        if ("401 Unauthorized" in error_msg or "401 Unauthorized" in traceback_str or 
            "HTTPStatusError" in error_msg or "HTTPStatusError" in traceback_str):
            
            console.print("[yellow]🔒 Authentication required for MCP server[/yellow]")
            
            # Try OAuth authentication
            access_token = await authenticate_with_oauth(console)
            
            if access_token:
                # Retry with Bearer token
                console.print("\n[blue]🔄 Retrying MCP connection with OAuth token...[/blue]")
                mcp_client.set_bearer_token(access_token)
                
                try:
                    tools = await mcp_client.introspect_tools()
                    
                    console.print(f"[green]✅ Authenticated connection successful! Session ID: {mcp_client.session_id}[/green]")
                    
                    # Create a nice panel with the tools information
                    tools_text = ""
                    if tools:
                        for i, tool in enumerate(tools, 1):
                            tool_name = tool.get('name', 'Unknown')
                            tool_desc = tool.get('description', 'No description')
                            tools_text += f"[bold yellow]{i}. {tool_name}[/bold yellow]\n   {tool_desc}\n\n"
                    else:
                        tools_text = "[dim]No tools available[/dim]"
                    
                    content = f"[bold green]Found {len(tools)} tools:[/bold green]\n\n{tools_text}"
                    panel = Panel(
                        content,
                        title="[bold magenta]🔐 Authenticated Tools from rube.app MCP Server[/bold magenta]",
                        border_style="cyan",
                        expand=True
                    )
                    console.print(panel)
                    return
                    
                except Exception as auth_error:
                    error_details = (
                        f"[bold red]Authentication failed:[/bold red]\n\n"
                        f"Even with OAuth token, the MCP server rejected the request.\n"
                        f"Error: {str(auth_error)}\n\n"
                        "[dim]The token may be invalid or the server configuration may have changed.[/dim]"
                    )
                    
                    error_panel = Panel(
                        error_details,
                        title="[bold red]🔐 Authenticated MCP Connection Failed[/bold red]",
                        border_style="red",
                        expand=True
                    )
                    console.print(error_panel)
                    return
            else:
                # OAuth failed, show original error
                error_details = (
                    "[bold red]Authentication Required:[/bold red]\n\n"
                    "The MCP server at https://rube.app/mcp requires authentication.\n"
                    "OAuth authentication was attempted but failed.\n\n"
                    "[bold green]✅ Good news:[/bold green] The MCP client connection is working correctly!\n"
                    "[dim]The server just requires proper credentials.[/dim]"
                )
        else:
            error_details = f"[bold red]MCP Error:[/bold red] {error_msg}\n\n[dim]Full traceback:[/dim]\n{traceback_str}"
            
        error_panel = Panel(
            error_details,
            title="[bold red]MCP Connection Error[/bold red]",
            border_style="red",
            expand=True
        )
        console.print(error_panel)


async def main():
    """Main function that coordinates OpenAI and MCP queries."""
    console = Console()
    
    # Query OpenAI about Canadian cities
    #await query_openai_for_city(console)
    
    # Try to connect to the MCP server
    await query_mcp_server(console)


if __name__ == "__main__":
    asyncio.run(main())


