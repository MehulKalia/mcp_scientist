import os
import requests
import json
import time
import asyncio
import aiohttp
import logging
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, AsyncGenerator
import uuid
from dotenv import load_dotenv
from mocks import mock_structure_prediction, mock_binding_prediction, mock_mutate_sequence
import re

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f'agent_logs_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger(__name__)

load_dotenv()

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

class AgentError(Exception):
    """Base exception for agent errors"""
    pass

class APIKeyError(AgentError):
    """Raised when API key is missing or invalid"""
    pass

class PredictionError(AgentError):
    """Raised when prediction fails"""
    pass

class ProteinDesignAgent:
    def __init__(
        self,
        alphafold_mcp_url: str = "http://localhost:8000",
        esmfold_mcp_url: Optional[str] = None,
        llm_api_key: Optional[str] = os.environ.get("ANTHROPIC_API_KEY"),
        llm_api_url: str = "https://api.anthropic.com/v1/messages",
        verbose: bool = True
    ):
        """
        Initialize the protein design agent.
        
        Args:
            alphafold_mcp_url: URL of the AlphaFold MCP server
            esmfold_mcp_url: URL of the ESMFold MCP server (optional)
            llm_api_key: API key for the LLM service (Claude)
            llm_api_url: URL for the LLM API
            verbose: Whether to print detailed logs
        """
        logger.info("Initializing ProteinDesignAgent")
        self.alphafold_mcp_url = alphafold_mcp_url
        self.esmfold_mcp_url = esmfold_mcp_url
        self.llm_api_key = llm_api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.llm_api_url = llm_api_url
        self.verbose = verbose
        self.session_id = str(uuid.uuid4())
        
        logger.debug(f"Session ID: {self.session_id}")
        logger.debug(f"AlphaFold MCP URL: {self.alphafold_mcp_url}")
        logger.debug(f"ESMFold MCP URL: {self.esmfold_mcp_url}")
        
        # Initialize conversation history
        self.conversation_history = []
        
        # Initialize basic session info
        self.current_iteration = 0
        self.best_sequence = None
        self.best_score = float('-inf')
        self.max_iterations = 3
        self.should_stop = False
        
        logger.info("ProteinDesignAgent initialized successfully")
        
    def log(self, message: str, color: Optional[str] = None) -> None:
        """Log a message if verbose mode is enabled."""
        if self.verbose:
            if color:
                logger.debug(f"{color}[ProteinDesignAgent] {message}{Colors.END}")
            else:
                logger.debug(f"[ProteinDesignAgent] {message}")
    
    def query_llm(self, prompt: str, include_history: bool = True) -> str:
        """
        Query the LLM with a prompt and optional conversation history.
        
        Args:
            prompt: The prompt to send to the LLM
            include_history: Whether to include conversation history
            
        Returns:
            LLM response text
        """
        logger.info("Querying LLM")
        if not self.llm_api_key:
            logger.error("LLM API key is missing")
            return "Error: No API key provided"
        
        # Print a clear separator
        print("\n" + "-"*80)
        self.log("SENDING REQUEST TO LLM API", Colors.RED)
        
        # Log the entire prompt without truncation
        self.log(f"Prompt: {prompt}", Colors.YELLOW)
        
        # Start with system prompt
        system_prompt = self.get_system_prompt()
        logger.debug(f"System prompt: {system_prompt}")
        
        # Combine conversation history if requested
        messages = []
        if include_history and self.conversation_history:
            messages = self.conversation_history.copy()
            logger.debug(f"Using {len(messages)} messages from history")
        
        # Add the current prompt
        messages.append({"role": "user", "content": prompt})
        
        # Make API call
        self.log(f"Making API call to Claude...", Colors.RED)
        
        headers = {
            "x-api-key": self.llm_api_key,
            "content-type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        payload = {
            "model": "claude-3-opus-20240229",
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
            logger.error(f"Error querying LLM: {str(e)}", exc_info=True)
            return f"Error: {str(e)}"
    
    def predict_structure(self, sequence: str) -> Dict[str, Any]:
        """
        Call the AlphaFold/ESMFold MCP server to predict protein structure.
        
        Args:
            sequence: Amino acid sequence
            
        Returns:
            Structure prediction result
        """
        logger.info(f"Predicting structure for sequence: {sequence[:10]}...")
        
        sequence_preview = sequence[:10] + "..." if len(sequence) > 10 else sequence
        self.log(f"STRUCTURE PREDICTION for: {sequence_preview}", Colors.RED)
        
        try:
            # Placeholder for actual MCP call
            logger.debug("Simulating structure prediction")
            
            # Simulate a structure prediction result
            structure_result = {
                "sequence": sequence,
                "pdb_url": f"https://example.com/pdb/{self.current_iteration}.pdb",
                "confidence": 0.8,
                "visualization_url": f"https://example.com/viz/{self.current_iteration}.png"
            }
            
            self.log(f"Structure prediction complete with confidence: {structure_result['confidence']}", Colors.GREEN)
            logger.debug(f"Structure result: {structure_result}")
            return structure_result
        except Exception as e:
            logger.error(f"Error in structure prediction: {str(e)}", exc_info=True)
            raise PredictionError(f"Structure prediction failed: {str(e)}")
    
    def predict_binding(self, sequence: str, target: str) -> float:
        """
        Call the MCP server to predict binding affinity to target protein.
        
        Args:
            sequence: Amino acid sequence
            target: Target protein name
            
        Returns:
            Binding affinity score
        """
        logger.info(f"Predicting binding for sequence: {sequence[:10]}... with target: {target}")
        
        sequence_preview = sequence[:10] + "..." if len(sequence) > 10 else sequence
        self.log(f"BINDING PREDICTION for: {sequence_preview} to {target}", Colors.RED)
        
        try:
            # Placeholder for actual MCP call
            logger.debug("Simulating binding prediction")
            
            # Simulate a binding score
            binding_score = 0.5 + (self.current_iteration * 0.05)  # Fake improvement over iterations
            
            self.log(f"Binding prediction complete, score: {binding_score:.2f}", Colors.GREEN)
            logger.info(f"Binding prediction complete with score: {binding_score}")
            return binding_score
        except Exception as e:
            logger.error(f"Error in binding prediction: {str(e)}", exc_info=True)
            raise PredictionError(f"Binding prediction failed: {str(e)}")
    
    def run(self, user_prompt: str) -> Dict[str, Any]:
        """
        Main method to run the protein design process.
        
        Args:
            user_prompt: The user's request, e.g., "Design a 50‑aa stapled α‑helix that binds MDM2"
            
        Returns:
            Results of the protein design process
        """
        self.log(f"Starting protein design process for: {user_prompt}", Colors.BLUE)
        
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
        
        # Iterative refinement loop
        for iteration in range(self.max_iterations):
            self.current_iteration = iteration + 1
            self.log(f"STARTING ITERATION {self.current_iteration}/{self.max_iterations}", Colors.BOLD + Colors.BLUE)
            
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
            
            # Evaluate each sequence
            for i, sequence in enumerate(sequences):
                # Predict structure
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
                self.log(f"Sequence {i+1}: binding score = {binding_score:.2f}", Colors.GREEN)
            
            # Update iteration best
            if iteration_results["binding_scores"]:
                best_idx = iteration_results["binding_scores"].index(max(iteration_results["binding_scores"]))
                iteration_results["best_sequence"] = iteration_results["sequences"][best_idx]
                iteration_results["best_score"] = iteration_results["binding_scores"][best_idx]
            
            # Add to results
            results["iterations"].append(iteration_results)
            
            # Generate status report for LLM
            status_prompt = f"""
            I've completed iteration {self.current_iteration} of the protein design process.
            
            Results:
            - Sequences tested: {len(iteration_results["sequences"])}
            - Best binding score: {self.best_score:.2f}
            - Best sequence so far: {self.best_sequence}
            
            Based on these results, please:
            1. Analyze what's working and what could be improved
            2. Suggest refinements to make for the next iteration
            3. Generate {len(sequences)} new refined sequences that might perform better
            
            Remember that the goal is to {user_prompt}
            """
            
            # Get LLM's analysis and refined sequences
            refinement_response = self.query_llm(status_prompt)
            
            # Extract new sequences from LLM response
            extract_prompt = """
            Based on your previous response, I need the refined sequences in a very specific format.
            
            Please provide ONLY the amino acid sequences using one-letter codes (ACDEFGHIKLMNPQRSTVWY).
            Format each sequence on its own line with NO additional text, numbers, or formatting.
            
            Example of the exact format I need:
            MAAKLVQAGKAAIALLKLLLKKR
            WTAVKIYGRPYPIEWGN
            DEFGHIKLM
            
            Please extract and format ONLY the sequences from your previous response exactly as shown above.
            """
            
            new_sequences_response = self.query_llm(extract_prompt)
            
            # Extract sequences - much simpler now
            new_sequences = []
            for line in new_sequences_response.split("\n"):
                cleaned_line = line.strip()
                # Skip empty lines and lines that are clearly not sequences
                if cleaned_line and not cleaned_line.startswith(">") and not cleaned_line.startswith("#"):
                    # Only keep valid amino acid characters
                    valid_sequence = ''.join(c for c in cleaned_line.upper() if c in "ACDEFGHIKLMNPQRSTVWY")
                    if valid_sequence and len(valid_sequence) >= 10:  # Minimum length check
                        new_sequences.append(valid_sequence)
            
            if new_sequences:
                self.log(f"Successfully extracted {len(new_sequences)} refined sequences", Colors.GREEN)
                for i, seq in enumerate(new_sequences):
                    self.log(f"Refined sequence {i+1}: {seq}", Colors.GREEN)
                sequences = new_sequences
            else:
                # Fallback - modify the best sequence slightly
                self.log("No valid sequences found in LLM response, using simple modification", Colors.YELLOW)
                best_seq = list(self.best_sequence)
                for i in range(len(best_seq)):
                    if i % 7 == 0 and i > 0 and i < len(best_seq) - 1:
                        best_seq[i] = 'K' if best_seq[i] != 'K' else 'R'
                sequences = [''.join(best_seq)]
        
        # Final results
        results["final_sequence"] = self.best_sequence
        results["final_binding_score"] = self.best_score
        
        # Get final analysis from LLM
        final_prompt = f"""
        I've completed all {self.max_iterations} iterations of the protein design process for the task: "{user_prompt}"
        
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

    async def process_request(self, config: Dict[str, Any]) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Process a protein design request asynchronously.
        
        Args:
            config: Configuration dictionary containing parameters like maxIterations
            
        Yields:
            Dictionary containing status updates and results
        """
        logger.info("Starting protein design process")
        logger.debug(f"Configuration: {config}")
        
        self.max_iterations = config.get("maxIterations", 3)
        self.should_stop = False
        
        try:
            # Initial planning
            logger.info("Sending initial status update")
            yield {
                "type": "status",
                "content": "Starting protein design process...",
                "data": {
                    "stage": "initialization",
                    "status": "in_progress"
                }
            }
            
            # Initial planning with LLM
            logger.info("Starting initial planning with LLM")
            initial_prompt = """
            I need your help with this protein design task: "Design a 50‑aa stapled α‑helix that binds MDM2"
            
            First, analyze this request and create a plan:
            1. What are the key requirements and constraints?
            2. What approach will you take to design this protein?
            3. What information do you need to search for in literature?
            4. What initial sequences would you propose to test?
            
            Please generate 2-3 initial amino acid sequences that meet these requirements.
            For each sequence, explain your design rationale.
            """
            
            yield {
                "type": "prompt",
                "content": initial_prompt,
                "data": {
                    "stage": "planning",
                    "prompt_type": "initial_planning"
                }
            }
            
            planning_response = await self.query_llm_async(initial_prompt, include_history=False)
            yield {
                "type": "response",
                "content": planning_response,
                "data": {
                    "stage": "planning",
                    "response_type": "initial_planning"
                }
            }
            
            # Extract sequences from the response
            logger.info("Extracting initial sequences")
            sequences = self.extract_sequences(planning_response)
            if not sequences:
                logger.warning("No sequences found in initial response, using default")
                sequences = ["ALELAELALELAELALELAELALELAELALELAELALELAELALELAEL"]
            
            logger.info(f"Starting with {len(sequences)} sequences")
            
            # Iterative refinement loop
            while self.current_iteration < self.max_iterations and not self.should_stop:
                self.current_iteration += 1
                logger.info(f"Starting iteration {self.current_iteration}/{self.max_iterations}")
                
                # Yield iteration start message
                yield {
                    "type": "iteration",
                    "content": f"Starting iteration {self.current_iteration}/{self.max_iterations}",
                    "data": {
                        "iteration": self.current_iteration,
                        "total_iterations": self.max_iterations,
                        "status": "in_progress"
                    }
                }
                
                if self.should_stop:
                    logger.info("Process stopped by user request")
                    yield {
                        "type": "status",
                        "content": "Agent process stopped by user request.",
                        "data": {
                            "status": "stopped",
                            "iteration": self.current_iteration
                        }
                    }
                    break
                
                # Evaluate each sequence
                iteration_results = []
                for sequence in sequences:
                    # Predict structure
                    structure = self.predict_structure(sequence)
                    
                    # Predict binding
                    binding_score = self.predict_binding(sequence, "MDM2")
                    
                    # Track results
                    iteration_results.append({
                        "sequence": sequence,
                        "structure": structure,
                        "binding_score": binding_score
                    })
                    
                    # Update best sequence if this is better
                    if binding_score > self.best_score:
                        self.best_sequence = sequence
                        self.best_score = binding_score
                
                # Yield iteration results
                yield {
                    "type": "iteration_results",
                    "content": f"Completed iteration {self.current_iteration}",
                    "data": {
                        "iteration": self.current_iteration,
                        "results": iteration_results,
                        "best_sequence": self.best_sequence,
                        "best_score": self.best_score
                    }
                }
                
                # Generate status report for LLM
                status_prompt = f"""
                I've completed iteration {self.current_iteration} of the protein design process.
                
                Results:
                - Sequences tested: {len(sequences)}
                - Best binding score: {self.best_score:.2f}
                - Best sequence so far: {self.best_sequence}
                
                Based on these results, please:
                1. Analyze what's working and what could be improved
                2. Suggest refinements to make for the next iteration
                3. Generate {len(sequences)} new refined sequences that might perform better
                
                Remember that the goal is to design a 50‑aa stapled α‑helix that binds MDM2
                """
                
                yield {
                    "type": "prompt",
                    "content": status_prompt,
                    "data": {
                        "stage": "refinement",
                        "prompt_type": "iteration_analysis",
                        "iteration": self.current_iteration
                    }
                }
                
                # Get LLM's analysis and refined sequences
                refinement_response = await self.query_llm_async(status_prompt)
                yield {
                    "type": "response",
                    "content": refinement_response,
                    "data": {
                        "stage": "refinement",
                        "response_type": "iteration_analysis",
                        "iteration": self.current_iteration
                    }
                }
                
                # Extract new sequences
                new_sequences = self.extract_sequences(refinement_response)
                if new_sequences:
                    sequences = new_sequences
                    logger.info(f"Using {len(sequences)} new sequences for next iteration")
                else:
                    logger.warning("No new sequences found, keeping current sequences")
                
                # After each iteration, yield the current best results
                if self.best_sequence and self.best_score is not None:
                    logger.info("Yielding current best results")
                    yield {
                        "type": "design_results",
                        "content": "=== DESIGN RESULTS ===",
                        "data": {
                            "sequence": self.best_sequence,
                            "binding_score": self.best_score,
                            "iteration": self.current_iteration,
                            "rationale": self.get_current_rationale()
                        }
                    }
                
        except Exception as e:
            logger.error(f"Error in process_request: {str(e)}", exc_info=True)
            yield {
                "type": "error",
                "content": f"Error: {str(e)}",
                "data": {
                    "error_type": type(e).__name__,
                    "error_details": str(e)
                }
            }
        finally:
            # Cleanup
            logger.info("Cleaning up process_request state")
            self.current_iteration = 0
            self.should_stop = False

    def get_current_rationale(self) -> str:
        """Get the current design rationale based on the best sequence"""
        logger.debug("Generating current rationale")
        if not self.best_sequence:
            logger.warning("No best sequence available for rationale")
            return "No design rationale available yet."
            
        rationale = f"""Current Design Analysis:

1. Best Sequence: {self.best_sequence}
2. Binding Score: {self.best_score:.2f}
3. Iteration: {self.current_iteration}/{self.max_iterations}

Design Strategy:
- Focused on optimizing binding affinity
- Iteratively refined sequence based on structural predictions
- Maintained key functional residues while exploring variations

Next Steps:
- Consider additional mutations for improved binding
- Evaluate structural stability
- Plan experimental validation"""

        logger.debug(f"Generated rationale: {rationale}")
        return rationale

    async def query_llm_async(self, prompt: str, include_history: bool = True) -> str:
        """Async version of query_llm"""
        logger.info("Querying LLM asynchronously")
        if not self.llm_api_key:
            logger.error("LLM API key is missing")
            raise APIKeyError("LLM API key is required for this agent to function")
        
        messages = []
        if include_history and self.conversation_history:
            messages = self.conversation_history.copy()
            logger.debug(f"Using {len(messages)} messages from history")
        
        messages.append({"role": "user", "content": prompt})
        
        headers = {
            "x-api-key": self.llm_api_key,
            "content-type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        payload = {
            "model": "claude-3-opus-20240229",
            "max_tokens": 4000,
            "messages": messages,
            "system": self.get_system_prompt()
        }
        
        try:
            logger.debug("Making async API call to Claude")
            async with aiohttp.ClientSession() as session:
                async with session.post(self.llm_api_url, headers=headers, json=payload) as response:
                    response.raise_for_status()
                    response_data = await response.json()
                    llm_response = response_data["content"][0]["text"]
                    
                    self.conversation_history.append({"role": "user", "content": prompt})
                    self.conversation_history.append({"role": "assistant", "content": llm_response})
                    
                    logger.debug(f"Received async response: {llm_response}")
                    logger.info("Async LLM query completed successfully")
                    
                    return llm_response
        except Exception as e:
            logger.error(f"Error in async LLM query: {str(e)}", exc_info=True)
            raise PredictionError(f"Error querying LLM: {str(e)}")

    def extract_sequences(self, text: str) -> List[str]:
        """Extract amino acid sequences from text using a strict regex."""
        logger.debug(f"Extracting sequences from text (first 100 chars): {text[:100]}...")
        sequences = []
        # Regex to match lines consisting only of amino acid characters (A-Y, excluding B, J, O, U, X, Z)
        # Ensure the matched string is at least 10 characters long
        sequence_regex = re.compile(r"^[ACDEFGHIKLMNPQRSTVWY]{10,}$", re.MULTILINE)

        found_sequences = sequence_regex.findall(text.strip())

        sequences.extend(found_sequences)

        logger.debug(f"Extracted {len(sequences)} sequences: {sequences}")
        return sequences

    def extract_target(self, prompt: str) -> str:
        """Extract target protein from prompt"""
        logger.debug(f"Extracting target from prompt: {prompt}")
        if "binds" in prompt.lower():
            parts = prompt.lower().split("binds")
            if len(parts) > 1:
                target = parts[1].strip()
                logger.debug(f"Extracted target: {target}")
                return target
        logger.debug("Using default target: MDM2")
        return "MDM2"  # Default target

    def get_system_prompt(self) -> str:
        """Get the system prompt for the LLM"""
        logger.debug("Getting system prompt")
        return """
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

# Example usage
if __name__ == "__main__":
    # Example prompt
    prompt = "Design a 50‑aa stapled α‑helix that binds MDM2"
    
    # Get API key from environment or set directly
    llm_api_key = os.environ.get("ANTHROPIC_API_KEY")
    
    # Create the agent
    agent = ProteinDesignAgent(
        alphafold_mcp_url="http://localhost:8000",
        llm_api_key=llm_api_key,
        verbose=True
    )
    
    # Run the agent
    results = agent.run(prompt)
    
    # Display results summary
    print("\n=== DESIGN RESULTS ===")
    print(f"Best sequence: {results['final_sequence']}")
    print(f"Binding score: {results['final_binding_score']:.2f}")
    print("\n=== RATIONALE ===")
    print(results["rationale"])
