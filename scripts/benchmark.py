"""
Performance Benchmark Tool

Measures processing time and resource usage for agent execution.
"""

import time
import psutil
import statistics
from src.core.orchestrator import ProcessOrchestrator

def measure_execution(query: str):
    print(f"Benchmarking query: {query}")
    
    # Start resource monitoring
    process = psutil.Process()
    start_cpu = process.cpu_percent()
    start_mem = process.memory_info().rss / 1024 / 1024
    
    start_time = time.time()
    
    # Run orchestrator
    orchestrator = ProcessOrchestrator()
    result = orchestrator.run(query)
    
    end_time = time.time()
    end_mem = process.memory_info().rss / 1024 / 1024
    end_cpu = process.cpu_percent()
    
    duration = end_time - start_time
    
    print("\n--- Benchmark Results ---")
    print(f"Total Duration: {duration:.2f}s")
    print(f"Success: {result['success']}")
    print(f"Quality Score: {result.get('quality_score', 0):.2f}")
    print(f"Memory Usage: {end_mem - start_mem:.2f} MB (diff)")
    print(f"CPU Usage: {end_cpu - start_cpu:.2f}% (diff)")
    
    # Node breakdown
    if "metrics" in result:
        timings = result["metrics"].get("node_timings", {})
        print("\nNode Timings:")
        for node, stats in timings.items():
            print(f"  {node}: {stats.get('avg_ms', 0)}ms (avg)")

if __name__ == "__main__":
    queries = [
        "What is the history of the internet?",
        "Explain machine learning basics",
    ]
    
    for q in queries:
        measure_execution(q)
