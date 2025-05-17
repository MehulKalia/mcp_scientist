import os
import requests
import json
import time
from typing import Dict, List, Any, Optional, Union
import uuid
from dotenv import load_dotenv

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
        self.alphafold_mcp_url = alphafold_mcp_url
        self.esmfold_mcp_url = esmfold_mcp_url
        self.llm_api_key = llm_api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.llm_api_url = llm_api_url
        self.verbose = verbose
        self.session_id = str(uuid.uuid4())
        
        # Initialize conversation history
        self.conversation_history = []
        
        # Initialize basic session info
        self.current_iteration = 0
        self.best_sequence = None
        self.best_score = float('-inf')
        
    def log(self, message: str, color: Optional[str] = None) -> None:
        """Log a message if verbose mode is enabled."""
        if self.verbose:
            if color:
                print(f"{color}[ProteinDesignAgent] {message}{Colors.END}")
            else:
                print(f"[ProteinDesignAgent] {message}")
    
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
            self.log(f"Error querying LLM: {e}", Colors.RED)
            return f"Error: {str(e)}"
    
    def predict_structure(self, sequence: str) -> Dict[str, Any]:
        """
        Call the AlphaFold/ESMFold MCP server to predict protein structure.
        
        Args:
            sequence: Amino acid sequence
            
        Returns:
            Structure prediction result
        """
        sequence_preview = sequence[:10] + "..." if len(sequence) > 10 else sequence
        self.log(f"STRUCTURE PREDICTION for: {sequence_preview}", Colors.RED)
        
        # Placeholder for actual MCP call
        # In a real implementation, this would call the MCP server
        self.log("Simulating structure prediction (MCP server call)", Colors.RED)
        
        # Simulate a structure prediction result
        structure_result = {
            "sequence": sequence,
            "pdb_url": f"https://example.com/pdb/{self.current_iteration}.pdb",
            "confidence": 0.8,
            "visualization_url": f"https://example.com/viz/{self.current_iteration}.png"
        }
        
        self.log(f"Structure prediction complete with confidence: {structure_result['confidence']}", Colors.GREEN)
        return structure_result
    
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
        max_iterations = 3
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
        I've completed all {max_iterations} iterations of the protein design process for the task: "{user_prompt}"
        
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
