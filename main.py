import sys
import argparse
import asyncio
import importlib

async def main():
    parser = argparse.ArgumentParser(description="ClawBot Command Dispatcher")
    parser.add_argument("command", help="The command to run (e.g., example_task)")
    parser.add_argument("--args", help="Arguments for the command", nargs="*")
    
    args = parser.parse_args()
    
    try:
        # Import the command module dynamically
        module_path = f"src.commands.{args.command}"
        command_module = importlib.import_module(module_path)
        
        if hasattr(command_module, "run"):
            await command_module.run(args.args)
        else:
            print(f"Error: Command '{args.command}' does not have a 'run' function.")
            
    except ImportError as e:
        print(f"Error: Command '{args.command}' not found. {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(main())
