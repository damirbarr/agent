from langchain_community.tools import WikipediaQueryRun, DuckDuckGoSearchRun
from langchain_community.utilities import WikipediaAPIWrapper
from langchain.tools import Tool
from datetime import datetime
import subprocess
from langchain_community.document_loaders.pdf import PyPDFLoader
from src.tools.zillow import search_zillow_properties, get_zillow_property_details
from src.tools.real_estate import find_property, extract_property_details, find_comparable_properties, analyze_property

def save_to_txt(data: str, filename):
    if filename is None:
        filename = f"output_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt"
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

# Tools for Zillow property search
zillow_search_tool = Tool(
    name="zillow_search",
    func=search_zillow_properties,
    description="Search for properties on Zillow by location (address, city, zip code, or neighborhood). Returns property listings with basic information.",
)

zillow_property_tool = Tool(
    name="zillow_property_details",
    func=get_zillow_property_details,
    description="Get detailed information about a specific property on Zillow using its URL. Provides comprehensive details about the property including features and description.",
)

# Real Estate Analysis Tools
property_finder_tool = Tool(
    name="find_property",
    func=find_property,
    description="Find a property on Zillow based on an address or description. Returns the property URL and basic information.",
)

property_details_tool = Tool(
    name="extract_property_details",
    func=extract_property_details,
    description="Extract detailed information about a property from its Zillow or Compass URL. Provides comprehensive details including listing price, bedrooms, baths, square footage, lot size, year built, rent estimates, and key features.",
)

property_comps_tool = Tool(
    name="find_comparable_properties",
    func=find_comparable_properties,
    description="Find comparable properties for a given property URL. Analyzes the target property and finds similar properties in the area. Parameters: property_url, radius_miles (default: 1.0), max_price_diff_percent (default: 20.0), num_comps (default: 3).",
)

property_analysis_tool = Tool(
    name="analyze_property",
    func=analyze_property,
    description="Perform a comprehensive analysis of a property by address or URL. This tool combines property finding, detailed information extraction, and comparable property analysis into a single structured report.",
)
