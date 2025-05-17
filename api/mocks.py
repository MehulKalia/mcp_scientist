"""
Mock data and functions for development and testing
"""
import asyncio
from typing import Dict, Any

async def mock_structure_prediction(sequence: str, iteration: int) -> Dict[str, Any]:
    """Mock structure prediction response"""
    await asyncio.sleep(1)  # Simulate API call
    return {
        "sequence": sequence,
        "pdb_url": f"https://example.com/pdb/{iteration}.pdb",
        "confidence": 0.8,
        "visualization_url": f"https://example.com/viz/{iteration}.png"
    }

async def mock_binding_prediction(sequence: str, target: str, iteration: int) -> float:
    """Mock binding prediction response"""
    await asyncio.sleep(1)  # Simulate API call
    return 0.5 + (iteration * 0.05)  # Fake improvement over iterations

def mock_mutate_sequence(sequence: str) -> str:
    """Create a slightly modified version of the sequence"""
    seq_list = list(sequence)
    for i in range(len(seq_list)):
        if i % 7 == 0 and i > 0 and i < len(seq_list) - 1:
            seq_list[i] = 'K' if seq_list[i] != 'K' else 'R'
    return ''.join(seq_list) 