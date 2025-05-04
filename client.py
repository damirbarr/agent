import requests
import argparse
import sys
import json
from typing import Optional

class ApiClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session_id = None
        self.cookies = {}
    
    def create_session(self) -> str:
        """Create a new session with the API"""
        response = requests.post(f"{self.base_url}/session")
        
        if response.status_code == 200:
            data = response.json()
            self.session_id = data["session_id"]
            
            # Save cookies for future requests
            self.cookies = response.cookies
            
            print(f"Session created: {self.session_id}")
            return self.session_id
        else:
            print(f"Error creating session: {response.text}")
            sys.exit(1)
    
    def send_query(self, query: str) -> dict:
        """Send a query to the AI agent"""
        if not self.session_id:
            self.create_session()
        
        response = requests.post(
            f"{self.base_url}/query",
            json={"query": query},
            cookies=self.cookies
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error processing query: {response.text}")
            return {"error": response.text}
    
    def send_command(self, command: str) -> dict:
        """Send a command to the AI agent"""
        if not self.session_id:
            self.create_session()
        
        response = requests.post(
            f"{self.base_url}/command",
            json={"command": command},
            cookies=self.cookies
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error executing command: {response.text}")
            return {"error": response.text}

def format_response(data: dict) -> str:
    """Format the response for display"""
    if "error" in data:
        return f"Error: {data['error']}"
    
    if "result" in data:  # Command response
        return data["result"]
    
    # Query response
    header = f"\n{'=' * 60}\n📋 TOPIC: {data['topic']}\n{'=' * 60}"
    
    answer_section = f"\n📌 ANSWER:\n{'-' * 60}\n{data['summary']}\n{'-' * 60}"
    
    reasoning_section = ""
    if data.get('reasoning'):
        reasoning_section = f"\n🔍 REASONING:\n{data['reasoning']}"
    
    sources = ", ".join(data['sources']) if data['sources'] else "None"
    tools_used = ", ".join(data['tools_used']) if data['tools_used'] else "None"
    metadata = f"\n📚 Sources: {sources}\n🛠️  Tools used: {tools_used}"
    
    return f"{header}{answer_section}{reasoning_section}{metadata}"

def interactive_mode(client: ApiClient):
    """Start an interactive session with the API"""
    print("AI Research Assistant CLI")
    print("Type 'exit' to quit, 'help' for available commands")
    
    client.create_session()
    
    while True:
        try:
            user_input = input("\n> ").strip()
            
            if user_input.lower() in ["exit", "quit", "bye"]:
                print("Goodbye!")
                break
            
            # Check if it's a command
            if user_input.lower() in ["help", "memory", "clear memory", "friendly mode"]:
                response = client.send_command(user_input)
                print(format_response(response))
            else:
                # Treat as a query
                response = client.send_query(user_input)
                print(format_response(response))
        
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")

def main():
    parser = argparse.ArgumentParser(description="Command-line client for AI Research Assistant API")
    parser.add_argument("--url", default="http://localhost:8000", help="Base URL for the API")
    parser.add_argument("--query", help="Send a single query and exit")
    parser.add_argument("--command", help="Send a single command and exit")
    
    args = parser.parse_args()
    
    client = ApiClient(base_url=args.url)
    
    if args.query:
        response = client.send_query(args.query)
        print(format_response(response))
    elif args.command:
        response = client.send_command(args.command)
        print(format_response(response))
    else:
        interactive_mode(client)

if __name__ == "__main__":
    main() 