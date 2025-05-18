import os
import requests
import json
import time
import subprocess
import threading
import sys
import asyncio
import nest_asyncio  # Add nest_asyncio for nested event loops
from typing import Dict, List, Any, Optional, Union
import uuid
from dotenv import load_dotenv

# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()

# Try official Anthropic client
try:
    from anthropic import Anthropic
    ANTHROPIC_CLIENT_AVAILABLE = True
    print("✅ Anthropic client library found and imported successfully")
except ImportError as e:
    ANTHROPIC_CLIENT_AVAILABLE = False
    print(f"❌ Anthropic client import failed: {e}")
    print("   Install with: pip install anthropic")

# Try to import MCP client library with both sync and async approaches
try:
    from mcp.client import Client as MCPClient
    MCP_CLIENT_AVAILABLE = True
    print("✅ MCP client library found and imported successfully")
except ImportError as e:
    MCP_CLIENT_AVAILABLE = False
    print(f"❌ MCP client library import failed: {e}")
    print("   Install with: pip install mcp")

# Try to import async MCP client
try:
    from mcp import ClientSession, StdioServerParameters, types
    from mcp.client.stdio import stdio_client
    ASYNC_MCP_AVAILABLE = True
    print("✅ Async MCP client libraries found and imported successfully")
except ImportError as e:
    ASYNC_MCP_AVAILABLE = False
    print(f"❌ Async MCP client import failed: {e}")
    print("   Install with: pip install mcp")

# Import fold_server module directly if possible
try:
    import fold_server
    FOLD_SERVER_IMPORTABLE = True
    print("✅ fold_server module can be imported directly")
except ImportError:
    FOLD_SERVER_IMPORTABLE = False
    print("❌ fold_server module cannot be imported directly")

load_dotenv()  # Add this line after the imports

# ANSI color codes for colored terminal output
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

class ProteinDesignAgent:
    def __init__(
        self,
        esmfold_mcp_path: Optional[str] = "fold_server.py",
        llm_api_key: Optional[str] = os.environ.get("ANTHROPIC_API_KEY"),
        llm_api_url: str = "https://api.anthropic.com/v1/messages",
        verbose: bool = True,
        model_name: str = "claude-3-5-sonnet-20240620"  # Updated to newer model
    ):
        """
        Initialize the protein design agent.
        
        Args:
            esmfold_mcp_path: Path to the ESMfold MCP server script
            llm_api_key: API key for the LLM service (Claude)
            llm_api_url: URL for the LLM API
            verbose: Whether to print detailed logs
            model_name: Name of the Claude model to use
        """
        self.esmfold_mcp_path = esmfold_mcp_path
        self.llm_api_key = llm_api_key
        self.llm_api_url = llm_api_url
        self.verbose = verbose
        self.session_id = str(uuid.uuid4())
        self.model_name = model_name  # Store model name
        
        # Initialize MCP client
        self.mcp_client = None
        self.mcp_server_process = None
        
        # Initialize Anthropic client
        if ANTHROPIC_CLIENT_AVAILABLE and self.llm_api_key:
            self.anthropic = Anthropic(api_key=self.llm_api_key)
        else:
            self.anthropic = None
        
        # Initialize MCP session and tools
        self.session = None  # ClientSession
        self.available_tools = []
        
        # Initialize conversation history
        self.conversation_history = []
        
        # Initialize basic session info
        self.current_iteration = 0
        self.best_sequence = None
        self.best_score = float('-inf')
        
    def log(self, message: str, color: Optional[str] = None) -> None:
        """Log a message if verbose mode is enabled."""
        if self.verbose:
            # Add emoji indicators based on color and message content
            emoji = ""
            
            # Check for specific message types first, before applying color defaults
            if "STRUCTURE PREDICTION" in message:
                emoji = "🧬 "  # DNA helix for structure prediction
            elif "BINDING PREDICTION" in message:
                emoji = "🧪 "  # Test tube for binding prediction
            elif "Making API call" in message:
                emoji = "🌐 "  # Globe for API calls
            elif "Sending query to Claude" in message:
                emoji = "🤖 "  # Robot for AI interactions
            elif "Successfully" in message or "SUCCESS" in message:
                emoji = "✅ "  # Green checkmark for success
            # Then handle color-based defaults
            elif color:
                if color == Colors.GREEN or color == Colors.BOLD + Colors.GREEN:
                    emoji = "✅ "  # Green checkmark for success
                elif color == Colors.RED or color == Colors.BOLD + Colors.RED:
                    # Only use red X for actual errors, not status messages
                    if any(err in message for err in ["Error", "error", "ERROR", "Failed", "failed", "FAILURE"]):
                        emoji = "❌ "  # Red X for errors
                    else:
                        emoji = "🔴 "  # Red circle for important (but not error) messages
                elif color == Colors.YELLOW or color == Colors.BOLD + Colors.YELLOW:
                    emoji = "⚠️ "  # Yellow warning triangle for warnings
                elif color == Colors.BLUE or color == Colors.BOLD + Colors.BLUE:
                    emoji = "🔹 "  # Blue dot for info
            
            # Print message with emoji
            if color:
                print(f"{color}{emoji}[ProteinDesignAgent] {message}{Colors.END}")
            else:
                print(f"{emoji}[ProteinDesignAgent] {message}")
                
    async def connect_to_server_and_run(self):
        """
        DEPRECATED: This method is kept for backward compatibility but should not be used.
        Use fold_with_fresh_connection instead for reliable connections.
        """
        self.log("WARNING: connect_to_server_and_run is deprecated, using fold_with_fresh_connection instead", Colors.YELLOW)
        return await self.fold_with_fresh_connection("ACDEFG") is not None
    
    def validate_and_clean_sequence(self, sequence: str) -> str:
        """
        Validate and clean a protein sequence by removing invalid characters.
        
        Args:
            sequence: Raw protein sequence to clean
            
        Returns:
            Cleaned sequence with only valid amino acid characters
        """
        valid_aa = set("ACDEFGHIKLMNPQRSTVWY")
        
        # Check if sequence needs cleaning
        if not all(aa in valid_aa for aa in sequence):
            invalid_chars = [aa for aa in sequence if aa not in valid_aa]
            self.log(f"WARNING: Sequence contains invalid amino acids: {invalid_chars}", Colors.YELLOW)
            
            # Clean the sequence
            cleaned_sequence = ''.join(aa for aa in sequence if aa in valid_aa)
            if cleaned_sequence != sequence:
                self.log(f"Cleaning sequence from {len(sequence)} to {len(cleaned_sequence)} chars", Colors.YELLOW)
                return cleaned_sequence
        
        return sequence

    async def process_query(self, query: str, sequence: str = None) -> Optional[str]:
        """
        Process a query using the LLM and MCP tools.
        
        Args:
            query: The query to process
            sequence: Optional protein sequence to fold
            
        Returns:
            PDB text if a fold operation was performed, otherwise None
        """
        if not self.anthropic:
            self.log("Anthropic client not initialized", Colors.RED)
            return None
        
        # Clean sequence if provided
        if sequence:
            sequence = self.validate_and_clean_sequence(sequence)
        
        # Create initial message
        content = query
        if sequence:
            content += f"\n\nPlease fold this protein sequence: {sequence}"
        
        messages = [{'role': 'user', 'content': content}]
        
        # Get available tools
        try:
            # Create fresh connection to get tools
            self.log("Creating fresh connection to get available tools", Colors.BLUE)
            python_path = sys.executable
            
            server_params = StdioServerParameters(
                command=python_path,
                args=[self.esmfold_mcp_path],
                env=os.environ.copy(),
            )
            
            available_tools = []
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await asyncio.wait_for(session.initialize(), timeout=10.0)
                    response = await asyncio.wait_for(session.list_tools(), timeout=10.0)
                    
                    available_tools = [{
                        "name": tool.name,
                        "description": tool.description,
                        "input_schema": tool.inputSchema
                    } for tool in response.tools]
                    
                    tool_names = [t["name"] for t in available_tools]
                    self.log(f"Available tools for Claude: {tool_names}", Colors.GREEN)
        except Exception as e:
            self.log(f"Error getting available tools: {e}", Colors.RED)
            return None
        
        # Create response
        self.log(f"Sending query to Claude with tools: {[t['name'] for t in available_tools]}", Colors.BLUE)
        
        response = self.anthropic.messages.create(
            max_tokens=2024,
            model=self.model_name,
            tools=available_tools,
            messages=messages
        )
        
        pdb_result = None
        process_query = True
        
        while process_query:
            assistant_content = []
            
            for content in response.content:
                if content.type == 'text':
                    self.log(f"Claude response: {content.text[:100]}...", Colors.GREEN)
                    assistant_content.append(content)
                    if len(response.content) == 1:
                        process_query = False
                        
                elif content.type == 'tool_use':
                    assistant_content.append(content)
                    messages.append({'role': 'assistant', 'content': assistant_content})
                    
                    tool_id = content.id
                    tool_args = content.input
                    tool_name = content.name
                    
                    self.log(f"Claude is calling tool: {tool_name} with args: {tool_args}", Colors.BLUE)
                    
                    # Call the tool through a fresh MCP connection for each tool call
                    try:
                        # If this is fold_sequence, use our fresh connection method
                        if tool_name == "fold_sequence":
                            sequence_to_fold = tool_args.get("sequence", "")
                            self.log(f"Folding sequence via Claude: {sequence_to_fold[:10]}...", Colors.BLUE)
                            
                            # Clean the sequence
                            sequence_to_fold = self.validate_and_clean_sequence(sequence_to_fold)
                            
                            # Use fresh connection to fold
                            loop = asyncio.get_event_loop()
                            pdb_text = loop.run_until_complete(
                                self.fold_with_fresh_connection(sequence_to_fold)
                            )
                            
                            if pdb_text:
                                pdb_result = pdb_text
                                self.log("Successfully received PDB from fold_sequence", Colors.GREEN)
                                tool_result = pdb_text
                            else:
                                tool_result = "Error: Failed to fold sequence"
                        else:
                            # For other tools (though we don't expect any)
                            self.log(f"Unknown tool requested: {tool_name}", Colors.RED)
                            tool_result = "Error: Unknown tool"
                        
                        # Add tool result to messages
                        messages.append({
                            "role": "user",
                            "content": [
                                {
                                    "type": "tool_result",
                                    "tool_use_id": tool_id,
                                    "content": tool_result
                                }
                            ]
                        })
                        
                        # Get next response
                        response = self.anthropic.messages.create(
                            max_tokens=2024,
                            model=self.model_name,
                            tools=available_tools,
                            messages=messages
                        )
                        
                        if len(response.content) == 1 and response.content[0].type == "text":
                            self.log(f"Final response: {response.content[0].text[:100]}...", Colors.GREEN)
                            process_query = False
                            
                    except Exception as e:
                        self.log(f"Error calling tool {tool_name}: {e}", Colors.RED)
                        import traceback
                        self.log(traceback.format_exc(), Colors.RED)
                        
                        # Add error result to messages
                        messages.append({
                            "role": "user",
                            "content": [
                                {
                                    "type": "tool_result",
                                    "tool_use_id": tool_id,
                                    "content": f"Error: {str(e)}"
                                }
                            ]
                        })
                        
                        # Continue conversation with error
                        response = self.anthropic.messages.create(
                            max_tokens=2024,
                            model=self.model_name,
                            tools=available_tools,
                            messages=messages
                        )
                        
                        if len(response.content) == 1 and response.content[0].type == "text":
                            process_query = False
        
        return pdb_result
    
    def start_mcp_server(self):
        """Verify the ESMfold MCP server is available and accessible."""
        if not self.esmfold_mcp_path or not os.path.exists(self.esmfold_mcp_path):
            self.log(f"ESMfold MCP server script not found at {self.esmfold_mcp_path}", Colors.RED)
            self.log(f"Current working directory: {os.getcwd()}", Colors.RED)
            self.log(f"Directory contents: {os.listdir('.')}", Colors.RED)
            return False
            
        self.log(f"VERIFYING ESMfold MCP server at {self.esmfold_mcp_path}...", Colors.BOLD + Colors.BLUE)
        
        # APPROACH 0: Try the official async approach if available
        if ASYNC_MCP_AVAILABLE and ANTHROPIC_CLIENT_AVAILABLE:
            self.log("Checking MCP server accessibility", Colors.BOLD + Colors.BLUE)
            
            # Validate the MCP server file
            try:
                with open(self.esmfold_mcp_path, 'r') as f:
                    server_code = f.read()
                    if "mcp.server" not in server_code or "fold_sequence" not in server_code:
                        self.log(f"WARNING: MCP server file may not be a valid MCP server: {self.esmfold_mcp_path}", Colors.YELLOW)
                    else:
                        self.log("MCP server file validation passed", Colors.GREEN)
            except Exception as e:
                self.log(f"Error reading MCP server file: {e}", Colors.RED)
            
            # Ensure required packages are installed
            try:
                import mcp
                from mcp.server import fastmcp
                self.log("Verified MCP server packages are installed", Colors.GREEN)
            except ImportError as e:
                self.log(f"Missing required MCP packages: {e}", Colors.RED)
                self.log("Please install with: pip install mcp", Colors.RED)
            
            # Check if fold_server.py needs dependencies
            try:
                import py3Dmol
                self.log("Verified py3Dmol is installed (required by fold_server.py)", Colors.GREEN)
            except ImportError:
                self.log("py3Dmol is not installed (required by fold_server.py)", Colors.YELLOW)
                self.log("Consider installing with: pip install py3Dmol", Colors.YELLOW)
            
            # Just verify connection without folding test sequence
            try:
                # Create test connection to verify server can be reached
                python_path = sys.executable
                server_params = StdioServerParameters(
                    command=python_path,
                    args=[self.esmfold_mcp_path],
                    env=os.environ.copy(),
                )
                
                # Check for connection instead of folding a sequence
                loop = asyncio.get_event_loop()
                async def test_connection():
                    self.log("Testing connection to MCP server...", Colors.BLUE)
                    async with stdio_client(server_params) as (read, write):
                        async with ClientSession(read, write) as session:
                            await asyncio.wait_for(session.initialize(), timeout=10.0)
                            response = await asyncio.wait_for(session.list_tools(), timeout=10.0)
                            tools = response.tools
                            tool_names = [tool.name for tool in tools]
                            if "fold_sequence" in tool_names:
                                self.log(f"MCP server offers the required 'fold_sequence' tool", Colors.GREEN)
                                return True
                            else:
                                self.log(f"ERROR: MCP server does not offer 'fold_sequence' tool", Colors.RED)
                                return False
                
                # Run the test connection function
                connection_success = loop.run_until_complete(test_connection())
                
                if connection_success:
                    self.log("MCP server verified and accessible!", Colors.GREEN)
                    return True
                else:
                    self.log("MCP server verification failed", Colors.RED)
                    return False
            except Exception as e:
                self.log(f"Error testing MCP server: {e}", Colors.RED)
                import traceback
                self.log(traceback.format_exc(), Colors.RED)
                return False
        
        # If we get here, we couldn't verify the server
        self.log("ERROR: Could not verify MCP server", Colors.BOLD + Colors.RED)
        return False
    
    def stop_mcp_server(self):
        """Clean up MCP resources."""
        # There's no persistent session to clean up anymore with our fresh connection approach
        self.log("No persistent MCP resources to clean up with fresh connection approach", Colors.BLUE)
        
        # Clean up server process if it exists (legacy code)
        if self.mcp_server_process:
            self.log("Stopping legacy MCP server process", Colors.BLUE)
            try:
                self.mcp_server_process.terminate()
                self.mcp_server_process.wait(timeout=5)
            except Exception as e:
                self.log(f"Error stopping server: {e}", Colors.RED)
                try:
                    self.mcp_server_process.kill()
                except:
                    pass
            self.mcp_server_process = None
    
    async def fold_with_fresh_connection(self, sequence: str) -> Optional[str]:
        """
        Create a fresh MCP connection, fold a sequence, and properly close the connection.
        This avoids reusing potentially closed connections.
        
        Args:
            sequence: Protein sequence to fold
            
        Returns:
            PDB text or None if failed
        """
        self.log(f"Creating fresh MCP connection to fold: {sequence[:10]}...", Colors.BLUE)
        
        try:
            # Create server parameters for stdio connection
            python_path = sys.executable
            self.log(f"Using Python executable: {python_path}", Colors.BLUE)
            
            server_params = StdioServerParameters(
                command=python_path,
                args=[self.esmfold_mcp_path],
                env=os.environ.copy(),
            )
            
            # Use a fresh connection with proper context management
            self.log("Establishing fresh MCP connection...", Colors.BLUE)
            async with stdio_client(server_params) as (read, write):
                self.log("Connection opened, initializing session...", Colors.BLUE)
                
                async with ClientSession(read, write) as session:
                    # Initialize the connection with timeout
                    self.log("Initializing MCP session...", Colors.BLUE)
                    await asyncio.wait_for(session.initialize(), timeout=10.0)
                    self.log("Session initialized successfully", Colors.GREEN)
                    
                    # List available tools
                    response = await asyncio.wait_for(session.list_tools(), timeout=10.0)
                    tools = response.tools
                    tool_names = [tool.name for tool in tools]
                    self.log(f"Available tools: {tool_names}", Colors.GREEN)
                    
                    # Verify fold_sequence tool is available
                    if "fold_sequence" not in tool_names:
                        self.log("fold_sequence tool not found", Colors.RED)
                        return None
                    
                    # Call the fold_sequence tool with timeout
                    self.log(f"Calling fold_sequence with sequence: {sequence[:10]}...", Colors.BLUE)
                    result = await asyncio.wait_for(
                        session.call_tool("fold_sequence", arguments={"sequence": sequence}),
                        timeout=60.0  # Longer timeout for actual folding
                    )
                    
                    if result and hasattr(result, 'content'):
                        pdb_text = result.content
                        self.log("Successfully received PDB from fold_sequence", Colors.GREEN)
                        pdb_preview = pdb_text[:50] + "..." if len(pdb_text) > 50 else pdb_text
                        self.log(f"PDB content preview: {pdb_preview}", Colors.GREEN)
                        return pdb_text
                    else:
                        self.log(f"No content received. Result: {result}", Colors.RED)
                        return None
        
        except asyncio.TimeoutError:
            self.log("Timeout error in MCP connection", Colors.RED)
            return None
        except Exception as e:
            self.log(f"Error in MCP connection: {e}", Colors.RED)
            import traceback
            self.log(traceback.format_exc(), Colors.RED)
            return None
    
    def fold_sequence_direct(self, sequence: str) -> Optional[str]:
        """Call the ESMfold API directly as a fallback."""
        self.log("Attempting direct call to ESMfold API (bypassing MCP)...", Colors.YELLOW)
        try:
            url = "https://api.esmatlas.com/foldSequence/v1/pdb/"
            self.log(f"Sending POST request to {url}", Colors.BLUE)
            response = requests.post(url, data=sequence, headers={"Content-Type": "text/plain"})
            
            if response.status_code == 200:
                self.log("ESMfold API direct call successful", Colors.GREEN)
                # Ensure we have PDB content
                pdb_text = response.text
                if "ATOM" in pdb_text and "HEADER" in pdb_text:
                    self.log("Valid PDB format received", Colors.GREEN)
                    return pdb_text
                else:
                    self.log(f"Response doesn't appear to be valid PDB format: {pdb_text[:100]}...", Colors.YELLOW)
                    return pdb_text  # Return anyway in case parsing is different
            else:
                self.log(f"ESMfold API returned status code {response.status_code}: {response.text}", Colors.RED)
                return None
        except Exception as e:
            self.log(f"Error in direct call to ESMfold API: {e}", Colors.RED)
            return None

    def predict_structure(self, sequence: str) -> Dict[str, Any]:
        """
        Call the ESMfold MCP server to predict protein structure.
        
        Args:
            sequence: Amino acid sequence
            
        Returns:
            Structure prediction result
        """
        sequence_preview = sequence[:10] + "..." if len(sequence) > 10 else sequence
        self.log(f"STRUCTURE PREDICTION for: {sequence_preview}", Colors.BOLD + Colors.RED)
        
        # Clean the sequence
        sequence = self.validate_and_clean_sequence(sequence)
        
        # Try direct fold with fresh connection
        try:
            # Create a fresh connection for each fold
            self.log("Attempting to fold with fresh MCP connection", Colors.BOLD + Colors.BLUE)
            loop = asyncio.get_event_loop()
            pdb_text = loop.run_until_complete(self.fold_with_fresh_connection(sequence))
            
            if pdb_text:
                self.log("SUCCESS: Successfully folded sequence using MCP!", Colors.GREEN)
                pdb_preview = pdb_text[:50] + "..." if len(pdb_text) > 50 else pdb_text
                self.log(f"PDB text (preview): {pdb_preview}", Colors.GREEN)
                
                # Check if the PDB text looks valid
                if "ATOM" in pdb_text and "HEADER" in pdb_text:
                    self.log("PDB format validation passed", Colors.GREEN)
                else:
                    self.log("WARNING: PDB text doesn't contain expected ATOM/HEADER markers", Colors.YELLOW)
                
                # Generate visualization URL (placeholder)
                viz_url = f"https://example.com/viz/{self.current_iteration}.png"
                
                return {
                    "sequence": sequence,
                    "pdb_text": pdb_text,
                    "confidence": 0.9,  # High confidence with official method
                    "visualization_url": viz_url
                }
        except Exception as e:
            self.log(f"Error in MCP fold attempt: {e}", Colors.RED)
            import traceback
            self.log(traceback.format_exc(), Colors.RED)
        
        # Try through Claude as another approach if direct approach failed
        if self.anthropic:
            try:
                self.log("ATTEMPT 2: Going through Claude to call the MCP tool", Colors.BLUE)
                query = f"Please fold this protein sequence using the fold_sequence tool."
                loop = asyncio.get_event_loop()
                pdb_text = loop.run_until_complete(self.process_query(query, sequence))
                
                if pdb_text:
                    self.log("SUCCESS: Successfully folded sequence through Claude!", Colors.GREEN)
                    pdb_preview = pdb_text[:50] + "..." if len(pdb_text) > 50 else pdb_text
                    self.log(f"PDB text (preview): {pdb_preview}", Colors.GREEN)
                    
                    # Generate visualization URL (placeholder)
                    viz_url = f"https://example.com/viz/{self.current_iteration}.png"
                    
                    return {
                        "sequence": sequence,
                        "pdb_text": pdb_text,
                        "confidence": 0.85,
                        "visualization_url": viz_url
                    }
            except Exception as e:
                self.log(f"Error in Claude-based fold attempt: {e}", Colors.RED)
                import traceback
                self.log(traceback.format_exc(), Colors.RED)
        
        # Fall back to direct ESMfold API call
        self.log("FALLBACK: Using direct ESMfold API call", Colors.YELLOW)
        pdb_text = self.fold_sequence_direct(sequence)
        
        if pdb_text:
            self.log("Successfully folded sequence using direct ESMfold API", Colors.GREEN)
            pdb_preview = pdb_text[:50] + "..." if len(pdb_text) > 50 else pdb_text
            self.log(f"PDB text (preview): {pdb_preview}", Colors.GREEN)
            
            # Generate visualization URL (placeholder)
            viz_url = f"https://example.com/viz/{self.current_iteration}.png"
            
            return {
                "sequence": sequence,
                "pdb_text": pdb_text,
                "confidence": 0.8,  # Good confidence with direct API
                "visualization_url": viz_url
            }
        
        # If all methods failed, use placeholder
        self.log("All folding methods failed, using placeholder", Colors.RED)
        return {
            "sequence": sequence,
            "pdb_text": "HEADER\nREMARK PLACEHOLDER PDB - ALL FOLDING METHODS FAILED\nATOM      1  N   ALA A   1       0.000   0.000   0.000  1.00  0.00           N",
            "confidence": 0.1,  # Very low confidence for placeholder
            "visualization_url": f"https://example.com/viz/{self.current_iteration}.png",
            "error": "Failed to fold sequence with all available methods"
        }
    
    def query_llm(self, prompt: str, include_history: bool = True) -> str:
        """
        Query the LLM with a prompt and optional conversation history.
        
        Args:
            prompt: The prompt to send to the LLM
            include_history: Whether to include conversation history
            
        Returns:
            LLM response text
        """
        if not self.llm_api_key:
            self.log("Error: LLM API key is required for this agent to function", Colors.RED)
            return "Error: No API key provided"
        
        # Print a clear separator
        print("\n" + "-"*80)
        self.log("SENDING REQUEST TO LLM API", Colors.RED)
        
        # Log the entire prompt without truncation
        self.log(f"Prompt: {prompt}", Colors.YELLOW)
        
        # Use Anthropic client if available
        if self.anthropic:
            self.log("Using Anthropic client library", Colors.BLUE)
            
            # Combine conversation history if requested
            messages = []
            if include_history and self.conversation_history:
                for msg in self.conversation_history:
                    if isinstance(msg, dict) and 'role' in msg and 'content' in msg:
                        messages.append(msg)
            
            # Add the current prompt
            messages.append({"role": "user", "content": prompt})
            
            try:
                # Make API call
                self.log("Making API call to Claude...", Colors.RED)
                
                response = self.anthropic.messages.create(
                    model=self.model_name,
                    max_tokens=4000,
                    messages=messages,
                    system="You are a protein design expert agent tasked with designing novel proteins for specific purposes."
                )
                
                # Extract response text
                if response and response.content:
                    llm_response = response.content[0].text
                    
                    # Add to conversation history
                    self.conversation_history.append({"role": "user", "content": prompt})
                    self.conversation_history.append({"role": "assistant", "content": llm_response})
                    
                    # Log the entire response without truncation
                    self.log(f"Received response: {llm_response}", Colors.GREEN)
                    print("-"*80 + "\n")
                    
                    return llm_response
                else:
                    self.log("Empty response from Claude", Colors.RED)
                    return "Error: Empty response"
            except Exception as e:
                self.log(f"Error querying LLM with Anthropic client: {e}", Colors.RED)
                self.log("Falling back to direct API call", Colors.YELLOW)
        
        # Fall back to direct API call
        self.log("Using direct API call to Claude", Colors.YELLOW)
        
        # Start with system prompt
        system_prompt = """
        You are a protein design expert agent tasked with designing novel proteins for specific purposes.
        You have access to protein folding models (AlphaFold/ESMFold) through MCP servers.
        
        Your goal is to design optimal protein sequences, continuously refining your approach based on feedback.
        Maintain a memory of your findings, strategies that worked or didn't work, and learnings from literature.
        
        For each step:
        1. Clearly state your reasoning
        2. Make a decision about what to do next
        3. If needed, generate specific amino acid sequences in standard one-letter code (ACDEFGHIKLMNPQRSTVWY)
        
        Remember previous protein designs, their predicted structures, binding scores, and what you've learned.
        """
        
        # Combine conversation history if requested
        messages = []
        if include_history and self.conversation_history:
            messages = self.conversation_history.copy()
        
        # Add the current prompt
        messages.append({"role": "user", "content": prompt})
        
        # Make API call
        headers = {
            "x-api-key": self.llm_api_key,
            "content-type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        payload = {
            "model": self.model_name,
            "max_tokens": 4000,
            "messages": messages,
            "system": system_prompt
        }
        
        try:
            self.log("Making API call to Claude...", Colors.RED)
            response = requests.post(self.llm_api_url, headers=headers, json=payload)
            response.raise_for_status()
            response_data = response.json()
            llm_response = response_data["content"][0]["text"]
            
            # Add to conversation history
            self.conversation_history.append({"role": "user", "content": prompt})
            self.conversation_history.append({"role": "assistant", "content": llm_response})
            
            # Log the entire response without truncation
            self.log(f"Received response: {llm_response}", Colors.GREEN)
            print("-"*80 + "\n")
            
            return llm_response
        except Exception as e:
            self.log(f"Error querying LLM: {e}", Colors.RED)
            return f"Error: {str(e)}"
    
    def predict_binding(self, sequence: str, target: str) -> float:
        """
        Call the MCP server to predict binding affinity to target protein.
        
        Args:
            sequence: Amino acid sequence
            target: Target protein name
            
        Returns:
            Binding affinity score
        """
        sequence_preview = sequence[:10] + "..." if len(sequence) > 10 else sequence
        self.log(f"BINDING PREDICTION for: {sequence_preview} to {target}", Colors.RED)
        
        # Placeholder for actual MCP call
        # In a real implementation, this would call the MCP server
        self.log("Simulating binding prediction (MCP server call)", Colors.RED)
        
        # Simulate a binding score
        binding_score = 0.5 + (self.current_iteration * 0.05)  # Fake improvement over iterations
        
        self.log(f"Binding prediction complete, score: {binding_score:.2f}", Colors.GREEN)
        return binding_score
    
    def run(self, user_prompt: str) -> Dict[str, Any]:
        """
        Main method to run the protein design process.
        
        Args:
            user_prompt: The user's request, e.g., "Design a 50‑aa stapled α‑helix that binds MDM2"
            
        Returns:
            Results of the protein design process
        """
        try:
            self.log(f"Starting protein design process for: {user_prompt}", Colors.BLUE)
            
            # Start MCP server and client
            server_started = self.start_mcp_server()
            if not server_started:
                self.log("Warning: MCP server initialization failed", Colors.RED)
                self.log("Will use ESMfold API calls as fallback", Colors.YELLOW)
            
            # Initialize a new session
            self.conversation_history = []
            self.current_iteration = 0
            self.best_sequence = None
            self.best_score = float('-inf')
            
            # Step 1: Initial planning
            self.log(f"STARTING INITIAL PLANNING", Colors.BLUE)
            initial_prompt = f"""
            I need your help with this protein design task: "{user_prompt}"
            
            First, analyze this request and create a plan:
            1. What are the key requirements and constraints?
            2. What approach will you take to design this protein?
            3. What information do you need to search for in literature?
            4. What initial sequences would you propose to test?
            
            Please generate 2-3 initial amino acid sequences that meet these requirements.
            For each sequence, explain your design rationale.
            """
            
            planning_response = self.query_llm(initial_prompt, include_history=False)
            self.log("Initial planning complete", Colors.BLUE)
            
            # Extract sequences from the response using the LLM
            self.log("Requesting specific sequence format from LLM", Colors.BLUE)
            extract_prompt = """
            Based on your previous response, I need the sequences in a very specific format.
            
            Please provide ONLY the amino acid sequences using one-letter codes (ACDEFGHIKLMNPQRSTVWY).
            Format each sequence on its own line with NO additional text, numbers, or formatting.
            
            Example of the exact format I need:
            MAAKLVQAGKAAIALLKLLLKKR
            WTAVKIYGRPYPIEWGN
            DEFGHIKLM
            
            Please extract and format ONLY the sequences from your previous response exactly as shown above.
            """
            
            sequences_response = self.query_llm(extract_prompt)
            
            # Extract sequences - much simpler now, just get non-empty lines
            sequences = []
            for line in sequences_response.split("\n"):
                cleaned_line = line.strip()
                # Skip empty lines and lines that are clearly not sequences
                if cleaned_line and not cleaned_line.startswith(">") and not cleaned_line.startswith("#"):
                    # Only keep valid amino acid characters
                    valid_sequence = ''.join(c for c in cleaned_line.upper() if c in "ACDEFGHIKLMNPQRSTVWY")
                    if valid_sequence and len(valid_sequence) >= 10:  # Minimum length check
                        sequences.append(valid_sequence)
            
            if not sequences:
                # Fallback in case no sequences were found
                self.log("No valid sequences found in LLM response, using placeholder", Colors.YELLOW)
                self.log("Here was the response:\n" + sequences_response, Colors.YELLOW)
                sequences = ["ALELAELALELAELALELAELALELAELALELAELALELAELALELAEL"]
            else:
                self.log(f"Successfully extracted {len(sequences)} sequences", Colors.GREEN)
                for i, seq in enumerate(sequences):
                    self.log(f"Sequence {i+1}: {seq}", Colors.GREEN)
            
            # Initialize results tracking
            results = {
                "session_id": self.session_id,
                "prompt": user_prompt,
                "iterations": [],
                "final_sequence": None,
                "final_binding_score": None,
                "final_structure": None,
                "rationale": None
            }
            
            # Modified to run just 1 iteration and process only the first sequence
            max_iterations = 1  # Just 1 iteration
            for iteration in range(max_iterations):
                self.current_iteration = iteration + 1
                self.log(f"STARTING ITERATION {self.current_iteration}/{max_iterations}", Colors.BOLD + Colors.BLUE)
                
                # Check if user wants to stop
                try:
                    user_input = input(f"{Colors.CYAN}Press Enter to continue to iteration {self.current_iteration}, or type 'stop' to end: {Colors.END}")
                    if user_input.lower() == 'stop':
                        self.log("Process stopped by user", Colors.YELLOW)
                        break
                except KeyboardInterrupt:
                    self.log("Process interrupted by user", Colors.YELLOW)
                    break
                    
                iteration_results = {
                    "iteration": self.current_iteration,
                    "sequences": [],
                    "structures": [],
                    "binding_scores": [],
                    "best_sequence": None,
                    "best_score": None
                }
                
                # Process only the first sequence to minimize MCP requests
                if sequences:
                    sequence = sequences[0]
                    self.log(f"Processing sequence: {sequence[:20]}...", Colors.BLUE)
                    
                    # Predict structure - this makes one MCP request
                    structure = self.predict_structure(sequence)
                    
                    # Extract target from prompt
                    target = "MDM2"  # Default/placeholder - in real implementation we'd extract this properly
                    if "binds" in user_prompt.lower():
                        parts = user_prompt.lower().split("binds")
                        if len(parts) > 1:
                            target = parts[1].strip()
                    
                    # Predict binding
                    binding_score = self.predict_binding(sequence, target)
                    
                    # Track results
                    iteration_results["sequences"].append(sequence)
                    iteration_results["structures"].append(structure)
                    iteration_results["binding_scores"].append(binding_score)
                    
                    # Update best sequence if this is better
                    if binding_score > self.best_score:
                        self.best_sequence = sequence
                        self.best_score = binding_score
                        
                    # Log results
                    self.log(f"Sequence: binding score = {binding_score:.2f}", Colors.GREEN)
                
                # Update iteration best
                if iteration_results["binding_scores"]:
                    best_idx = iteration_results["binding_scores"].index(max(iteration_results["binding_scores"]))
                    iteration_results["best_sequence"] = iteration_results["sequences"][best_idx]
                    iteration_results["best_score"] = iteration_results["binding_scores"][best_idx]
                
                # Add to results
                results["iterations"].append(iteration_results)
                
                # Skip generation of new sequences since we only do one iteration
            
            # Final results
            results["final_sequence"] = self.best_sequence
            results["final_binding_score"] = self.best_score
            
            # Get final analysis from LLM
            final_prompt = f"""
            I've completed the protein design process for the task: "{user_prompt}"
            
            Final results:
            - Best sequence: {self.best_sequence}
            - Best binding score: {self.best_score:.2f}
            
            Please provide:
            1. A summary of the design process and what we learned
            2. An analysis of the final sequence and why it's effective
            3. Suggestions for further optimization if we were to continue
            4. Any limitations or considerations for experimental validation
            """
            
            final_analysis = self.query_llm(final_prompt)
            results["rationale"] = final_analysis
            
            self.log("Protein design process complete", Colors.GREEN)
            return results
        finally:
            # Clean up resources
            self.stop_mcp_server()


# Example usage
if __name__ == "__main__":
    # Display cool ASCII art banner
    print("""
  _____           _         _____            
 |  __ \         | |       / ____|           
 | |__) | __ ___ | |_ ___ | |  __  ___ _ __  
 |  ___/ '__/ _ \| __/ _ \| | |_ |/ _ \ '_ \ 
 | |   | | | (_) | || (_) | |__| |  __/ | | |
 |_|   |_|  \___/ \__\___/ \_____|\___|_| |_|
                                             
    """)
    print("🧬 Welcome to ProtoGen - Protein Design Agent\n")
    
    import argparse
    
    # Set up argument parser
    parser = argparse.ArgumentParser(description='ProtoGen: AI-powered protein design agent')
    parser.add_argument('--prompt', type=str, help='Design prompt (e.g., "Design a 50‑aa stapled α‑helix that binds MDM2")')
    args = parser.parse_args()
    
    # Get design prompt from arguments or user input
    if args.prompt:
        prompt = args.prompt
    else:
        prompt = input("🔍 Enter your protein design prompt (e.g., 'Design a 50‑aa stapled α‑helix that binds MDM2'): ")
    
    # Check for required packages
    if not ASYNC_MCP_AVAILABLE:
        print("\n❌ MCP library not found. Please install it with:")
        print("   pip install mcp")
    else:
        print("✅ MCP library found")
    
    if not ANTHROPIC_CLIENT_AVAILABLE:
        print("\n❌ Anthropic client not found. Please install it with:")
        print("   pip install anthropic")
    else:
        print("✅ Anthropic client found")
    
    if not nest_asyncio:
        print("\n❌ nest_asyncio not found. Please install it with:")
        print("   pip install nest-asyncio")
    else:
        print("✅ nest_asyncio found")
    
    # Get API key from environment or prompt user
    llm_api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not llm_api_key:
        llm_api_key = input("🔑 Enter your Anthropic API key (or set ANTHROPIC_API_KEY environment variable): ")
    else:
        print("✅ Found Anthropic API key in environment")
    
    print("\n🚀 Starting protein design process...")
    
    # Create the agent
    agent = ProteinDesignAgent(
        esmfold_mcp_path="fold_server.py",
        llm_api_key=llm_api_key,
        verbose=True
    )
    
    # Run the agent
    results = agent.run(prompt)
    
    # Display results summary
    print("\n✨ === DESIGN RESULTS === ✨")
    print(f"🧬 Best sequence: {results['final_sequence']}")
    print(f"📊 Binding score: {results['final_binding_score']:.2f}")
    print("\n📝 === RATIONALE === 📝")
    print(results["rationale"])
