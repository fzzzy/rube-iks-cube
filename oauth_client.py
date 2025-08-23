#!/usr/bin/env python3

import asyncio
import secrets
import urllib.parse
from typing import Optional, Dict, Any
import subprocess
import httpx
from rich.console import Console
from rich.prompt import Prompt


class OAuth2Client:
    """OAuth 2.0 client for rube.app authentication."""
    
    def __init__(self, authorization_endpoint: str, token_endpoint: str, 
                 client_id: Optional[str] = None, client_secret: Optional[str] = None):
        self.authorization_endpoint = authorization_endpoint
        self.token_endpoint = token_endpoint
        self.client_id = client_id
        self.client_secret = client_secret
    
    def generate_authorization_url(self, redirect_uri: str, email: str) -> tuple[str, str]:
        """Generate OAuth 2.0 authorization URL."""
        state = secrets.token_urlsafe(32)
        
        params = {
            "response_type": "code",
            "redirect_uri": redirect_uri,
            "scope": "openid profile email",
            "state": state,
            "login_hint": email,
            "email": email
        }
        
        if self.client_id:
            params["client_id"] = self.client_id
        
        auth_url = f"{self.authorization_endpoint}?{urllib.parse.urlencode(params)}"
        return auth_url, state
    
    async def exchange_code_for_token(self, auth_code: str, redirect_uri: str) -> Optional[Dict[str, Any]]:
        """Exchange authorization code for access token."""
        data = {
            "grant_type": "authorization_code",
            "code": auth_code,
            "redirect_uri": redirect_uri
        }
        
        if self.client_id:
            data["client_id"] = self.client_id
        if self.client_secret:
            data["client_secret"] = self.client_secret
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.token_endpoint,
                    data=data,
                    headers={"Accept": "application/json"}
                )
                response.raise_for_status()
                return response.json()
        except Exception:
            return None
    
    async def interactive_auth_flow(self, email: str) -> Optional[str]:
        """
        Interactive OAuth 2.0 authorization flow with manual token extraction.
        """
        console = Console()
        console.print("🔐 Starting OAuth 2.0 Authorization Flow", style="bold blue")
        
        try:
            # Generate authorization URL with rube.app's expected redirect URI
            auth_url, state = self.generate_authorization_url(
                redirect_uri="https://rube.app/api/auth/callback",
                email=email
            )
            
            console.print("🌐 Opening authorization URL in browser...", style="yellow")
            
            # Open browser
            try:
                subprocess.run(["open", auth_url], check=True)
                console.print("✅ Browser opened successfully!", style="green")
            except subprocess.CalledProcessError as e:
                console.print(f"❌ Failed to open browser: {e}", style="red")
                console.print(f"\nPlease manually open this URL: {auth_url}", style="yellow")
            
            # Guide user through the process
            console.print("\n" + "="*80, style="bold blue")
            console.print("📋 COMPLETE OAUTH IN BROWSER", style="bold blue")
            console.print("="*80, style="bold blue")
            
            console.print("\n1. 🔐 Complete the OAuth login in your browser")
            console.print("2. 🏠 You should be redirected to the rube.app dashboard")
            console.print("3. 🔍 We need to extract your session token from the browser")
            
            # Wait for user to complete OAuth
            Prompt.ask("\n[bold green]Press Enter after you've completed the OAuth login and are on rube.app")
            
            console.print("\n" + "="*80, style="bold yellow")
            console.print("🔑 TOKEN EXTRACTION INSTRUCTIONS", style="bold yellow")
            console.print("="*80, style="bold yellow")
            
            console.print("\nNow we need to get your authentication token. Try these methods:")
            console.print("\n[bold]Method 1: Browser Developer Tools[/bold]")
            console.print("1. In your rube.app browser tab, press F12 (or Cmd+Option+I on Mac)")
            console.print("2. Go to the 'Application' tab (Chrome) or 'Storage' tab (Firefox)")
            console.print("3. Look in 'Local Storage' or 'Session Storage' for rube.app")
            console.print("4. Look for keys like: 'token', 'access_token', 'auth_token', 'session'")
            console.print("5. Copy the token value")
            
            console.print("\n[bold]Method 2: Network Tab[/bold]")
            console.print("1. In Developer Tools, go to the 'Network' tab")
            console.print("2. Refresh the rube.app page")
            console.print("3. Look for requests with 'Authorization: Bearer ...' headers")
            console.print("4. Copy the Bearer token value")
            
            # Ask for the token
            token = Prompt.ask("\n[bold green]Paste your authentication token here")
            
            if token and token.strip():
                # Clean up the token (remove "Bearer " prefix if present)
                token = token.strip()
                if token.lower().startswith("bearer "):
                    token = token[7:]  # Remove "Bearer " prefix
                
                console.print("✅ Token received!", style="green")
                console.print(f"Token preview: {token[:20]}..." if len(token) > 20 else f"Token: {token}", style="dim")
                
                if len(token) > 10:  # Basic length check
                    console.print("🎉 Authentication token successfully obtained!", style="bold green")
                    return token
                else:
                    console.print("⚠️  Token seems short, but proceeding anyway...", style="yellow")
                    return token
            else:
                console.print("❌ No token provided", style="red")
                return None
            
        except Exception as e:
            console.print(f"❌ Error during authorization: {e}", style="bold red")
            return None


async def main():
    """Test the OAuth client."""
    console = Console()
    
    console.print("[bold blue]🧪 Testing OAuth 2.0 Client[/bold blue]")
    
    # Initialize OAuth client with Composio endpoints
    oauth_client = OAuth2Client(
        authorization_endpoint="https://login.composio.dev/oauth2/authorize",
        token_endpoint="https://login.composio.dev/oauth2/token"
    )
    
    # Get email from user
    email = Prompt.ask("\n[bold green]Enter your email address for login hint", default="")
    if email.strip() == "":
        print("No email provided. Exiting.")
        return
    
    # Run interactive auth flow
    access_token = await oauth_client.interactive_auth_flow(email=email)
    
    if access_token:
        console.print(f"\n[green]🎉 Success! Access token obtained: {access_token[:20]}...[/green]")
        console.print("\n[dim]You can now use this token with the MCP client:[/dim]")
        console.print(f"[code]client.set_bearer_token('{access_token}')[/code]")
    else:
        console.print("\n[red]❌ Failed to obtain access token[/red]")


if __name__ == "__main__":
    asyncio.run(main())
