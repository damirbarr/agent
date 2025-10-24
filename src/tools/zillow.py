import logging
from typing import Dict, Any, Optional, List, Union
from browser_use import Agent as BrowserAgent
from src.config import ModelConfig

logger = logging.getLogger(__name__)

# Module-level caches that persist across instances
_SEARCH_CACHE = {}
_DETAILS_CACHE = {}

class ZillowPropertySearch:
    """Tool for searching properties on Zillow using browser-use."""

    def __init__(self, llm=None):
        """
        Initialize the ZillowPropertySearch.

        Args:
            llm: Optional LLM instance. If not provided, uses ModelConfig.get_browser_llm()
        """
        self.llm = llm or ModelConfig.get_browser_llm()
        # Use module-level caches instead of instance-level
        self._search_cache = _SEARCH_CACHE
        self._details_cache = _DETAILS_CACHE

        # Log model configuration
        model_info = ModelConfig.get_model_info()
        logger.info(f"🤖 ZillowPropertySearch initialized with {model_info['provider']} - {model_info['browser_model']}")
    
    async def search_property(self, location: str) -> Dict[str, Any]:
        """
        Search for properties in a given location and return basic search results.
        
        Args:
            location: Address, city, zip code, or neighborhood
            
        Returns:
            Dict with search results or error information
        """
        # Caching logic
        if location in self._search_cache:
            return self._search_cache[location]
        try:
            agent = BrowserAgent(
                task=f"Search for properties in {location} on Zillow. Extract the first 5 property listings with their address, price, details (beds/baths/sqft), and link URLs.",
                llm=self.llm,
            )
            result = await agent.run()
            properties = []
            if isinstance(result, dict) and "properties" in result:
                for prop in result.get("properties", [])[:5]:
                    properties.append({
                        "address": prop.get("address", "Address not available"),
                        "price": prop.get("price", "Price not available"),
                        "details": prop.get("details", "Details not available"),
                        "link": prop.get("link", None)
                    })
            if not properties:
                import re
                result_str = str(result)
                addresses = re.findall(r'Address: (.*?)(?:\n|$)', result_str)
                prices = re.findall(r'Price: (.*?)(?:\n|$)', result_str)
                details = re.findall(r'Details: (.*?)(?:\n|$)', result_str)
                links = re.findall(r'Link: (https://www\.zillow\.com/.*?)(?:\n|$)', result_str)
                for i in range(min(len(addresses), len(prices), 5)):
                    properties.append({
                        "address": addresses[i] if i < len(addresses) else "Address not available",
                        "price": prices[i] if i < len(prices) else "Price not available",
                        "details": details[i] if i < len(details) and i < len(details) else "Details not available",
                        "link": links[i] if i < len(links) else None
                    })
            if not properties:
                result_obj = {
                    "success": False,
                    "error": "No properties found or data extraction failed",
                    "message": "Try a different location or more specific search terms"
                }
                self._search_cache[location] = result_obj
                return result_obj
            search_url = f"https://www.zillow.com/homes/{location.replace(' ', '-').lower()}_rb/"
            result_obj = {
                "success": True,
                "location": location,
                "properties": properties,
                "search_url": search_url
            }
            self._search_cache[location] = result_obj
            return result_obj
        except Exception as e:
            logger.error(f"Error searching Zillow: {e}")
            result_obj = {
                "success": False,
                "error": str(e),
                "message": "An error occurred while searching Zillow"
            }
            self._search_cache[location] = result_obj
            return result_obj
    
    async def get_property_details(self, property_url: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific property.
        
        Args:
            property_url: URL of the property on Zillow
            
        Returns:
            Dict with property details or error information
        """
        # Caching logic
        if property_url in self._details_cache:
            return self._details_cache[property_url]
        try:
            agent = BrowserAgent(
                task=f"Visit this Zillow property page: {property_url}. Extract and organize all property details including: address, price, beds, baths, square footage, description, features list, and image URLs.",
                llm=self.llm,
            )
            
            result = await agent.run()
            
            # Default details structure
            details = {
                "address": "Address not available",
                "price": "Price not available",
                "beds": "Beds not available",
                "baths": "Baths not available",
                "sqft": "Square footage not available",
                "description": "Description not available",
                "features": ["Features not available"],
                "image_urls": ["Images not available"]
            }
            
            # Update with extracted information
            if isinstance(result, dict):
                if "address" in result:
                    details["address"] = result["address"]
                if "price" in result:
                    details["price"] = result["price"]
                if "beds" in result:
                    details["beds"] = result["beds"]
                if "baths" in result:
                    details["baths"] = result["baths"]
                if "sqft" in result:
                    details["sqft"] = result["sqft"]
                if "description" in result:
                    details["description"] = result["description"]
                if "features" in result and isinstance(result["features"], list):
                    details["features"] = result["features"]
                if "image_urls" in result and isinstance(result["image_urls"], list):
                    details["image_urls"] = result["image_urls"]
            else:
                # Try to parse the raw text result
                import re
                result_str = str(result)
                address_match = re.search(r'Address: (.*?)(?:\n|$)', result_str)
                if address_match:
                    details["address"] = address_match.group(1)
                price_match = re.search(r'Price: (.*?)(?:\n|$)', result_str)
                if price_match:
                    details["price"] = price_match.group(1)
                beds_match = re.search(r'Beds: (.*?)(?:\n|$)', result_str)
                if beds_match:
                    details["beds"] = beds_match.group(1)
                baths_match = re.search(r'Baths: (.*?)(?:\n|$)', result_str)
                if baths_match:
                    details["baths"] = baths_match.group(1)
                sqft_match = re.search(r'Square footage: (.*?)(?:\n|$)', result_str)
                if sqft_match:
                    details["sqft"] = sqft_match.group(1)
                desc_match = re.search(r'Description:(.*?)(?:Features:|$)', result_str, re.DOTALL)
                if desc_match:
                    details["description"] = desc_match.group(1).strip()
                # Extract features
                features_match = re.search(r'Features:(.*?)(?:Image URLs:|$)', result_str, re.DOTALL)
                if features_match:
                    features_text = features_match.group(1).strip()
                    features_list = [f.strip() for f in features_text.split('\n-') if f.strip()]
                    if features_list:
                        details["features"] = features_list
                # Extract image URLs
                image_urls_match = re.findall(r'https://[^\s]+\.jpg', result_str)
                if image_urls_match:
                    details["image_urls"] = image_urls_match
            
            return {
                "success": True,
                "property_url": property_url,
                "details": details
            }
            
        except Exception as e:
            logger.error(f"Error getting property details: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "An error occurred while getting property details"
            }

# Wrapper functions to use with LangChain
async def _search_zillow(location: str) -> str:
    """Internal async implementation of Zillow search"""
    searcher = ZillowPropertySearch()
    results = await searcher.search_property(location)
    
    if not results["success"]:
        return f"Error searching Zillow: {results['error']}. {results['message']}"
    
    # Format the results for output
    properties_info = []
    for idx, prop in enumerate(results["properties"], 1):
        properties_info.append(
            f"Property {idx}:\n"
            f"  Address: {prop['address']}\n"
            f"  Price: {prop['price']}\n"
            f"  Details: {prop['details']}\n"
            f"  Link: {prop['link'] if prop['link'] else 'Not available'}\n"
        )
    
    formatted_result = (
        f"Zillow Search Results for '{results['location']}':\n\n"
        f"{'\n'.join(properties_info)}\n"
        f"Search URL: {results['search_url']}"
    )
    
    return formatted_result

async def _get_zillow_details(property_url: str) -> str:
    """Internal async implementation of Zillow property details"""
    searcher = ZillowPropertySearch()
    results = await searcher.get_property_details(property_url)
    
    if not results["success"]:
        return f"Error getting property details: {results['error']}. {results['message']}"
    
    details = results["details"]
    
    # Format the features list
    features_formatted = "\n  - ".join(details["features"])
    
    formatted_result = (
        f"Property Details for {details['address']}:\n\n"
        f"Price: {details['price']}\n"
        f"Beds: {details['beds']}\n"
        f"Baths: {details['baths']}\n"
        f"Size: {details['sqft']}\n\n"
        f"Description:\n{details['description']}\n\n"
        f"Features:\n  - {features_formatted}\n\n"
        f"Property URL: {results['property_url']}"
    )
    
    return formatted_result

# Synchronous wrapper functions for tool integration
import asyncio

def search_zillow_properties(location: str) -> str:
    """
    Search for properties on Zillow based on location using browser-use.
    
    Args:
        location: Address, city, zip code, or neighborhood
        
    Returns:
        String with property information or error message
    """
    return asyncio.run(_search_zillow(location))

def get_zillow_property_details(property_url: str) -> str:
    """
    Get detailed information about a specific property on Zillow using browser-use.

    Args:
        property_url: URL of the property on Zillow

    Returns:
        String with detailed property information or error message
    """
    return asyncio.run(_get_zillow_details(property_url))

# Cache management functions
def clear_zillow_cache():
    """Clear all cached Zillow search and property details."""
    global _SEARCH_CACHE, _DETAILS_CACHE
    _SEARCH_CACHE.clear()
    _DETAILS_CACHE.clear()
    logger.info("Cleared Zillow caches")

def get_cache_stats() -> Dict[str, int]:
    """Get statistics about cached items."""
    return {
        "search_cache_size": len(_SEARCH_CACHE),
        "details_cache_size": len(_DETAILS_CACHE)
    } 