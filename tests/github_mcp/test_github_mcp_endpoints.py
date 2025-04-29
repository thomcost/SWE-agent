#!/usr/bin/env python3
"""
Simple script to test GitHub MCP Server endpoints directly.
"""

import sys
import time
import requests
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("github-mcp-endpoints-test")

def test_endpoints(host="localhost", port=7444):
    """Test basic GitHub MCP Server endpoints."""
    base_url = f"http://{host}:{port}"
    
    endpoints = [
        "/",
        "/mcp",
        "/mcp/v1",
        "/mcp/v1/ping",
        "/mcp/v1/schema",
        "/mcp/v1/tools"
    ]
    
    logger.info(f"Testing GitHub MCP Server endpoints on {base_url}")
    success = False
    
    for endpoint in endpoints:
        url = f"{base_url}{endpoint}"
        logger.info(f"Testing endpoint: {url}")
        
        try:
            response = requests.get(url, timeout=5)
            logger.info(f"Response status code: {response.status_code}")
            
            if response.status_code == 200:
                success = True
                logger.info("Endpoint responded successfully!")
                try:
                    logger.info(f"Response content type: {response.headers.get('Content-Type', 'unknown')}")
                    if "application/json" in response.headers.get("Content-Type", ""):
                        logger.info(f"Response JSON: {response.json()}")
                    else:
                        logger.info(f"Response text: {response.text[:200]}...")
                except Exception as e:
                    logger.error(f"Error parsing response: {e}")
            else:
                logger.warning(f"Endpoint returned non-200 status: {response.status_code}")
                logger.warning(f"Response text: {response.text[:200]}...")
        except requests.RequestException as e:
            logger.error(f"Error connecting to endpoint: {e}")
    
    if success:
        logger.info("At least one endpoint responded successfully")
    else:
        logger.error("All endpoints failed to respond")
        
    return success

if __name__ == "__main__":
    # Get host and port from command line arguments if provided
    host = sys.argv[1] if len(sys.argv) > 1 else "localhost"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 7444
    
    # Test endpoints continuously until Ctrl+C is pressed
    try:
        logger.info("Press Ctrl+C to stop testing")
        while True:
            test_endpoints(host, port)
            logger.info("Waiting 5 seconds before next test...")
            time.sleep(5)
    except KeyboardInterrupt:
        logger.info("Testing stopped by user")