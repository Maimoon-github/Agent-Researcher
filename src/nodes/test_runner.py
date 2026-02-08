import logging
import sys
import os
import json
from source_discovery_agent import SourceDiscoveryAgent, SourceDiscoveryConfig

logging.basicConfig(level=logging.INFO)

def main():
    try:
        # scan current directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        config = SourceDiscoveryConfig(
            local_scan_directories=[current_dir],
            min_credibility_score=0.1 # Lower score just in case
        )
        
        agent = SourceDiscoveryAgent(config=config)
        
        query = "Impact of climate change on biodiversity"
        print(f"Running query: {query}")
        
        result = agent.discover_sources(
            query=query,
            query_id="test_002",
            source_type_preferences=["local"]
        )
        
        print(json.dumps(result, indent=2))
        
    except Exception as e:
        logging.error(f"Test failed: {e}", exc_info=2)

if __name__ == "__main__":
    main()
