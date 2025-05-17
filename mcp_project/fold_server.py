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

@mcp.tool()
def visualize_pdb(pdb_str: str, width: int = 800, height: int = 600) -> str:
    """
    Renders a PDB string into a base64-encoded PNG via py3Dmol.
    Returns: 'data:image/png;base64,...'
    """
    view = py3Dmol.view(width=width, height=height)
    view.addModel(pdb_str, "pdb")
    view.setStyle({"cartoon": {"color":"spectrum"}})
    view.zoomTo()
    # get the PNG data URI
    data_uri = view.png()
    if not data_uri.startswith("data:image/png;base64,"):
        raise RuntimeError("Unexpected PNG output")
    return data_uri

if __name__ == "__main__":
    # run over stdio, per the tutorial
    mcp.run(transport="stdio")
