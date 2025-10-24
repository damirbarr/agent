import logging
import asyncio
from typing import Dict, Any, List, Optional, Union
from browser_use import Agent as BrowserAgent
from langchain_openai import ChatOpenAI
import re
import json

logger = logging.getLogger(__name__)

class RealEstateAnalyzer:
    """Tool for analyzing real estate properties using browser automation."""
    
    def __init__(self, model_name="gpt-4o"):
        self.llm = ChatOpenAI(model=model_name)
    
    async def find_property(self, search_query: str) -> Dict[str, Any]:
        """
        Find a property on Zillow using a search query.
        
        Args:
            search_query: Address or description of the property
            
        Returns:
            Dict with property information or error
        """
        try:
            agent = BrowserAgent(
                task=f"""
                Search for this property: "{search_query}" on Zillow.
                Find the most relevant property listing that matches this query.
                Return the property details including:
                1. Full property URL
                2. Address
                3. Price
                4. Basic details (beds/baths/sqft)
                """,
                llm=self.llm,
            )
            
            result = await agent.run()
            
            # Extract the property URL
            property_url = None
            if isinstance(result, dict) and "url" in result:
                property_url = result["url"]
            else:
                # Try to find URL in the result text
                url_match = re.search(r'(https?://(?:www\.)?zillow\.com/[^\s]+)', str(result))
                if url_match:
                    property_url = url_match.group(1)
            
            if not property_url:
                return {
                    "success": False,
                    "error": "Could not find property URL",
                    "message": "Try a more specific search query"
                }
            
            return {
                "success": True,
                "query": search_query,
                "property_url": property_url,
                "source": "zillow",
                "raw_result": result
            }
            
        except Exception as e:
            logger.error(f"Error finding property: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "An error occurred while searching for the property"
            }
    
    async def extract_property_details(self, property_url: str, check_compass: bool = True) -> Dict[str, Any]:
        """
        Extract comprehensive details about a property from Zillow or Compass.
        
        Args:
            property_url: URL of the property (Zillow or Compass)
            check_compass: Whether to also check Compass if this is a Zillow URL
            
        Returns:
            Dict with detailed property information or error
        """
        try:
            # Determine if this is a Zillow or Compass URL
            is_zillow = "zillow.com" in property_url.lower()
            is_compass = "compass.com" in property_url.lower()
            
            # If not either of these sites, return an error
            if not is_zillow and not is_compass:
                return {
                    "success": False,
                    "error": "Unsupported website",
                    "message": "Only Zillow and Compass URLs are currently supported"
                }
            
            # Extract details from the primary source
            primary_details = await self._extract_from_site(property_url)
            
            # If requested and this is a Zillow URL, try to find and extract from Compass too
            compass_details = {}
            if check_compass and is_zillow and primary_details.get("success", False):
                try:
                    # Try to find the same property on Compass
                    address = primary_details.get("details", {}).get("address", "")
                    if address:
                        compass_url = await self._find_on_compass(address)
                        if compass_url:
                            compass_details = await self._extract_from_site(compass_url)
                except Exception as e:
                    logger.warning(f"Error getting Compass details: {e}")
            
            # Merge the details, preferring Compass for any fields it has
            if compass_details.get("success", False):
                merged_details = self._merge_property_details(
                    primary_details.get("details", {}),
                    compass_details.get("details", {})
                )
                sources = ["zillow", "compass"]
            else:
                merged_details = primary_details.get("details", {})
                sources = ["zillow"] if is_zillow else ["compass"]
            
            return {
                "success": True,
                "property_url": property_url,
                "sources": sources,
                "details": merged_details
            }
            
        except Exception as e:
            logger.error(f"Error extracting property details: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "An error occurred while extracting property details"
            }
    
    async def find_comparable_properties(self, property_url: str, radius_miles: float = 1.0, 
                                        max_price_diff_percent: float = 20.0, 
                                        num_comps: int = 3) -> Dict[str, Any]:
        """
        Find comparable properties for a given property.
        
        Args:
            property_url: URL of the target property
            radius_miles: Search radius in miles
            max_price_diff_percent: Maximum price difference percentage
            num_comps: Number of comps to return
            
        Returns:
            Dict with comparable properties or error
        """
        try:
            # First, get details of the target property
            property_details = await self.extract_property_details(property_url, check_compass=False)
            
            if not property_details.get("success", False):
                return {
                    "success": False,
                    "error": "Failed to get target property details",
                    "message": property_details.get("message", "Unknown error")
                }
            
            # Extract key information for comps search
            details = property_details.get("details", {})
            address = details.get("address", "")
            beds = details.get("beds", "")
            baths = details.get("baths", "")
            sqft = details.get("sqft", "")
            price = details.get("price", "")
            
            # Use neighborhood or zip code from address
            match = re.search(r'([A-Z]{2}\s+\d{5}|\w+\s+neighborhood)', address)
            location = match.group(1) if match else "nearby"
            
            # Search for comparable properties
            agent = BrowserAgent(
                task=f"""
                Find {num_comps} comparable properties to this property:
                URL: {property_url}
                Address: {address}
                Price: {price}
                Beds: {beds}
                Baths: {baths}
                Square Feet: {sqft}
                
                Search within {radius_miles} miles radius and with a price difference of no more than {max_price_diff_percent}%.
                Look for properties that are as similar as possible in:
                1. Bedroom and bathroom count
                2. Square footage
                3. Property type (house, condo, etc.)
                4. Neighborhood quality
                
                For each comparable property, provide:
                1. Property URL
                2. Address
                3. Price
                4. Beds/Baths/Sqft
                5. Key similarities and differences compared to the target property
                """,
                llm=self.llm,
            )
            
            result = await agent.run()
            
            # Process and structure the results
            comps = []
            
            if isinstance(result, dict) and "comps" in result:
                # If the result has a structured comps list
                comps = result["comps"]
            elif isinstance(result, list):
                # If result is already a list
                comps = result
            else:
                # Try to parse from text
                # Look for property URLs
                urls = re.findall(r'(https?://(?:www\.)?(?:zillow|compass|redfin)\.com/[^\s]+)', str(result))
                
                # For each URL, extract surrounding text as a comp entry
                for i, url in enumerate(urls[:num_comps]):
                    # Find text blocks related to this URL
                    url_index = str(result).find(url)
                    if url_index >= 0:
                        # Get text before and after URL to capture all details
                        start_index = max(0, str(result).rfind("\n\n", 0, url_index))
                        end_index = str(result).find("\n\n", url_index)
                        if end_index < 0:
                            end_index = len(str(result))
                        
                        comp_text = str(result)[start_index:end_index]
                        
                        # Extract key details
                        address_match = re.search(r'Address:\s*(.*?)(?:\n|$)', comp_text)
                        price_match = re.search(r'Price:\s*(.*?)(?:\n|$)', comp_text)
                        details_match = re.search(r'(?:Details|Specs):\s*(.*?)(?:\n|$)', comp_text)
                        
                        comp = {
                            "url": url,
                            "address": address_match.group(1) if address_match else "Address not found",
                            "price": price_match.group(1) if price_match else "Price not found",
                            "details": details_match.group(1) if details_match else "Details not found",
                        }
                        
                        # Look for comparison text
                        comparison_match = re.search(r'(?:Comparison|Similarities|Differences):\s*(.*?)(?:\n\n|$)', comp_text, re.DOTALL)
                        if comparison_match:
                            comp["comparison"] = comparison_match.group(1).strip()
                        
                        comps.append(comp)
            
            return {
                "success": True,
                "target_property_url": property_url,
                "target_property_details": details,
                "comparable_properties": comps,
                "search_parameters": {
                    "radius_miles": radius_miles,
                    "max_price_diff_percent": max_price_diff_percent,
                }
            }
            
        except Exception as e:
            logger.error(f"Error finding comparable properties: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "An error occurred while finding comparable properties"
            }
    
    async def _extract_from_site(self, property_url: str) -> Dict[str, Any]:
        """Internal method to extract details from a specific site."""
        try:
            is_zillow = "zillow.com" in property_url.lower()
            is_compass = "compass.com" in property_url.lower()
            
            site_name = "Zillow" if is_zillow else "Compass"
            
            agent = BrowserAgent(
                task=f"""
                Visit this {site_name} property page: {property_url}.
                Extract and organize all property details including:
                
                1. Address (full address with zip code)
                2. Listing price
                3. Number of bedrooms
                4. Number of bathrooms
                5. Finished square footage
                6. Lot size square footage
                7. Year built
                8. Rentcast estimate or any rental estimates provided
                9. Key features from the description (look for mentions of renovations, special features, etc.)
                10. What's visible in the photos (note any important features like updated kitchen, pool, etc.)
                11. School information
                12. Neighborhood information
                13. Price history if available
                
                Format the data in a structured way.
                """,
                llm=self.llm,
            )
            
            result = await agent.run()
            
            # Initialize with default structure
            details = {
                "address": "Not found",
                "price": "Not found",
                "beds": "Not found",
                "baths": "Not found", 
                "sqft_finished": "Not found",
                "sqft_lot": "Not found",
                "year_built": "Not found",
                "rent_estimate": "Not found",
                "key_features": [],
                "photo_observations": [],
                "schools": [],
                "neighborhood": "Not found",
                "price_history": [],
                "description": "Not found"
            }
            
            # Update with extracted information
            if isinstance(result, dict):
                # If result is already structured, map fields
                for key in details:
                    if key in result:
                        details[key] = result[key]
                    # Check for alternative field names
                    elif key == "sqft_finished" and "sqft" in result:
                        details[key] = result["sqft"]
                    elif key == "sqft_lot" and "lot_size" in result:
                        details[key] = result["lot_size"]
                    elif key == "rent_estimate" and "rental_estimate" in result:
                        details[key] = result["rental_estimate"]
                    elif key == "key_features" and "features" in result:
                        details[key] = result["features"]
            else:
                # If result is text, parse using regex
                text_result = str(result)
                
                # Address
                address_match = re.search(r'(?:Address|Location):\s*(.*?)(?:\n|$)', text_result)
                if address_match:
                    details["address"] = address_match.group(1).strip()
                
                # Price
                price_match = re.search(r'(?:Price|Listing Price|Listed for):\s*\$?([\d,]+)', text_result)
                if price_match:
                    details["price"] = f"${price_match.group(1)}"
                
                # Beds
                beds_match = re.search(r'(?:Beds|Bedrooms):\s*(\d+(?:\.\d+)?)', text_result)
                if beds_match:
                    details["beds"] = beds_match.group(1)
                
                # Baths
                baths_match = re.search(r'(?:Baths|Bathrooms):\s*(\d+(?:\.\d+)?)', text_result)
                if baths_match:
                    details["baths"] = baths_match.group(1)
                
                # Square Footage
                sqft_match = re.search(r'(?:Square Feet|Sqft|Square Footage):\s*([\d,]+)', text_result)
                if sqft_match:
                    details["sqft_finished"] = sqft_match.group(1)
                
                # Lot Size
                lot_match = re.search(r'(?:Lot Size|Lot):\s*([\d,]+)\s*(?:sqft|sq\. ft\.)', text_result)
                if lot_match:
                    details["sqft_lot"] = lot_match.group(1)
                
                # Year Built
                year_match = re.search(r'(?:Year Built|Built in):\s*(\d{4})', text_result)
                if year_match:
                    details["year_built"] = year_match.group(1)
                
                # Rent Estimate
                rent_match = re.search(r'(?:Rent|Rental|Rentcast) [eE]stimate:\s*\$?([\d,]+)', text_result)
                if rent_match:
                    details["rent_estimate"] = f"${rent_match.group(1)}"
                
                # Description and features
                desc_match = re.search(r'Description:(.*?)(?:Features:|$)', text_result, re.DOTALL)
                if desc_match:
                    details["description"] = desc_match.group(1).strip()
                
                # Features
                features_section = re.search(r'(?:Features|Key Features):(.*?)(?:\n\n|$)', text_result, re.DOTALL)
                if features_section:
                    features_text = features_section.group(1).strip()
                    features = [f.strip() for f in re.split(r'\n-|\n•|\n\*', features_text) if f.strip()]
                    if features:
                        details["key_features"] = features
                
                # Photo observations
                photos_section = re.search(r'(?:Photos|Photo Observations|From the photos):(.*?)(?:\n\n|$)', text_result, re.DOTALL)
                if photos_section:
                    photos_text = photos_section.group(1).strip()
                    observations = [o.strip() for o in re.split(r'\n-|\n•|\n\*', photos_text) if o.strip()]
                    if observations:
                        details["photo_observations"] = observations
            
            return {
                "success": True,
                "property_url": property_url,
                "details": details
            }
            
        except Exception as e:
            logger.error(f"Error extracting from {property_url}: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to extract details from {property_url}"
            }
    
    async def _find_on_compass(self, address: str) -> Optional[str]:
        """Find a property on Compass using its address."""
        try:
            agent = BrowserAgent(
                task=f"""
                Search for this property address on Compass.com: "{address}"
                If you find the property, return ONLY the full property URL.
                If you can't find it, say "Not found".
                """,
                llm=self.llm,
            )
            
            result = await agent.run()
            
            # Check if result contains a Compass URL
            compass_url_match = re.search(r'(https?://(?:www\.)?compass\.com/[^\s]+)', str(result))
            if compass_url_match:
                return compass_url_match.group(1)
            
            return None
            
        except Exception as e:
            logger.warning(f"Error finding property on Compass: {e}")
            return None
    
    def _merge_property_details(self, zillow_details: Dict[str, Any], compass_details: Dict[str, Any]) -> Dict[str, Any]:
        """Merge property details from Zillow and Compass, preferring Compass data when available."""
        merged = zillow_details.copy()
        
        for key, value in compass_details.items():
            # Skip if Compass value is empty or "Not found"
            if value in (None, "", "Not found", []):
                continue
                
            # For lists, combine unique items
            if isinstance(value, list) and isinstance(merged.get(key, []), list):
                existing_items = set(str(item).lower() for item in merged.get(key, []))
                for item in value:
                    if str(item).lower() not in existing_items:
                        merged.setdefault(key, []).append(item)
            else:
                # For scalar values, prefer Compass data
                merged[key] = value
        
        return merged

# Synchronous wrapper functions for LangChain tool integration
def find_property(search_query: str) -> str:
    """
    Find a property on Zillow using a search query.
    
    Args:
        search_query: Address or description of the property
        
    Returns:
        String with property information or error message
    """
    analyzer = RealEstateAnalyzer()
    result = asyncio.run(analyzer.find_property(search_query))
    
    if not result["success"]:
        return f"Error finding property: {result['error']}. {result['message']}"
    
    formatted_result = {
        "property_found": True,
        "search_query": result['query'],
        "property_url": result['property_url'],
        "source": result.get('source', 'zillow')
    }
    
    # Add any additional information from the raw result
    if isinstance(result["raw_result"], dict):
        if "address" in result["raw_result"]:
            formatted_result["address"] = result["raw_result"]["address"]
        if "price" in result["raw_result"]:
            formatted_result["price"] = result["raw_result"]["price"]
        if "details" in result["raw_result"]:
            formatted_result["details"] = result["raw_result"]["details"]
    
    # Convert to JSON for structured output
    return json.dumps(formatted_result, indent=2)

def extract_property_details(property_url: str) -> str:
    """
    Extract comprehensive details about a property from Zillow or Compass.
    
    Args:
        property_url: URL of the property (Zillow or Compass)
        
    Returns:
        String with detailed property information or error message
    """
    analyzer = RealEstateAnalyzer()
    result = asyncio.run(analyzer.extract_property_details(property_url))
    
    if not result["success"]:
        return f"Error extracting property details: {result['error']}. {result['message']}"
    
    details = result["details"]
    sources = ", ".join(result["sources"])
    
    # Create a structured output format
    property_data = {
        "property_details_extracted": True,
        "property_url": result["property_url"],
        "data_sources": sources,
        "address": details["address"],
        "price": details["price"],
        "bedrooms": details["beds"],
        "bathrooms": details["baths"],
        "square_feet": {
            "finished": details["sqft_finished"],
            "lot": details["sqft_lot"]
        },
        "year_built": details["year_built"],
        "rent_estimate": details["rent_estimate"],
        "description": details["description"],
        "key_features": details["key_features"],
        "photo_observations": details["photo_observations"],
        "neighborhood": details["neighborhood"]
    }
    
    # Convert to JSON for structured output
    return json.dumps(property_data, indent=2)

def find_comparable_properties(property_url: str, radius_miles: float = 1.0, 
                               max_price_diff_percent: float = 20.0, 
                               num_comps: int = 3) -> str:
    """
    Find comparable properties for a given property.
    
    Args:
        property_url: URL of the target property
        radius_miles: Search radius in miles
        max_price_diff_percent: Maximum price difference percentage
        num_comps: Number of comps to return
        
    Returns:
        String with comparable properties or error message
    """
    analyzer = RealEstateAnalyzer()
    result = asyncio.run(analyzer.find_comparable_properties(
        property_url, radius_miles, max_price_diff_percent, num_comps
    ))
    
    if not result["success"]:
        return f"Error finding comparable properties: {result['error']}. {result['message']}"
    
    target_details = result["target_property_details"]
    comps = result["comparable_properties"]
    
    # Create a structured output format
    comps_data = {
        "comparable_properties_found": True,
        "target_property": {
            "url": result["target_property_url"],
            "address": target_details.get("address", "Not available"),
            "price": target_details.get("price", "Not available"),
            "bedrooms": target_details.get("beds", "Not available"),
            "bathrooms": target_details.get("baths", "Not available"),
            "square_feet": target_details.get("sqft_finished", "Not available")
        },
        "search_parameters": {
            "radius_miles": result["search_parameters"]["radius_miles"],
            "max_price_diff_percent": result["search_parameters"]["max_price_diff_percent"],
            "num_comps_requested": num_comps,
            "num_comps_found": len(comps)
        },
        "comparable_properties": []
    }
    
    # Add each comparable property
    for comp in comps:
        comp_data = {
            "url": comp.get("url", "Not available"),
            "address": comp.get("address", "Not available"),
            "price": comp.get("price", "Not available"),
            "details": comp.get("details", "Not available")
        }
        
        if "comparison" in comp:
            comp_data["comparison"] = comp["comparison"]
            
        comps_data["comparable_properties"].append(comp_data)
    
    # Convert to JSON for structured output
    return json.dumps(comps_data, indent=2)

# Function to create a comprehensive property analysis report
def analyze_property(address_or_url: str) -> str:
    """
    Perform a comprehensive analysis of a property with structured report format.
    
    Args:
        address_or_url: Property address or direct Zillow/Compass URL
        
    Returns:
        Formatted property analysis summary
    """
    # Initialize the analyzer
    analyzer = RealEstateAnalyzer()
    
    # Determine if input is a URL or address
    is_url = address_or_url.startswith("http")
    
    # Step 1: Find property or use direct URL
    if is_url:
        property_url = address_or_url
        property_result = {"success": True, "property_url": property_url}
    else:
        property_result = asyncio.run(analyzer.find_property(address_or_url))
        if not property_result["success"]:
            return f"Error: Could not find property. {property_result['message']}"
        property_url = property_result["property_url"]
    
    # Step 2: Extract detailed property information
    details_result = asyncio.run(analyzer.extract_property_details(property_url))
    if not details_result["success"]:
        return f"Error: Could not extract property details. {details_result['message']}"
    
    # Step 3: Find comparable properties
    comps_result = asyncio.run(analyzer.find_comparable_properties(
        property_url, radius_miles=1.0, max_price_diff_percent=20.0, num_comps=3
    ))
    
    # Create detailed property data dictionary (for possible JSON usage)
    property_details = details_result["details"]
    sources = details_result["sources"]
    analysis_data = {
        "success": True,
        "property_information": {
            "address": property_details["address"],
            "property_url": property_url,
            "data_sources": sources
        },
        "property_details": {
            "price": property_details["price"],
            "bedrooms": property_details["beds"],
            "bathrooms": property_details["baths"],
            "square_feet_finished": property_details["sqft_finished"],
            "lot_size": property_details["sqft_lot"],
            "year_built": property_details["year_built"],
            "estimated_monthly_rent": property_details["rent_estimate"]
        },
        "property_features": {
            "key_features": property_details["key_features"],
            "visible_in_photos": property_details["photo_observations"]
        },
        "property_description": property_details["description"],
        "neighborhood_information": property_details["neighborhood"]
    }
    
    # Add comparable properties if available
    if comps_result["success"]:
        comps = comps_result["comparable_properties"]
        analysis_data["comparable_properties"] = {
            "search_parameters": {
                "radius_miles": comps_result["search_parameters"]["radius_miles"],
                "max_price_diff_percent": comps_result["search_parameters"]["max_price_diff_percent"]
            },
            "properties": []
        }
        
        for comp in comps:
            analysis_data["comparable_properties"]["properties"].append({
                "address": comp.get("address", "Not available"),
                "price": comp.get("price", "Not available"),
                "details": comp.get("details", "Not available"),
                "url": comp.get("url", "Not available"),
                "comparison": comp.get("comparison", "Not available")
            })
    
    # Create a formatted human-readable summary
    # Main property details summary
    beds = property_details["beds"] if property_details["beds"] != "Not found" else "N/A"
    baths = property_details["baths"] if property_details["baths"] != "Not found" else "N/A" 
    year_built = property_details["year_built"] if property_details["year_built"] != "Not found" else "N/A"
    price = property_details["price"] if property_details["price"] != "Not found" else "N/A"
    sqft = property_details["sqft_finished"] if property_details["sqft_finished"] != "Not found" else "N/A"
    lot_size = property_details["sqft_lot"] if property_details["sqft_lot"] != "Not found" else "N/A"
    
    # Extract notable features (limit to 3-5 most important ones)
    notable_features = []
    if property_details["key_features"]:
        notable_features.extend(property_details["key_features"][:3])
    
    # Add photo observations if we need more features
    if len(notable_features) < 3 and property_details["photo_observations"]:
        remaining_slots = 3 - len(notable_features)
        notable_features.extend(property_details["photo_observations"][:remaining_slots])
    
    # Features text
    features_text = "; ".join(notable_features) if notable_features else "No notable features found"
    
    # Neighborhood and schools
    neighborhood_info = property_details["neighborhood"]
    if neighborhood_info == "Not found":
        neighborhood_info = "Limited neighborhood information available"
    
    # Comparable properties summary
    comps_summary = ""
    if comps_result["success"] and comps:
        comp_prices = []
        for comp in comps:
            price_str = comp.get("price", "").replace("$", "").replace(",", "")
            if price_str.isdigit():
                comp_prices.append(int(price_str))
        
        if comp_prices:
            avg_comp_price = sum(comp_prices) / len(comp_prices)
            price_str = price.replace("$", "").replace(",", "")
            if price_str.isdigit():
                property_price = int(price_str)
                price_difference = ((property_price - avg_comp_price) / avg_comp_price) * 100
                comps_summary = f"The property is priced {abs(price_difference):.1f}% {'above' if price_difference > 0 else 'below'} the average of comparable properties in the area."
    
    # Format the summary
    address = property_details["address"]
    quick_summary = f"The property at {address} is a {beds}-bedroom, {baths}-bath home "
    quick_summary += f"built in {year_built}, " if year_built != "N/A" else ""
    quick_summary += f"currently listed at {price}. "
    
    # Add features if available
    if notable_features:
        quick_summary += f"It features {features_text}. "
    
    # Add neighborhood info if available
    if neighborhood_info != "Limited neighborhood information available":
        quick_summary += f"The neighborhood {neighborhood_info} "
    
    # Add rental info if available
    rent_estimate = property_details["rent_estimate"]
    if rent_estimate and rent_estimate != "Not found":
        quick_summary += f"Estimated monthly rent: {rent_estimate}. "
    
    # Add comps summary if available
    if comps_summary:
        quick_summary += comps_summary
    
    # Store the raw data for potential JSON access
    json_data = json.dumps(analysis_data, indent=2)
    
    return quick_summary 