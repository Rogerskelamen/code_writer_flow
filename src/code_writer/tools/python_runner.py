import subprocess
import sys
import os
from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field


class PythonRunnerInput(BaseModel):
    """Input schema for PythonRunner."""
    file_path: str = Field(..., description="Path to the Python file to run")
    args: str = Field(default="", description="Command line arguments for the Python script")


class TestRunner(BaseTool):
    name: str = "Python Code Runner"
    description: str = (
        "Execute Python files and return the output. "
        "Useful for running test files, scripts, or any Python code. "
        "Returns both stdout and stderr output."
    )
    args_schema: Type[BaseModel] = PythonRunnerInput

    def _run(self, file_path: str, args: str = "") -> str:
        """Execute a Python file and return the output."""
        try:
            # Handle relative paths properly
            if not os.path.isabs(file_path):
                # If it's a relative path, make it relative to current working directory
                file_path = os.path.abspath(file_path)

            # Check if file exists
            if not os.path.exists(file_path):
                return f"Error: File '{file_path}' not found."

            # Build the command
            cmd = [sys.executable, file_path]
            if args.strip():
                cmd.extend(args.split())

            # Run the Python file
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10,  # 10 second timeout
                cwd=os.getcwd()  # Use current working directory
            )

            # Format the output
            output = ""
            if result.stdout:
                output += f"STDOUT:\n{result.stdout}\n"
            if result.stderr:
                output += f"STDERR:\n{result.stderr}\n"

            output += f"Return Code: {result.returncode}\n"

            if result.returncode == 0:
                output += "✅ Execution successful!"
            else:
                output += "❌ Execution failed!"

            return output

        except subprocess.TimeoutExpired:
            return "Error: Script execution timed out (10 seconds limit)."
        except Exception as e:
            return f"Error executing Python file: {str(e)}"
