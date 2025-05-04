from langchain_community.tools import WikipediaQueryRun, DuckDuckGoSearchRun
from langchain_community.utilities import WikipediaAPIWrapper
from langchain.tools import Tool
from datetime import datetime
import subprocess
from langchain_community.document_loaders.pdf import PyPDFLoader

def save_to_txt(data: str, filename: str = "research_output.txt"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted_text = f"--- Output ---\nTimestamp: {timestamp}\n\n{data}\n\n"

    with open(filename, "a", encoding="utf-8") as f:
        f.write(formatted_text)
    
    return f"Data successfully saved to {filename}"

save_tool = Tool(
    name="save_text_to_file",
    func=save_to_txt,
    description="Saves structured research data to a text file.",
)

search = DuckDuckGoSearchRun()
search_tool = Tool(
    name="search",
    func=search.run,
    description="Search the web for information",
)

api_wrapper = WikipediaAPIWrapper(top_k_results=1, doc_content_chars_max=100)
wiki_tool = WikipediaQueryRun(api_wrapper=api_wrapper)

# A tool to use the shell
def use_shell(command: str):
    return subprocess.check_output(command, shell=True).decode("utf-8")

shell_tool = Tool(
    name="local_shell",
    func=use_shell,
    description="Use the local shell to run commands",
)

# A tool to read a PDF file
def read_pdf(file_path: str):
    return PyPDFLoader(file_path).load()

read_pdf_tool = Tool(
    name="read_pdf",
    func=read_pdf,
    description="Read a PDF file",
)
