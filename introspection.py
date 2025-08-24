"""
Introspection utilities for exploring Composio SDK objects.
"""

import inspect
from typing import get_type_hints
from rich.console import Console


def introspect_composio_client(client, console: Console) -> None:
    """Perform detailed introspection of the Composio client object."""
    
    # Get the object type name for the title
    object_type = client.__class__.__name__
    
    # Get all attributes and methods
    console.print(f"\n[bold cyan]=== {object_type} API ===[/bold cyan]")
    all_attrs = dir(client)
    
    # Get only public methods
    methods = []
    for attr in all_attrs:
        if not attr.startswith('_') and callable(getattr(client, attr)):
            methods.append(attr)
    
    console.print(f"\n[bold green]Available Methods ({len(methods)}):[/bold green]")
    for method in sorted(methods):
        try:
            method_obj = getattr(client, method)
            console.print(f"\n[bold yellow]• {method}[/bold yellow]")
            
            # Get method signature
            try:
                sig = inspect.signature(method_obj)
                console.print(f"  [cyan]Signature:[/cyan] {method}{sig}")
            except (ValueError, TypeError):
                console.print("  [cyan]Signature:[/cyan] Unable to inspect signature")
            
            # Get type hints if available
            try:
                type_hints = get_type_hints(method_obj)
                if type_hints:
                    console.print("  [cyan]Type Hints:[/cyan]")
                    for param, hint in type_hints.items():
                        console.print(f"    {param}: {hint}")
            except (NameError, AttributeError, TypeError):
                pass
            
            # Get parameters from signature
            try:
                sig = inspect.signature(method_obj)
                if sig.parameters:
                    console.print("  [cyan]Parameters:[/cyan]")
                    for param_name in sig.parameters:
                        param_obj = sig.parameters[param_name]
                        param_info = f"    {param_name}"
                        # Use getattr to safely access parameter attributes
                        annotation = getattr(param_obj, 'annotation', inspect.Parameter.empty)
                        if annotation != inspect.Parameter.empty:
                            param_info += f": {annotation}"
                        default = getattr(param_obj, 'default', inspect.Parameter.empty)
                        if default != inspect.Parameter.empty:
                            param_info += f" = {default}"
                        console.print(param_info)
            except (ValueError, TypeError):
                pass
            
            # Get docstring
            if hasattr(method_obj, '__doc__') and method_obj.__doc__:
                doc = method_obj.__doc__.strip()
                console.print("  [cyan]Documentation:[/cyan]")
                # Split docstring into lines and indent them
                for line in doc.split('\n'):
                    console.print(f"    {line.strip()}")
            else:
                console.print("  [cyan]Documentation:[/cyan] No documentation available")
                
        except Exception as e:
            console.print(f"  • {method} (inspection failed: {e})")
    
    console.print(f"\n[green]✓ {object_type} API introspection completed[/green]")
