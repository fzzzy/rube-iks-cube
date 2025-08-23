
import logging
from typing import        self.headers = headers or {}
        self._session_id = None
        self._next_request_id = 1 Optional
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

# Simple logging setup
logger = logging.getLogger(__name__)


class MCPClient:
    """Client for connecting to and interacting with MCP (Model Context Protocol) servers."""
    
    def __init__(self, url: str, auth: Optional[Any] = None, headers: Optional[Dict[str, str]] = None):
        """
        Initialize the MCP client with a server URL and optional authentication.
        
        Args:
            url: The URL of the MCP server to connect to
            auth: Optional httpx.Auth instance for authentication (e.g., httpx.BasicAuth, bearer tokens)
            headers: Optional additional headers to include in requests
        """
        self.url = url
        self.auth = auth
        self.headers = headers or {}
        self._session_id = None
        self._next_request_id = 1
        
        logger.info("=== INITIALIZING MCP CLIENT ===")
        logger.info(f"Server URL: {url}")
        logger.info(f"Authentication configured: {auth is not None}")
        logger.info(f"Additional headers: {bool(self.headers)}")
        if self.headers:
            # Log headers but mask potential sensitive values
            safe_headers = {}
            for k, v in self.headers.items():
                if any(sensitive in k.lower() for sensitive in ['auth', 'token', 'key', 'secret']):
                    safe_headers[k] = "***MASKED***"
                else:
                    safe_headers[k] = v
            logger.info(f"Header keys: {list(safe_headers.keys())}")
    
    def set_bearer_token(self, token: str) -> None:
        """
        Set a bearer token for authorization.
        
        Args:
            token: The bearer token to use for authorization
        """
        self.headers = self.headers or {}
        self.headers['Authorization'] = f'Bearer {token}'
        logger.info("Bearer token configured for authorization")
    
    def set_api_key(self, api_key: str, header_name: str = 'X-API-Key') -> None:
        """
        Set an API key for authorization.
        
        Args:
            api_key: The API key to use
            header_name: The header name to use (default: 'X-API-Key')
        """
        self.headers = self.headers or {}
        self.headers[header_name] = api_key
        logger.info(f"API key configured with header: {header_name}")
    
    def _get_next_id(self) -> int:
        """Get the next request ID for JSON-RPC messages."""
        request_id = self._next_request_id
        self._next_request_id += 1
        return request_id
    
    async def _initialize_connection(self, read_stream, write_stream, get_session_id):
        """
        Initialize the MCP connection by sending the initialize request and notification.
        
        Args:
            read_stream: The read stream from the MCP client connection
            write_stream: The write stream from the MCP client connection
            get_session_id: Function to get the session ID
        """
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
                id=self._get_next_id(),
                method="initialize",
                params=initialize_params.model_dump(by_alias=True, exclude_none=True)
            ))
        )
        
        logger.info("=== SENDING INITIALIZE REQUEST ===")
        logger.info(f"Target URL: {self.url}")
        logger.info(f"Request message: {init_message.message.model_dump(by_alias=True, exclude_none=True)}")
        
        await write_stream.send(init_message)
        
        # Wait for initialize response
        response = await read_stream.receive()
        
        logger.info("=== RECEIVED INITIALIZE RESPONSE ===")
        if isinstance(response, Exception):
            logger.error(f"Initialize failed with exception: {type(response).__name__}: {response}")
            # Try to extract more details if it's an HTTP-related exception
            if hasattr(response, 'response'):
                http_response = getattr(response, 'response')
                logger.error(f"HTTP Status Code: {getattr(http_response, 'status_code', 'Unknown')}")
                logger.error(f"HTTP Headers: {dict(getattr(http_response, 'headers', {}))}")
                try:
                    content = getattr(http_response, 'text', None) or getattr(http_response, 'content', 'No content')
                    logger.error(f"HTTP Content: {content}")
                except Exception as e:
                    logger.error(f"Could not extract HTTP content: {e}")
            # Also log any other interesting attributes
            for attr in ['status_code', 'headers', 'text', 'content', 'request', 'args']:
                if hasattr(response, attr):
                    try:
                        value = getattr(response, attr)
                        logger.error(f"Exception.{attr}: {value}")
                    except Exception as e:
                        logger.error(f"Could not access Exception.{attr}: {e}")
            raise response
        
        logger.info(f"Initialize response: {response.message.model_dump(by_alias=True, exclude_none=True)}")
        
        self._session_id = get_session_id()
        logger.info(f"Session ID established: {self._session_id}")
        
        # Send initialized notification
        initialized_notification = SessionMessage(
            message=JSONRPCMessage(root=JSONRPCNotification(
                jsonrpc="2.0",
                method="notifications/initialized",
                params={}
            ))
        )
        
        logger.info("=== SENDING INITIALIZED NOTIFICATION ===")
        logger.info(f"Notification: {initialized_notification.message.model_dump(by_alias=True, exclude_none=True)}")
        
        await write_stream.send(initialized_notification)
    
    async def introspect_tools(self) -> List[Dict[str, Any]]:
        """
        Connect to the MCP server and retrieve the list of available tools.
        
        Returns:
            List of tool dictionaries containing name, description, and other metadata
            
        Raises:
            Exception: If connection fails or server returns an error
        """
        logger.info("=== STARTING TOOL INTROSPECTION ===")
        logger.info(f"Connecting to MCP server at: {self.url}")
        
        try:
            async with streamablehttp_client(
                self.url, 
                headers=self.headers, 
                auth=self.auth
            ) as (read_stream, write_stream, get_session_id):
                # Initialize the connection
                await self._initialize_connection(read_stream, write_stream, get_session_id)
                
                # List available tools
                list_tools_request = SessionMessage(
                    message=JSONRPCMessage(root=JSONRPCRequest(
                        jsonrpc="2.0",
                        id=self._get_next_id(),
                        method="tools/list",
                        params={}
                    ))
                )
                
                logger.info("=== SENDING TOOLS/LIST REQUEST ===")
                logger.info(f"Request message: {list_tools_request.message.model_dump(by_alias=True, exclude_none=True)}")
                
                await write_stream.send(list_tools_request)
                
                # Wait for tools response
                logger.info("=== WAITING FOR TOOLS/LIST RESPONSE ===")
                tools_response = await read_stream.receive()
                
                logger.info("=== RECEIVED TOOLS/LIST RESPONSE ===")
                if isinstance(tools_response, Exception):
                    logger.error(f"Tools list failed with exception: {type(tools_response).__name__}: {tools_response}")
                    # Extract detailed error information
                    if hasattr(tools_response, 'response'):
                        http_response = getattr(tools_response, 'response')
                        logger.error(f"HTTP Status Code: {getattr(http_response, 'status_code', 'Unknown')}")
                        logger.error(f"HTTP Headers: {dict(getattr(http_response, 'headers', {}))}")
                        
                        # Look for authorization hints in headers
                        headers = getattr(http_response, 'headers', {})
                        if 'www-authenticate' in headers:
                            logger.error(f"WWW-Authenticate header found: {headers['www-authenticate']}")
                        if 'authorization' in headers:
                            logger.error(f"Authorization header in response: {headers['authorization']}")
                        
                        # Check for OAuth-related headers
                        oauth_headers = [h for h in headers.keys() if 'oauth' in h.lower() or 'bearer' in h.lower()]
                        if oauth_headers:
                            logger.error(f"OAuth/Bearer related headers: {oauth_headers}")
                        
                        try:
                            content = getattr(http_response, 'text', None) or getattr(http_response, 'content', 'No content')
                            logger.error(f"HTTP Response Content: {content}")
                            
                            # Look for OAuth/authorization hints in response body
                            if isinstance(content, str):
                                content_lower = content.lower()
                                if any(word in content_lower for word in ['oauth', 'bearer', 'token', 'authorize', 'authentication']):
                                    logger.error("Response content contains authentication-related keywords")
                                    
                        except Exception as e:
                            logger.error(f"Could not extract HTTP content: {e}")
                    
                    # Log all exception attributes for debugging
                    for attr in ['status_code', 'headers', 'text', 'content', 'request', 'args']:
                        if hasattr(tools_response, attr):
                            try:
                                value = getattr(tools_response, attr)
                                logger.error(f"Exception.{attr}: {value}")
                            except Exception as e:
                                logger.error(f"Could not access Exception.{attr}: {e}")
                    
                    raise tools_response
                
                logger.info(f"Tools response: {tools_response.message.model_dump(by_alias=True, exclude_none=True)}")
                
                # Parse tools from response
                tools = []
                if (isinstance(tools_response.message.root, JSONRPCResponse) and 
                    tools_response.message.root.result and 
                    isinstance(tools_response.message.root.result, dict) and
                    'tools' in tools_response.message.root.result):
                    tools = tools_response.message.root.result['tools']
                    logger.info(f"Successfully retrieved {len(tools)} tools")
                    for i, tool in enumerate(tools):
                        logger.debug(f"Tool {i+1}: {tool.get('name', 'Unknown')} - {tool.get('description', 'No description')}")
                else:
                    logger.warning("No tools found in response or unexpected response format")
                
                return tools
                
        except Exception as e:
            logger.error("=== TOOL INTROSPECTION FAILED ===")
            logger.error(f"Exception type: {type(e).__name__}")
            logger.error(f"Exception message: {e}")
            
            # Try to extract more details for authorization errors
            logger.error(f"Exception dictionary: {e.__dict__}")
            
            # Handle ExceptionGroup - extract sub-exceptions
            if hasattr(e, 'exceptions'):
                exceptions = getattr(e, 'exceptions', [])
                logger.error(f"Found ExceptionGroup with {len(exceptions)} sub-exceptions:")
                for i, sub_exception in enumerate(exceptions):
                    logger.error(f"Sub-exception {i}: {type(sub_exception).__name__}: {sub_exception}")
                    logger.error(f"Sub-exception {i} dict: {sub_exception.__dict__}")
                    
                    # Check each sub-exception for HTTP response details
                    if hasattr(sub_exception, 'response'):
                        http_response = getattr(sub_exception, 'response')
                        status_code = getattr(http_response, 'status_code', None)
                        logger.error(f"Sub-exception {i} HTTP Status Code: {status_code}")
                        
                        if status_code in [401, 403]:
                            logger.error(f"=== AUTHORIZATION ERROR DETECTED IN SUB-EXCEPTION {i} ===")
                            headers = dict(getattr(http_response, 'headers', {}))
                            logger.error(f"All response headers: {headers}")
                            
                            # Look for specific authorization hints
                            auth_hints = []
                            if 'www-authenticate' in headers:
                                auth_hints.append(f"WWW-Authenticate: {headers['www-authenticate']}")
                            if 'authorization' in headers:
                                auth_hints.append(f"Authorization in response: {headers['authorization']}")
                            
                            # Check for OAuth-related information
                            for header_name, header_value in headers.items():
                                if any(word in header_name.lower() for word in ['oauth', 'bearer', 'token', 'auth']):
                                    auth_hints.append(f"{header_name}: {header_value}")
                            
                            if auth_hints:
                                logger.error("Authorization hints found:")
                                for hint in auth_hints:
                                    logger.error(f"  {hint}")
                            else:
                                logger.error("No explicit authorization hints found in headers")
                                
                            # Try to get response content
                            try:
                                if hasattr(http_response, 'text'):
                                    content = http_response.text
                                elif hasattr(http_response, 'content'):
                                    content = http_response.content
                                else:
                                    content = "No content available"
                                logger.error(f"HTTP Response Content: {content}")
                            except Exception as content_e:
                                logger.error(f"Could not extract HTTP content: {content_e}")
            
            # Also check if the main exception has response details
            if hasattr(e, 'response'):
                http_response = getattr(e, 'response')
                status_code = getattr(http_response, 'status_code', None)
                logger.error(f"HTTP Status Code: {status_code}")
                
                if status_code in [401, 403]:
                    logger.error("=== AUTHORIZATION ERROR DETECTED ===")
                    headers = dict(getattr(http_response, 'headers', {}))
                    logger.error(f"All response headers: {headers}")
                    
                    # Look for specific authorization hints
                    auth_hints = []
                    if 'www-authenticate' in headers:
                        auth_hints.append(f"WWW-Authenticate: {headers['www-authenticate']}")
                    if 'authorization' in headers:
                        auth_hints.append(f"Authorization in response: {headers['authorization']}")
                    
                    # Check for OAuth-related information
                    for header_name, header_value in headers.items():
                        if any(word in header_name.lower() for word in ['oauth', 'bearer', 'token', 'auth']):
                            auth_hints.append(f"{header_name}: {header_value}")
                    
                    if auth_hints:
                        logger.error("Authorization hints found:")
                        for hint in auth_hints:
                            logger.error(f"  {hint}")
                    else:
                        logger.error("No explicit authorization hints found in headers")
            
            raise
    
    async def call_tool(self, tool_name: str, arguments: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Call a specific tool on the MCP server.
        
        Args:
            tool_name: The name of the tool to call
            arguments: Optional dictionary of arguments to pass to the tool
            
        Returns:
            Dictionary containing the tool's response
            
        Raises:
            Exception: If connection fails, tool doesn't exist, or server returns an error
        """
        if arguments is None:
            arguments = {}
        
        logger.info("=== STARTING TOOL CALL ===")
        logger.info(f"Tool name: {tool_name}")
        logger.info(f"Arguments: {arguments}")
        logger.info(f"Connecting to MCP server at: {self.url}")
        
        try:
            async with streamablehttp_client(
                self.url, 
                headers=self.headers, 
                auth=self.auth
            ) as (read_stream, write_stream, get_session_id):
                # Initialize the connection
                await self._initialize_connection(read_stream, write_stream, get_session_id)
                
                # Call the tool
                tool_call_request = SessionMessage(
                    message=JSONRPCMessage(root=JSONRPCRequest(
                        jsonrpc="2.0",
                        id=self._get_next_id(),
                        method="tools/call",
                        params={
                            "name": tool_name,
                            "arguments": arguments
                        }
                    ))
                )
                
                logger.info("=== SENDING TOOLS/CALL REQUEST ===")
                logger.info(f"Request message: {tool_call_request.message.model_dump(by_alias=True, exclude_none=True)}")
                
                await write_stream.send(tool_call_request)
                
                # Wait for tool response
                logger.info("=== WAITING FOR TOOLS/CALL RESPONSE ===")
                tool_response = await read_stream.receive()
                
                logger.info("=== RECEIVED TOOLS/CALL RESPONSE ===")
                if isinstance(tool_response, Exception):
                    logger.error(f"Tool call failed with exception: {type(tool_response).__name__}: {tool_response}")
                    
                    # Extract detailed error information for authorization issues
                    if hasattr(tool_response, 'response'):
                        http_response = getattr(tool_response, 'response')
                        status_code = getattr(http_response, 'status_code', None)
                        logger.error(f"HTTP Status Code: {status_code}")
                        
                        if status_code in [401, 403]:
                            logger.error("=== AUTHORIZATION ERROR DURING TOOL CALL ===")
                            headers = dict(getattr(http_response, 'headers', {}))
                            logger.error(f"All response headers: {headers}")
                            
                            # Look for authorization hints
                            auth_hints = []
                            if 'www-authenticate' in headers:
                                auth_hints.append(f"WWW-Authenticate: {headers['www-authenticate']}")
                            if 'authorization' in headers:
                                auth_hints.append(f"Authorization in response: {headers['authorization']}")
                            
                            # Check for OAuth/Bearer related headers
                            for header_name, header_value in headers.items():
                                if any(word in header_name.lower() for word in ['oauth', 'bearer', 'token', 'auth']):
                                    auth_hints.append(f"{header_name}: {header_value}")
                            
                            if auth_hints:
                                logger.error("Authorization hints found:")
                                for hint in auth_hints:
                                    logger.error(f"  {hint}")
                            
                            try:
                                content = getattr(http_response, 'text', None) or getattr(http_response, 'content', 'No content')
                                logger.error(f"HTTP Response Content: {content}")
                                
                                # Look for OAuth/authorization hints in response body
                                if isinstance(content, str):
                                    content_lower = content.lower()
                                    if any(word in content_lower for word in ['oauth', 'bearer', 'token', 'authorize', 'authentication']):
                                        logger.error("Response content contains authentication-related keywords")
                                        
                            except Exception as e:
                                logger.error(f"Could not extract HTTP content: {e}")
                        
                        logger.error(f"HTTP Headers: {dict(getattr(http_response, 'headers', {}))}")
                    
                    # Log all exception attributes for debugging
                    for attr in ['status_code', 'headers', 'text', 'content', 'request', 'args']:
                        if hasattr(tool_response, attr):
                            try:
                                value = getattr(tool_response, attr)
                                logger.error(f"Exception.{attr}: {value}")
                            except Exception as e:
                                logger.error(f"Could not access Exception.{attr}: {e}")
                    
                    raise tool_response
                
                logger.info(f"Tool response: {tool_response.message.model_dump(by_alias=True, exclude_none=True)}")
                
                # Parse result from response
                if isinstance(tool_response.message.root, JSONRPCResponse):
                    result = tool_response.message.root.result or {}
                    logger.info(f"Tool call successful, result keys: {list(result.keys()) if isinstance(result, dict) else 'Non-dict result'}")
                    return result
                else:
                    logger.error("Unexpected response format from tool call")
                    raise Exception("Unexpected response format from tool call")
                    
        except Exception as e:
            logger.error("=== TOOL CALL FAILED ===")
            logger.error(f"Exception type: {type(e).__name__}")
            logger.error(f"Exception message: {e}")
            
            # Try to extract more details for authorization errors
            if hasattr(e, 'response'):
                http_response = getattr(e, 'response')
                status_code = getattr(http_response, 'status_code', None)
                logger.error(f"HTTP Status Code: {status_code}")
                
                if status_code in [401, 403]:
                    logger.error("=== AUTHORIZATION ERROR DETECTED IN TOOL CALL ===")
                    headers = dict(getattr(http_response, 'headers', {}))
                    logger.error(f"All response headers: {headers}")
                    
                    # Look for specific authorization hints
                    auth_hints = []
                    if 'www-authenticate' in headers:
                        auth_hints.append(f"WWW-Authenticate: {headers['www-authenticate']}")
                    if 'authorization' in headers:
                        auth_hints.append(f"Authorization in response: {headers['authorization']}")
                    
                    # Check for OAuth-related information
                    for header_name, header_value in headers.items():
                        if any(word in header_name.lower() for word in ['oauth', 'bearer', 'token', 'auth']):
                            auth_hints.append(f"{header_name}: {header_value}")
                    
                    if auth_hints:
                        logger.error("Authorization hints found:")
                        for hint in auth_hints:
                            logger.error(f"  {hint}")
                    else:
                        logger.error("No explicit authorization hints found in headers")
            
            raise
    
    @property
    def session_id(self) -> Optional[str]:
        """Get the current session ID, if connected."""
        return self._session_id
