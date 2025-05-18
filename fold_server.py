from typing import Optional
import requests
import base64
import py3Dmol
from mcp.server.fastmcp import FastMCP
import os

mcp = FastMCP("fold")

@mcp.tool()
def fold_sequence(sequence: str) -> str:
    """
    Submits a raw amino-acid sequence to the ESMFold API and returns the PDB text.
    """
    url = "https://api.esmatlas.com/foldSequence/v1/pdb/"
    resp = requests.post(url, data=sequence, headers={"Content-Type":"text/plain"})
    if resp.status_code != 200:
        print("Status:", resp.status_code)
        print("Body:", resp.text)
    resp.raise_for_status()
    return resp.text

if __name__ == "__main__":
    # run over stdio, per the tutorial
    mcp.run(transport="stdio")