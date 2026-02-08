"""
Agent Researcher - Main Entry Point

Provides CLI interface and continuous loop execution.
"""

import sys
import time
import argparse
from pathlib import Path
from typing import Optional

from loguru import logger

from .core.config import Config, get_config, reload_config
from .core.orchestrator import ProcessOrchestrator
from .core.llm_manager import get_llm_manager
from .nodes.logging_node import LoggingNode


def setup_logging(config: Config):
    """Initialize logging configuration."""
    LoggingNode.configure_logging(config)


def check_ollama_connection(config: Config) -> bool:
    """Check if Ollama is running and accessible."""
    import httpx
    
    try:
        with httpx.Client(timeout=5) as client:
            response = client.get(f"{config.llm.ollama_base_url}/api/tags")
            if response.status_code == 200:
                models = response.json().get("models", [])
                logger.info(f"Ollama connected. {len(models)} models available.")
                return True
    except Exception as e:
        logger.error(f"Cannot connect to Ollama at {config.llm.ollama_base_url}: {e}")
    
    return False


def run_single(
    query: str,
    output_format: str = "markdown",
    config_path: Optional[str] = None,
) -> dict:
    """Run a single research query."""
    config = reload_config(config_path) if config_path else get_config()
    setup_logging(config)
    
    if not check_ollama_connection(config):
        logger.error("Ollama is not available. Please start Ollama first.")
        return {"success": False, "error": "Ollama not available"}
    
    orchestrator = ProcessOrchestrator(config)
    result = orchestrator.run(query, output_format)
    
    return result


def run_continuous_loop(
    config_path: Optional[str] = None,
    interval_minutes: int = 60,
):
    """
    Run the agent in a continuous loop.
    
    In continuous mode, the agent:
    1. Refreshes knowledge base
    2. Processes any queued queries
    3. Generates scheduled reports
    4. Sleeps until next interval
    """
    config = reload_config(config_path) if config_path else get_config()
    setup_logging(config)
    
    logger.info("=" * 60)
    logger.info("Agent Researcher - Continuous Mode")
    logger.info("=" * 60)
    
    if not check_ollama_connection(config):
        logger.error("Ollama is not available. Please start Ollama first.")
        return
    
    orchestrator = ProcessOrchestrator(config)
    iteration = 0
    
    # Example: predefined research topics for continuous operation
    scheduled_topics = [
        "Latest developments in artificial intelligence research",
        "Recent advances in renewable energy technology",
        "Current trends in software development practices",
    ]
    
    try:
        while True:
            iteration += 1
            logger.info(f"\n{'='*60}")
            logger.info(f"Continuous Loop - Iteration {iteration}")
            logger.info(f"{'='*60}")
            
            # Rotate through topics
            topic_index = (iteration - 1) % len(scheduled_topics)
            query = scheduled_topics[topic_index]
            
            logger.info(f"Processing: {query}")
            
            try:
                result = orchestrator.run(query, "markdown")
                
                if result.get("success"):
                    logger.info(f"✓ Document generated: {result.get('output_path')}")
                    logger.info(f"  Quality score: {result.get('quality_score', 0):.2f}")
                else:
                    logger.warning(f"✗ Generation failed: {result.get('error')}")
                
                # Log LLM stats
                llm = get_llm_manager()
                stats = llm.get_stats()
                logger.info(f"  Model: {stats['current_model']}")
                logger.info(f"  Total tokens: {stats['total_tokens_used']}")
                logger.info(f"  Model switches: {stats['model_switches']}")
                
            except Exception as e:
                logger.error(f"Error in iteration {iteration}: {e}")
            
            # Sleep until next interval
            logger.info(f"\nSleeping for {interval_minutes} minutes...")
            time.sleep(interval_minutes * 60)
            
    except KeyboardInterrupt:
        logger.info("\nShutting down continuous loop...")
        logger.info(f"Completed {iteration} iterations")


def run_interactive():
    """Run in interactive mode with user input."""
    config = get_config()
    setup_logging(config)
    
    logger.info("=" * 60)
    logger.info("Agent Researcher - Interactive Mode")
    logger.info("=" * 60)
    
    if not check_ollama_connection(config):
        logger.error("Ollama is not available. Please start Ollama first.")
        return
    
    orchestrator = ProcessOrchestrator(config)
    
    print("\nWelcome to Agent Researcher!")
    print("Enter your research query (or 'quit' to exit)")
    print("-" * 40)
    
    while True:
        try:
            query = input("\nQuery: ").strip()
            
            if query.lower() in ("quit", "exit", "q"):
                print("Goodbye!")
                break
            
            if not query:
                continue
            
            print(f"\nProcessing: {query[:50]}...")
            
            result = orchestrator.run(query, "markdown")
            
            if result.get("success"):
                print(f"\n✓ Document generated!")
                print(f"  Path: {result.get('output_path')}")
                print(f"  Quality: {result.get('quality_score', 0):.2%}")
            else:
                print(f"\n✗ Failed: {result.get('error')}")
            
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Agent Researcher - Autonomous Research Agent System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run single query
  python -m src.main --query "Latest AI research developments"
  
  # Run in interactive mode
  python -m src.main --interactive
  
  # Run in continuous mode
  python -m src.main --continuous --interval 30
  
  # Specify output format
  python -m src.main --query "Research topic" --format pdf
        """,
    )
    
    parser.add_argument(
        "--query", "-q",
        type=str,
        help="Research query to process",
    )
    
    parser.add_argument(
        "--format", "-f",
        type=str,
        choices=["markdown", "md", "pdf", "docx", "html"],
        default="markdown",
        help="Output format (default: markdown)",
    )
    
    parser.add_argument(
        "--config", "-c",
        type=str,
        help="Path to configuration file",
    )
    
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Run in interactive mode",
    )
    
    parser.add_argument(
        "--continuous",
        action="store_true",
        help="Run in continuous loop mode",
    )
    
    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Interval in minutes for continuous mode (default: 60)",
    )
    
    args = parser.parse_args()
    
    if args.continuous:
        run_continuous_loop(args.config, args.interval)
    elif args.interactive:
        run_interactive()
    elif args.query:
        result = run_single(args.query, args.format, args.config)
        if result.get("success"):
            print(f"\n✓ Success! Output: {result.get('output_path')}")
            sys.exit(0)
        else:
            print(f"\n✗ Failed: {result.get('error')}")
            sys.exit(1)
    else:
        parser.print_help()
        print("\nNo action specified. Use --query, --interactive, or --continuous")
        sys.exit(1)


if __name__ == "__main__":
    main()
