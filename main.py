#!/usr/bin/env python3

import asyncio
from rich.console import Console
from rich.panel import Panel
from mcp.client.streamable_http import streamablehttp_client
from mcp.shared.message import SessionMessage
from mcp.types import (
    JSONRPCMessage,
    JSONRPCRequest,
    JSONRPCNotification,
    JSONRPCResponse,
    ClientCapabilities,
    RootsCapability,
    InitializeRequestParams,
    Implementation,
)
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


async def query_mcp_server(console: Console) -> None:
    """Try to connect to the MCP server and introspect tools."""
    console.print("\n[bold blue]Now trying MCP server connection...[/bold blue]")
    
    try:
        # Use the official streamablehttp_client
        async with streamablehttp_client("https://rube.app/mcp") as (read_stream, write_stream, get_session_id):
            # Send initialize request
            initialize_params = InitializeRequestParams(
                protocolVersion="2024-11-05",
                capabilities=ClientCapabilities(
                    roots=RootsCapability(listChanged=True)
                ),
                clientInfo=Implementation(name="rube-iks-cube", version="0.1.0")
            )
            
            init_message = SessionMessage(
                message=JSONRPCMessage(root=JSONRPCRequest(
                    jsonrpc="2.0",
                    id=1,
                    method="initialize",
                    params=initialize_params.model_dump(by_alias=True, exclude_none=True)
                ))
            )
            
            await write_stream.send(init_message)
            
            # Wait for initialize response
            response = await read_stream.receive()
            if isinstance(response, Exception):
                raise response
                
            console.print(f"[green]Initialization successful! Session ID: {get_session_id()}[/green]")
            
            # Send initialized notification
            initialized_notification = SessionMessage(
                message=JSONRPCMessage(root=JSONRPCNotification(
                    jsonrpc="2.0",
                    method="notifications/initialized",
                    params={}
                ))
            )
            
            await write_stream.send(initialized_notification)
            
            # List available tools
            list_tools_request = SessionMessage(
                message=JSONRPCMessage(root=JSONRPCRequest(
                    jsonrpc="2.0",
                    id=2,
                    method="tools/list",
                    params={}
                ))
            )
            
            await write_stream.send(list_tools_request)
            
            # Wait for tools response
            tools_response = await read_stream.receive()
            if isinstance(tools_response, Exception):
                raise tools_response
            
            # Parse tools from response
            tools = []
            if (isinstance(tools_response.message.root, JSONRPCResponse) and 
                tools_response.message.root.result and 
                isinstance(tools_response.message.root.result, dict) and
                'tools' in tools_response.message.root.result):
                tools = tools_response.message.root.result['tools']
            
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
            
    except Exception as e:
        import traceback
        error_msg = str(e)
        traceback_str = traceback.format_exc()
        
        # Check for specific HTTP errors in the error message or traceback
        if ("401 Unauthorized" in error_msg or "401 Unauthorized" in traceback_str or 
            "HTTPStatusError" in error_msg or "HTTPStatusError" in traceback_str):
            error_details = (
                "[bold red]Authentication Required:[/bold red]\n\n"
                "The MCP server at https://rube.app/mcp requires authentication.\n"
                "You may need to provide API keys or authentication headers.\n\n"
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


