"""Tool for reading specific lines from a file."""
from typing import Optional, Type
import logging

from langchain_core.callbacks import CallbackManagerForToolRun
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool

logger = logging.getLogger(__name__)

def read_lines_from_file(file_path: str, start_line: int, end_line: int) -> str:
    """
    Reads specified lines from a file.

    Args:
        file_path: The path to the file.
        start_line: The 1-based starting line number.
        end_line: The 1-based ending line number.

    Returns:
        The content of the specified lines, or an error message.
    """
    logger.debug(f"Reading lines from {file_path} from {start_line} to {end_line}")
    if start_line <= 0 or end_line <= 0:
        logger.error(f"Error: Line numbers must be positive. start_line: {start_line}, end_line: {end_line}")
        return "Error: Line numbers must be positive."
    if start_line > end_line:
        logger.error(f"Error: Start line cannot be greater than end line. start_line: {start_line}, end_line: {end_line}")
        return "Error: Start line cannot be greater than end line."

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Adjust to 0-based indexing for list access
        start_idx = start_line - 1
        end_idx = end_line

        if start_idx >= len(lines):
            return f"Error: Start line {start_line} is beyond the end of the file (total lines: {len(lines)})."
        
        # Ensure end_idx does not exceed the number of lines
        actual_end_idx = min(end_idx, len(lines))
        
        selected_lines = lines[start_idx:actual_end_idx]
        # logger.debug(f"Selected lines: {selected_lines}")
        logger.debug(f"{len(selected_lines)} lines selected")
        return "".join(selected_lines)
    except FileNotFoundError:
        logger.error(f"Error: File not found at {file_path}")
        return f"Error: File not found at {file_path}"
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        return f"An error occurred: {str(e)}"


class FileReadLinesInput(BaseModel):
    """Input for ReadFileLinesTool."""
    file_path: str = Field(description="The path to the file.")
    start_line: int = Field(description="The 1-based starting line number to read.")
    end_line: int = Field(description="The 1-based ending line number to read.")


class ReadFileLinesTool(BaseTool):
    """Tool that reads a specified range of lines from a file."""

    name: str = "read_file_lines"
    description: str = (
        "Reads lines from start_line to end_line (inclusive) from the specified file. "
        "Useful for fetching specific segments of code or text."
    )
    args_schema: Type[BaseModel] = FileReadLinesInput

    def _run(
        self,
        file_path: str,
        start_line: int,
        end_line: int,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Use the tool."""
        return read_lines_from_file(file_path, start_line, end_line)

    async def _arun(
        self,
        file_path: str,
        start_line: int,
        end_line: int,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Use the tool asynchronously."""
        # For simplicity, we're calling the synchronous version.
        # For a truly async implementation, use aiofiles or similar.
        return read_lines_from_file(file_path, start_line, end_line)

if __name__ == '__main__':
    # Example Usage
    # Create a dummy file
    dummy_file_path = "dummy_test_file.txt"
    with open(dummy_file_path, "w") as f:
        f.write("Line 1\n")
        f.write("Line 2\n")
        f.write("Line 3\n")
        f.write("Line 4\n")
        f.write("Line 5\n")

    # Test the function
    print("Testing read_lines_from_file function:")
    print(f"Reading lines 2-4:\n{read_lines_from_file(dummy_file_path, 2, 4)}")
    print(f"Reading line 1:\n{read_lines_from_file(dummy_file_path, 1, 1)}")
    print(f"Reading lines 4-6 (beyond EOF):\n{read_lines_from_file(dummy_file_path, 4, 6)}")
    print(f"Reading non-existent file:\n{read_lines_from_file('non_existent.txt', 1, 2)}")
    print(f"Invalid range (start > end):\n{read_lines_from_file(dummy_file_path, 3, 2)}")
    print(f"Invalid range (start_line=0):\n{read_lines_from_file(dummy_file_path, 0, 2)}")


    # Test the tool
    print("\nTesting ReadFileLinesTool:")
    tool = ReadFileLinesTool()
    
    result = tool.run({"file_path": dummy_file_path, "start_line": 2, "end_line": 3})
    print(f"Tool result for lines 2-3:\n{result}")

    result = tool.run({"file_path": "non_existent.txt", "start_line": 1, "end_line": 1})
    print(f"Tool result for non_existent.txt:\n{result}")
    
    # Clean up dummy file
    import os
    os.remove(dummy_file_path) 