import os
import subprocess
from typing import Optional
from langchain.tools import tool
from app.utils import constants

@tool
def create_directory(local_repo_path: str, dir_path: str) -> str:
    """
    Create a new writable directory with the given directory name if it does not exist.
    If the directory exists, it ensures the directory is writable.

    Parameters:
        local_repo_path (str): The path to the local directory storing the github repository.
        dir_path (str): The path of the directory to create.

    Returns:
        str: Success or error message.
    """
    if ".." in dir_path:
        return f"Cannot make a directory with '..' in path"
    full_dir_path = os.path.join(local_repo_path, dir_path)
    try:
        os.makedirs(full_dir_path, exist_ok=True)
        subprocess.run(["chmod", "u+w", full_dir_path], check=True)
        return f"Directory successfully '{full_dir_path}' created and set as writeable."
    except subprocess.CalledProcessError as e:
        return f"Failed to create or set writable directory '{full_dir_path}': {e}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"


@tool
def find_file(local_repo_path: str, file_name: str) -> Optional[str]:
    """
    Recursively searches for a file in the given path.
    Returns string of full path to file, or None if file not found.

    Parameters:
        local_repo_path (str): The path to the local directory storing the github repository.
        file_name (str): The name of the file.

    Returns:
        str: The path to the file
    """
    # FIXME handle multiple matches
    for root, _, files in os.walk(local_repo_path):
        if file_name in files:
            return os.path.join(root, file_name)
    return None


@tool
def create_file(local_repo_path: str, file_name: str, content: str = "", dir_path=""):
    """
    Creates a new file and content in the specified directory.

    Parameters:
        local_repo_path (str): The path to the local directory storing the github repository.
        file_name (str): The name of the file.
        content (str): The content of the file.
        dir_path (str): The directory path for the file.

    Returns:
        str: A message indicating the result of the operation.
    """
    # Validate file type
    try:
        _, file_type = file_name.split(".")
        assert file_type in constants.VALID_FILE_TYPES
    except:
        return f"Invalid filename {file_name} - must end with a valid file type: {constants.VALID_FILE_TYPES}"
    full_dir_path = os.path.join(local_repo_path, dir_path)
    file_path = os.path.join(full_dir_path, file_name)
    if not os.path.exists(file_path):
        try:
            with open(file_path, "w")as file:
                file.write(content)
            print(f"File '{file_name}' created successfully at: '{file_path}'.")
            return f"File '{file_name}' created successfully at: '{file_path}'."
        except Exception as e:
            print(f"Failed to create file '{file_name}' at: '{file_path}': {str(e)}")
            return f"Failed to create file '{file_name}' at: '{file_path}': {str(e)}"
    else:
        print(f"File '{file_name}' already exists at: '{file_path}'.")
        return f"File '{file_name}' already exists at: '{file_path}'."


@tool
def update_file(local_repo_path: str, file_name: str, content: str, dir_path: str = ""):
    """
    Updates, appends, or modifies an existing file with new content.

    Parameters:
        local_repo_path (str): The path to the local directory storing the github repository.
        file_name (str): The name of the file.
        content (str): The content of the file.
        dir_path (str): The directory path for the file.

    Returns:
        str: A message indicating the result of the operation.
    """
    if dir_path:
        file_path = os.path.join(local_repo_path, dir_path, file_name)
    else:
        file_path = find_file(local_repo_path, file_name)

    if file_path and os.path.exists(file_path):
        try:
            with open(file_path, "a") as file:
                file.write(content)
            return f"File '{file_name}' updated successfully at: '{file_path}'"
        except Exception as e:
            return f"Failed to update file '{file_name}' at: '{file_path}' - {str(e)}"
    else:
        return f"File '{file_name}' not found at: '{file_path}'"


@tool
def create_or_update_file(local_repo_path: str, file_name: str, content: str = "", dir_path=""):
    """
    Creates or updates a file with the specified content in the specified directory.

    Parameters:
        local_repo_path (str): The path to the local directory storing the github repository.
        file_name (str): The name of the file.
        content (str): The content of the file.
        dir_path (str): The directory path for the file.

    Returns:
        str: A message indicating the result of the operation.
    """
    # Validate file type
    try:
        _, file_type = file_name.split(".")
        assert file_type in constants.VALID_FILE_TYPES
    except:
        return f"Invalid filename {file_name} - must end with a valid file type: {constants.VALID_FILE_TYPES}"
    full_dir_path = os.path.join(local_repo_path, dir_path)
    file_path = os.path.join(full_dir_path, file_name)
    if os.path.exists(file_path):
        try:
            with open(file_path, "w") as file:
                file.write(content)
            return f"File '{file_name}' updated successfully at: '{file_path}'"
        except Exception as e:
            return f"Failed to update file '{file_name}' at: '{file_path}' - {str(e)}"
    else:
        try:
            with open(file_path, "w")as file:
                file.write(content)
            print(f"File '{file_name}' created successfully at: '{file_path}'.")
            return f"File '{file_name}' created successfully at: '{file_path}'."
        except Exception as e:
            print(f"Failed to create file '{file_name}' at: '{file_path}': {str(e)}")
            return f"Failed to create file '{file_name}' at: '{file_path}': {str(e)}"
