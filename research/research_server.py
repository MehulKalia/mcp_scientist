import arxiv
import json
import os
from typing import List
from mcp.server.fastmcp import FastMCP
import urllib.request
import anthropic
import base64
import httpx

PAPER_DIR = "papers"

# Initialize FastMCP server
mcp = FastMCP("research")

@mcp.tool()
def search_papers(topic: str, max_results: int = 5) -> List[str]:
    """
    Search for papers on arXiv based on a topic and store their information.
    
    Args:
        topic: The topic to search for
        max_results: Maximum number of results to retrieve (default: 5)
        
    Returns:
        List of paper IDs found in the search
    """
    
    # Use arxiv to find the papers 
    client = arxiv.Client()

    # Search for the most relevant articles matching the queried topic
    search = arxiv.Search(
        query = topic,
        max_results = max_results,
        sort_by = arxiv.SortCriterion.Relevance
    )

    papers = client.results(search)
    
    # Create directory for this topic
    path = os.path.join(PAPER_DIR, topic.lower().replace(" ", "_"))
    os.makedirs(path, exist_ok=True)
    
    file_path = os.path.join(path, "papers_info.json")

    # Try to load existing papers info
    try:
        with open(file_path, "r") as json_file:
            papers_info = json.load(json_file)
    except (FileNotFoundError, json.JSONDecodeError):
        papers_info = {}

    # Process each paper and add to papers_info  
    paper_ids = []
    for paper in papers:
        paper_id = paper.get_short_id()
        paper_ids.append(paper_id)
        paper_info = {
            'title': paper.title,
            'authors': [author.name for author in paper.authors],
            'summary': paper.summary,
            'pdf_url': paper.pdf_url,
            'published': str(paper.published.date())
        }
        papers_info[paper_id] = paper_info
        
        # Download and save the PDF file
        pdf_filename = f"{paper_id}.pdf"
        pdf_path = os.path.join(path, pdf_filename)
        if not os.path.exists(pdf_path):
            try:
                print(f"Downloading PDF for {paper_id}...")
                urllib.request.urlretrieve(paper.pdf_url, pdf_path)
                paper_info['pdf_path'] = pdf_path
                print(f"PDF saved to {pdf_path}")
            except Exception as e:
                print(f"Error downloading PDF for {paper_id}: {str(e)}")
                paper_info['pdf_path'] = None
        else:
            paper_info['pdf_path'] = pdf_path
            print(f"PDF already exists at {pdf_path}")
    
    # Save updated papers_info to json file
    with open(file_path, "w") as json_file:
        json.dump(papers_info, json_file, indent=2)
    
    print(f"Results are saved in: {file_path}")
    
    return paper_ids

@mcp.tool()
def extract_info(paper_id: str) -> str:
    """
    Search for information about a specific paper across all topic directories.
    
    Args:
        paper_id: The ID of the paper to look for
        
    Returns:
        JSON string with paper information if found, error message if not found
    """
 
    for item in os.listdir(PAPER_DIR):
        item_path = os.path.join(PAPER_DIR, item)
        if os.path.isdir(item_path):
            file_path = os.path.join(item_path, "papers_info.json")
            if os.path.isfile(file_path):
                try:
                    with open(file_path, "r") as json_file:
                        papers_info = json.load(json_file)
                        if paper_id in papers_info:
                            return json.dumps(papers_info[paper_id], indent=2)
                except (FileNotFoundError, json.JSONDecodeError) as e:
                    print(f"Error reading {file_path}: {str(e)}")
                    continue
    
    return f"There's no saved information related to paper {paper_id}."


@mcp.tool()
def analyze_paper_with_claude(paper_id: str='2409.12922v1', question: str = "What are the key findings in this paper?") -> str:
    """
    Analyze a paper using Claude AI. This function takes a paper ID, loads the PDF,
    and asks Claude to analyze it based on the provided question.
    
    Args:
        paper_id: The ID of the paper to analyze
        question: The question to ask Claude about the paper (default: "What are the key findings in this paper?")
        
    Returns:
        Claude's analysis of the paper
    """
    # Find the paper's PDF file
    pdf_path = None
    for item in os.listdir(PAPER_DIR):
        item_path = os.path.join(PAPER_DIR, item)
        if os.path.isdir(item_path):
            # Check if the PDF exists in this topic directory
            potential_pdf_path = os.path.join(item_path, f"{paper_id}.pdf")
            if os.path.isfile(potential_pdf_path):
                pdf_path = potential_pdf_path
                break
                
            # Also check the papers_info.json to find the stored pdf_path
            file_path = os.path.join(item_path, "papers_info.json")
            if os.path.isfile(file_path):
                try:
                    with open(file_path, "r") as json_file:
                        papers_info = json.load(json_file)
                        if paper_id in papers_info and "pdf_path" in papers_info[paper_id]:
                            stored_pdf_path = papers_info[paper_id]["pdf_path"]
                            if os.path.isfile(stored_pdf_path):
                                pdf_path = stored_pdf_path
                                break
                except (FileNotFoundError, json.JSONDecodeError) as e:
                    print(f"Error reading {file_path}: {str(e)}")
                    continue
    
    if not pdf_path:
        return f"Could not find PDF file for paper {paper_id}. Please make sure the paper has been downloaded."
    
    try:
        # Load and encode the PDF file
        with open(pdf_path, "rb") as f:
            pdf_data = base64.standard_b64encode(f.read()).decode("utf-8")

        # Initialize Anthropic client and get API key from environment variable
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        
        # Send the PDF to Claude for analysis
        response = client.messages.create(
            model="claude-3-7-sonnet-20250219",
            max_tokens=512, # 8192,
            system="You are a the best data scientist and researcher in the world. Your exeprtise spans life sciences, AI and protein design. Your are searching for useful information in the development and discovery of new proteins. When provided with PDF you must extract all the relevant informations for the development of new proteins.", # <-- role prompt
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "document",
                            "source": {
                                "type": "base64",
                                "media_type": "application/pdf",
                                "data": pdf_data
                            }
                        },
                        {
                            "type": "text",
                            "text": question
                        }
                    ]
                }
            ],
        )
        return  response.content
    except Exception as e:
        return f"Error analyzing paper: {str(e)}"

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

# Initialize Anthropic client with API key from .env if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv module not installed, will use environment variables directly

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')