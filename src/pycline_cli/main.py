import os
import sys
import argparse
import asyncio
from pycline import PyCline


async def async_main():
    parser = argparse.ArgumentParser(description="Anthropic CLI: Interact with Claude AI")
    parser.add_argument("prompt", type=str, help="Enter a prompt to send to Claude")
    args = parser.parse_args()

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("API key must be provided either directly or through ANTHROPIC_API_KEY environment variable")
    client = PyCline(
        api_provider="anthropic", 
        api_key=api_key,
        model_id="claude-3-5-sonnet-20241022")
    await client.resume_task(args.prompt)
    print(f"\nClaude's Done. cost: {client.get_cost()}")


def main():
    return asyncio.run(async_main())


if __name__ == "__main__":
    sys.exit(main())
