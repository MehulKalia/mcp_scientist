# Protogen: Unlocking Abundance in Protein Discovery with AI Agents

## 🌱 Inspiration

When Claude Code launched, it enabled software engineers to have an "abundance mindset," radically accelerating innovation. Inspired by this, we recognized biotechnology as another field significantly bottlenecked by manual workflows: reading literature, designing experiments, and analyzing data. Despite breakthroughs like AlphaFold, the real bottleneck was still present. We asked ourselves: What if biotech researchers could adopt the same abundance mindset through powerful, streamlined tools?

## 🛠️ How We Built Protogen

We strongly believe in CLI tools. They're performant, easily integrated into existing workflows, and minimize distractions. With this philosophy, Protogen was designed as a CLI-first solution, empowering researchers to interact seamlessly with advanced AI-driven protein folding:

- **CLI-First Design**: Built using Python's Click library, Protogen delivers high performance and easy automation directly from researchers' terminals.
- **AI Agent & Reasoning**: Integrated Claude's reasoning power, coupled with protein-folding APIs (ESMFold), enabling rapid generation and assessment of protein designs.
- **Backend and APIs**: FastAPI provided efficient, low-latency communication between our agentic workflows and external resources, including literature searches and protein-folding APIs.
- **Real-Time Visualization (Optional Integration)**: For deeper insights, Protogen outputs protein structures compatible with visualization tools like Py3Dmol, maintaining modularity while preserving CLI simplicity.

Protogen's CLI-centric approach provided maximum flexibility, speed, and integration into researchers' existing toolchains.

## 📚 What We Learned

Building Protogen taught us valuable lessons:

- **Efficiency through Simplicity**: A CLI tool reduced overhead and distraction, enhancing researchers' productivity by integrating seamlessly into existing scripting and automation workflows.
- **The Power of MCP**: The value of MCP being the language through which LLMs speak with is valuable. This hackathon gave us the opportunity to learn how to use MCP in an impactful application.
- **Agentic Workflows**: We learned to expertly chain multiple AI-driven tasks like literature retrieval, sequence design, and folding prediction.
- **Rapid Prototyping**: Delivering a robust, fully functional CLI application within a one-day hackathon strengthened our skills in agile development and real-time problem-solving.

## 🚧 Challenges We Faced

- **Computational Constraints**: Without direct access to advanced GPU resources (e.g., H100 GPUs required for certain AlphaFold functionalities), we creatively mocked certain simulations, balancing realism and feasibility.
- **CLI UX Design**: Crafting an intuitive yet powerful CLI experience required iterative testing and continuous feedback from users accustomed to GUI tools.
- **Integrating Diverse APIs**: Coordinating multiple API integrations, especially within a CLI context, demanded careful orchestration to ensure reliability and clarity in outputs.

## 🚀 What's Next for Protogen?

Protogen represents the beginning of a larger vision: streamlined, abundant biotech innovation driven by AI agents. Our next steps include:

- Securing resources to unlock full AlphaFold capabilities.
- Enhancing our CLI tool's functionality with expanded integrations and customizable automation scripts.
- Collaborating closely with biotech researchers to refine Protogen's workflows and validate its real-world impact.

With Protogen, we're making an abundant future in biotechnology not only imaginable, but practically achievable right from the command line.

## How to Run:
### Install Dependencies
Make a virtual environment of your choice, then install the following dependencies
`pip install requests python-dotenv anthropic mcp[cli] mcp-server py3Dmol biopython matplotlib`

### Other steps
In one terminal start the MCP server
`mcp dev .\fold_server.py`
In another terminal run our CLI
`python agent.py`