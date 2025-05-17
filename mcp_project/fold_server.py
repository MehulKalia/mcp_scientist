from typing import Optional
import requests
import base64
import py3Dmol
from mcp.server.fastmcp import FastMCP
import subprocess, tempfile, base64, os
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
    Visualizes a PDB structure using PyMOL and returns a data URI for the PNG image.
    Falls back to BioPython if PyMOL is not available.
    """
    try:
        return visualize_pdb_pymol(pdb_str, width, height)
    except Exception as e:
        print(f"PyMOL visualization failed: {e}")
        print("Falling back to BioPython visualization")
        return visualize_pdb_biopython(pdb_str, width, height)

def visualize_pdb_pymol(pdb_str: str, width: int = 800, height: int = 600) -> str:
    """
    Visualizes a PDB structure using PyMOL and returns a data URI for the PNG image.
    """
    # 1) write PDB
    pdb_file = tempfile.NamedTemporaryFile(suffix=".pdb", delete=False)
    pdb_file.write(pdb_str.encode())
    pdb_file.close()

    # 2) generate a PyMOL script
    pml = tempfile.NamedTemporaryFile(suffix=".pml", delete=False, mode="w")
    pml.write(f"""
load {pdb_file.name}, model
hide everything, model
show cartoon, model
spectrum count, model
bg_color white
ray {width},{height}
png {pdb_file.name}.png
quit
""")
    pml.close()

    # 3) call PyMOL headless
    subprocess.run(
        ["pymol", "-cq", pml.name],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    # 4) read & encode the PNG
    png_path = pdb_file.name + ".png"
    with open(png_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()

    # 5) cleanup
    os.unlink(pdb_file.name)
    os.unlink(pml.name)
    os.unlink(png_path)

    return "data:image/png;base64," + b64

@mcp.tool()
def visualize_pdb_biopython(pdb_str: str, width: int = 800, height: int = 600, 
                            elev: int = 20, azim: int = 30, marker_size: int = 2,
                            background_color: str = 'white') -> str:
    """
    Visualizes a PDB structure using BioPython and Matplotlib and returns a data URI
    for the PNG image. This is a fallback for when PyMOL is not available.
    
    Args:
        pdb_str: PDB file content as string
        width: Width of the output image in pixels
        height: Height of the output image in pixels
        elev: Elevation viewing angle in degrees
        azim: Azimuth viewing angle in degrees
        marker_size: Size of the atom markers
        background_color: Background color of the image
        
    Returns:
        Data URI for the PNG image
    """
    try:
        # Import required libraries
        from Bio.PDB import PDBParser
        import matplotlib.pyplot as plt
        from mpl_toolkits.mplot3d import Axes3D
        import numpy as np
        import io
        
        # Write PDB content to a temporary file
        pdb_file = tempfile.NamedTemporaryFile(suffix=".pdb", delete=False)
        pdb_file.write(pdb_str.encode())
        pdb_file.close()
        
        try:
            # Parse the PDB file
            parser = PDBParser(QUIET=True)
            structure = parser.get_structure('protein', pdb_file.name)
            
            # Extract atom coordinates and colors based on atom type
            coords = []
            atom_types = []
            
            for model in structure:
                for chain in model:
                    for residue in chain:
                        for atom in residue:
                            coords.append(atom.get_coord())
                            atom_types.append(atom.get_id()[0])  # First character of atom ID usually represents element
            
            coords = np.array(coords)
            
            # Define colormaps for different atom types
            element_colors = {
                'C': 'black',   # Carbon
                'N': 'blue',    # Nitrogen
                'O': 'red',     # Oxygen
                'S': 'yellow',  # Sulfur
                'P': 'orange',  # Phosphorus
                'H': 'white',   # Hydrogen
                ' ': 'green'    # Unknown/other
            }
            
            # Create figure with appropriate DPI to match requested dimensions
            fig_width = width / 100  # Convert pixels to inches (assuming 100 DPI)
            fig_height = height / 100
            dpi = 100
            
            fig = plt.figure(figsize=(fig_width, fig_height), dpi=dpi, facecolor=background_color)
            ax = fig.add_subplot(111, projection='3d')
            
            # Set the viewing angle
            ax.view_init(elev=elev, azim=azim)
            
            # Color points by residue index (similar to 'spectrum' in PyMOL)
            scatter = ax.scatter(
                coords[:, 0], coords[:, 1], coords[:, 2], 
                s=marker_size, 
                c=np.arange(len(coords)), 
                cmap='viridis',
                alpha=0.7
            )
            
            # Create a cleaner visualization
            ax.set_axis_off()
            ax.grid(False)
            ax.set_facecolor(background_color)
            fig.patch.set_facecolor(background_color)
            
            # Adjust the plot to minimize margins
            plt.tight_layout(pad=0)
            
            # Save the figure to a BytesIO object
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=dpi, bbox_inches='tight', 
                        pad_inches=0, transparent=background_color=='transparent')
            plt.close(fig)
            
            # Convert to base64 data URI
            buf.seek(0)
            b64 = base64.b64encode(buf.read()).decode()
            return "data:image/png;base64," + b64
            
        finally:
            # Clean up
            os.unlink(pdb_file.name)
            
    except Exception as e:
        # If BioPython visualization fails, return an error message as a text data URI
        error_message = f"Error visualizing PDB with BioPython: {str(e)}"
        return "data:text/plain," + base64.b64encode(error_message.encode()).decode()

@mcp.tool()
def visualize_pdb_3d(pdb_str: str, width: int = 800, height: int = 600, style: str = "cartoon") -> str:
    """
    Generates an interactive 3D visualization of the protein structure using py3Dmol.
    
    Args:
        pdb_str: PDB file content as string
        width: Width of the viewer
        height: Height of the viewer
        style: Visualization style ('cartoon', 'sphere', 'stick', 'line', or 'cross')
        
    Returns:
        HTML content for an interactive 3D visualization
    """
    try:
        # Create a viewer
        view = py3Dmol.view(width=width, height=height)
        
        # Add the model
        view.addModel(pdb_str, "pdb")
        
        # Apply style
        if style == "cartoon":
            view.setStyle({"cartoon": {"color": "spectrum"}})
        elif style == "sphere":
            view.setStyle({"sphere": {"colorscheme": "spectralbase"}})
        elif style == "stick":
            view.setStyle({"stick": {"colorscheme": "spectralbase"}})
        elif style == "line":
            view.setStyle({"line": {"colorscheme": "spectralbase"}})
        elif style == "cross":
            view.setStyle({"cross": {"colorscheme": "spectralbase"}})
        else:
            # Default to cartoon
            view.setStyle({"cartoon": {"color": "spectrum"}})
        
        # Set view options
        view.zoomTo()
        
        # Get the HTML content
        html_content = view.write_html()
        
        # Return as data URI
        b64 = base64.b64encode(html_content.encode()).decode()
        return "data:text/html;base64," + b64
        
    except Exception as e:
        # If py3Dmol visualization fails, return an error message
        error_message = f"Error creating 3D visualization: {str(e)}"
        return "data:text/plain," + base64.b64encode(error_message.encode()).decode()

if __name__ == "__main__":
    # run over stdio, per the tutorial
    mcp.run(transport="stdio")
