"""Tool for exact codebase search using ripgrep."""
import subprocess
import asyncio
from typing import List, Optional, Type
import logging

from langchain_core.callbacks import CallbackManagerForToolRun
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool

logger = logging.getLogger(__name__)

def search_with_ripgrep(query: str, path: str = ".", file_types: Optional[List[str]] = None) -> str:
    """
    Searches for an exact string or regex pattern in a given path using ripgrep.

    Args:
        query: The exact string or regex pattern to search for.
        path: The directory or file to search in. Defaults to current directory.
        file_types: A list of file extensions to include in the search (e.g., ["py", "md"]).

    Returns:
        The search results from ripgrep, or an error message.
    """
    logger.debug(f"Searching for {query} in {path} with file types {file_types}")
    assert path is not None, "Path must be provided"
    command = ["rg", "--json", "--context", "3", "--max-count", "50"]

    if file_types:
        for ft in file_types:
            command.extend(["-g", f"*.{ft}"])
    
    command.append(query)
    command.append(path)

    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = process.communicate()

        if process.returncode == 0:
            logger.info(f"Search results: {stdout}")
            return stdout # ripgrep with --json outputs one JSON object per line for each match
        elif process.returncode == 1: # No matches found
            logger.warning(f"No matches found for query: {query} in path: {path}")
            return "No matches found."
        else:
            logger.error(f"Ripgrep error (return code {process.returncode}):\n{stderr}")
            return f"Ripgrep error (return code {process.returncode}):\n{stderr}"
    except FileNotFoundError:
        logger.error("Error: ripgrep command not found. Please ensure ripgrep is installed and in your PATH.")
        return "Error: ripgrep command not found. Please ensure ripgrep is installed and in your PATH."
    except Exception as e:
        logger.error(f"An error occurred during search: {str(e)}")
        return f"An error occurred during search: {str(e)}"


async def search_with_ripgrep_async(query: str, path: str = ".", file_types: Optional[List[str]] = None) -> str:
    """
    Asynchronously searches for an exact string or regex pattern in a given path using ripgrep.

    Args:
        query: The exact string or regex pattern to search for.
        path: The directory or file to search in. Defaults to current directory.
        file_types: A list of file extensions to include in the search (e.g., ["py", "md"]).

    Returns:
        The search results from ripgrep, or an error message.
    """
    logger.debug(f"Searching for {query} in {path} with file types {file_types}")
    assert path is not None, "Path must be provided"
    
    command = ["rg", "--json", "--context", "3", "--max-count", "50"]

    if file_types:
        for ft in file_types:
            command.extend(["-g", f"*.{ft}"])
    
    command.append(query)
    command.append(path)

    try:
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout_bytes, stderr_bytes = await process.communicate()
        stdout = stdout_bytes.decode()
        stderr = stderr_bytes.decode()

        if process.returncode == 0: # Success
            return stdout # ripgrep with --json outputs one JSON object per line for each match
        elif process.returncode == 1: # No matches found
            logger.warning(f"No matches found for query: {query} in path: {path}")
            return "No matches found."
        else:
            logger.error(f"Ripgrep error (return code {process.returncode}):\n{stderr}")
            return f"Ripgrep error (return code {process.returncode}):\n{stderr}"
    except FileNotFoundError:
        logger.error("Error: ripgrep command not found. Please ensure ripgrep is installed and in your PATH.")
        return "Error: ripgrep command not found. Please ensure ripgrep is installed and in your PATH."
    except Exception as e:
        logger.error(f"An error occurred during async search: {str(e)}")
        return f"An error occurred during async search: {str(e)}"


class CodebaseSearchInput(BaseModel):
    """Input for CodebaseSearchTool."""
    query: str = Field(description="The exact string or regex pattern to search for.")
    path: str = Field(default='.', description="The directory or file path to search within. Defaults to the current directory.")
    file_types: Optional[List[str]] = Field(default=None, description="Optional list of file extensions to filter by (e.g., ['py', 'js']).")

class CodebaseSearchTool(BaseTool):
    """Tool that performs an exact search in the codebase using ripgrep."""

    name: str = "codebase_exact_search"
    description: str = (
        "Searches for an exact string or regex pattern within the codebase (or a specified path). "
        "Returns matching lines with context. Powered by ripgrep. "
        "Use this for finding specific function names, variable names, or exact error messages."
    )
    args_schema: Type[BaseModel] = CodebaseSearchInput

    def _run(
        self,
        query: str,
        path: str = ".",
        file_types: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Use the tool."""
        return search_with_ripgrep(query, path, file_types)

    async def _arun(
        self,
        query: str,
        path: str = ".",
        file_types: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Use the tool asynchronously."""
        # For simplicity, calling the synchronous version.
        # A true async version would use asyncio.subprocess.
        return await search_with_ripgrep_async(query, path, file_types)


if __name__ == '__main__':
    # Create dummy files and directories for testing
    import os
    if not os.path.exists("test_dir"):
        os.makedirs("test_dir/subdir")

    with open("test_dir/sample.py", "w") as f:
        f.write("def hello_world():\n")
        f.write("    print(\"Hello, Python!\")\n")
        f.write("\n")
        f.write("class MyClass:\n")
        f.write("    pass\n")

    with open("test_dir/subdir/another.txt", "w") as f:
        f.write("This is a test file.\n")
        f.write("Another line with hello_world here.\n")
        f.write("Final line.\n")

    print("Testing search_with_ripgrep function:")
    
    print("\n1. Search for 'hello_world' in test_dir (all files):")
    print(search_with_ripgrep("hello_world", "test_dir"))

    print("\n2. Search for 'hello_world' in .py files in test_dir:")
    print(search_with_ripgrep("hello_world", "test_dir", file_types=["py"]))

    print("\n3. Search for 'MyClass' in test_dir/sample.py:")
    print(search_with_ripgrep("MyClass", "test_dir/sample.py"))
    
    print("\n4. Search for a non-existent term:")
    print(search_with_ripgrep("non_existent_term_xyz", "test_dir"))

    print("\n5. Search in a non-existent path:")
    print(search_with_ripgrep("hello_world", "non_existent_dir"))

    # Test the tool
    print("\nTesting CodebaseSearchTool:")
    tool = CodebaseSearchTool()

    result = tool.run({"query": "hello_world", "path": "test_dir", "file_types": ["txt"]})
    print(f"\nTool result for 'hello_world' in .txt files:\n{result}")
    
    result = tool.run({"query": "def hello_world"})
    print(f"\nTool result for 'def hello_world' in current dir (might find this test script itself):")
    print(result)

    print("\nTesting search_with_ripgrep_async function:")
    async def main_async_test():
        print("\nAsync 1. Search for 'hello_world' in test_dir (all files):")
        print(await search_with_ripgrep_async("hello_world", "test_dir"))

        print("\nAsync 2. Search for 'hello_world' in .py files in test_dir:")
        print(await search_with_ripgrep_async("hello_world", "test_dir", file_types=["py"]))

        print("\nAsync 3. Search for 'MyClass' in test_dir/sample.py:")
        print(await search_with_ripgrep_async("MyClass", "test_dir/sample.py"))
        
        print("\nAsync 4. Search for a non-existent term:")
        print(await search_with_ripgrep_async("non_existent_term_xyz_async", "test_dir"))

        print("\nAsync 5. Search in a non-existent path:")
        print(await search_with_ripgrep_async("hello_world", "non_existent_dir_async"))

        # Test the tool's arun method
        print("\nTesting CodebaseSearchTool._arun:")
        tool_instance = CodebaseSearchTool()
        
        arun_result_txt = await tool_instance._arun(query="hello_world", path="test_dir", file_types=["txt"])
        print(f"\nTool arun result for 'hello_world' in .txt files:\n{arun_result_txt}")
        
        arun_result_def = await tool_instance._arun(query="def hello_world")
        print(f"\nTool arun result for 'def hello_world' in current dir:\n{arun_result_def}")

    asyncio.run(main_async_test())

    # Clean up dummy files and directory
    if os.path.exists("test_dir/sample.py"):
        os.remove("test_dir/sample.py")
    if os.path.exists("test_dir/subdir/another.txt"):
        os.remove("test_dir/subdir/another.txt")
    if os.path.exists("test_dir/subdir"):
        os.rmdir("test_dir/subdir")
    if os.path.exists("test_dir"):
        os.rmdir("test_dir") 