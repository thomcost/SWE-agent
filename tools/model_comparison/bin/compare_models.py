#!/usr/bin/env python3

import os
import sys
import json
import time
import argparse
import subprocess
import concurrent.futures
from datetime import datetime
from pathlib import Path

# Add parent directory to import path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))

def parse_args():
    parser = argparse.ArgumentParser(description="Compare different LLMs on the same task")
    parser.add_argument("--task", required=True, help="Task to run (GitHub issue URL, coding challenge, etc.)")
    parser.add_argument("--models", required=True, help="Comma-separated list of models to compare")
    parser.add_argument("--config", default="default.yaml", help="Config file to use")
    parser.add_argument("--output", default="model_comparison_results", help="Output directory for results")
    return parser.parse_args()

def parse_issue_url(url):
    """Parse GitHub issue URL into owner, repo, and issue number."""
    parts = url.strip("/").split("/")
    if "github.com" in parts and "issues" in parts:
        owner_idx = parts.index("github.com") + 1
        repo_idx = owner_idx + 1
        issue_idx = parts.index("issues") + 1
        return parts[owner_idx], parts[repo_idx], parts[issue_idx]
    return None, None, None

def run_model(model, task, config, output_dir):
    """Run SWE-agent with the specified model on the given task."""
    model_output_dir = os.path.join(output_dir, model.replace("/", "-"))
    os.makedirs(model_output_dir, exist_ok=True)
    
    # Set up environment variables for the model
    env = os.environ.copy()
    
    if "gpt" in model.lower() or "openai" in model.lower():
        provider = "openai"
    elif "claude" in model.lower() or "anthropic" in model.lower():
        provider = "anthropic"
    else:
        provider = "unknown"
    
    # Extract repository and issue information if it's a GitHub URL
    owner, repo, issue = parse_issue_url(task)
    
    # Build the command
    cmd = ["python", "-m", "sweagent", "run", "-c", config]
    
    if owner and repo and issue:
        cmd.extend(["--repo_name", f"{owner}/{repo}", "--issue_number", issue])
    else:
        cmd.extend(["--task", task])
    
    cmd.extend(["--model_provider", provider, "--model", model, "--output_dir", model_output_dir])
    
    # Run the command and capture output
    start_time = time.time()
    result = subprocess.run(cmd, env=env, capture_output=True, text=True)
    end_time = time.time()
    
    # Save results
    with open(os.path.join(model_output_dir, "run_info.json"), "w") as f:
        json.dump({
            "model": model,
            "task": task,
            "config": config,
            "start_time": datetime.fromtimestamp(start_time).isoformat(),
            "end_time": datetime.fromtimestamp(end_time).isoformat(),
            "duration": end_time - start_time,
            "success": result.returncode == 0,
            "returncode": result.returncode
        }, f, indent=2)
    
    with open(os.path.join(model_output_dir, "stdout.log"), "w") as f:
        f.write(result.stdout)
    
    with open(os.path.join(model_output_dir, "stderr.log"), "w") as f:
        f.write(result.stderr)
    
    return {
        "model": model,
        "success": result.returncode == 0,
        "duration": end_time - start_time
    }

def compare_results(results, output_dir):
    """Compare and summarize the results."""
    summary = {
        "task": args.task,
        "config": args.config,
        "timestamp": datetime.now().isoformat(),
        "results": results
    }
    
    # Sort by success and then by duration
    results.sort(key=lambda x: (-x["success"], x["duration"]))
    
    # Save summary
    with open(os.path.join(output_dir, "summary.json"), "w") as f:
        json.dump(summary, f, indent=2)
    
    # Generate summary report
    with open(os.path.join(output_dir, "summary.md"), "w") as f:
        f.write(f"# Model Comparison Results\n\n")
        f.write(f"Task: {args.task}\n")
        f.write(f"Config: {args.config}\n")
        f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("## Results Summary\n\n")
        f.write("| Rank | Model | Success | Duration (s) |\n")
        f.write("|------|-------|---------|-------------|\n")
        
        for i, result in enumerate(results, 1):
            success = "✅" if result["success"] else "❌"
            f.write(f"| {i} | {result['model']} | {success} | {result['duration']:.2f} |\n")
    
    return summary

if __name__ == "__main__":
    args = parse_args()
    models = [m.strip() for m in args.models.split(",")]
    output_dir = os.path.abspath(args.output)
    
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Starting comparison of {len(models)} models on task: {args.task}")
    print(f"Models: {', '.join(models)}")
    print(f"Results will be saved to: {output_dir}")
    
    results = []
    
    # Run models in parallel
    with concurrent.futures.ProcessPoolExecutor() as executor:
        futures = [executor.submit(run_model, model, args.task, args.config, output_dir) for model in models]
        
        for future in concurrent.futures.as_completed(futures):
            try:
                result = future.result()
                results.append(result)
                print(f"Completed run for {result['model']}: {'Successful' if result['success'] else 'Failed'} in {result['duration']:.2f} seconds")
            except Exception as e:
                print(f"Error running model: {e}")
    
    # Compare and summarize results
    summary = compare_results(results, output_dir)
    
    print("\nComparison complete!")
    print(f"Summary report saved to: {os.path.join(output_dir, 'summary.md')}")
    
    # Display summary table
    print("\nResults Summary:")
    for i, result in enumerate(summary["results"], 1):
        status = "SUCCESS" if result["success"] else "FAILED"
        print(f"{i}. {result['model']} - {status} - {result['duration']:.2f}s")