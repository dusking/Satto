import os
import sys
import argparse
import asyncio
import textwrap
from importlib.metadata import version
from satto import Satto


async def async_main():
    parser = argparse.ArgumentParser(description="Anthropic CLI: Interact with Claude AI")
    parser.add_argument('--version', action='version', version=f'satto {version("satto")}')
    subparsers = parser.add_subparsers(dest='command', required=True)
    
    # Start command
    start_parser = subparsers.add_parser('start', help='Start a new task')
    start_parser.add_argument("prompt", type=str, help="Enter a prompt to send to Claude")
    
    # Continue command
    resume_parser = subparsers.add_parser('cont', help='Continue an existing task')
    resume_parser.add_argument("prompt", type=str, help="Enter a prompt to send to Claude")
    
    args = parser.parse_args()    
    client = Satto(api_provider="anthropic")
    
    if args.command == 'start':
        await client.start_task(args.prompt)
    else:  # resume
        await client.resume_task(args.prompt)
    print(textwrap.dedent(f"""Claude's Done. 
cost: {client.get_cost()}.
task_id: {client.get_task_id()}."""))


def main():
    return asyncio.run(async_main())


if __name__ == "__main__":
    sys.exit(main())
