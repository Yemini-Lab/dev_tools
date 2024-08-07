import os
import platform
import subprocess
from pathlib import Path
import shutil

# List of hidden imports
hidden_imports = [
    'xml.etree',
    'xml.etree.ElementTree',
    'scikit-image',
    'mx.DateTime'
]

def list_python_files(path):
    """List all Python files in the given directory."""
    files = os.listdir(path)
    python_files = [file for file in files if file.endswith('.py')]
    return python_files

# Define directories using Path
npal_directory = Path('C:/Users/YeminiPC/Documents/GitHub/NeuroPAL_ID')
script_directory = npal_directory / '+Wrapper'
distribution_directory = script_directory / 'dist'
compile_directory = npal_directory / 'win_visualize' / 'for_redistribution_files_only' / 'lib' / 'bin' / platform.system().lower()

# List Python files in the directory
python_files = list_python_files(script_directory)

# Add Python files to hidden imports
hidden_imports.extend(python_files)

# Process each Python file
for file in python_files:
    file_path = script_directory / file
    cmd = f"pyinstaller {file_path}"

    # Add hidden imports to the command
    hidden_imports_string = ' '.join(f"--hidden-import={import_name}" for import_name in hidden_imports)
    cmd += f" {hidden_imports_string} --onefile"

    # Execute the command
    subprocess.call(cmd, shell=True)

    # Define source and destination paths for moving files
    source_file = distribution_directory / file.replace('.py', '.exe')
    destination_file = compile_directory / file.replace('.py', '.exe')

    # Move files from source to destination
    try:
        shutil.move(str(source_file), str(destination_file))
        print(f"Successfully compiled {destination_file}.\n")
    except FileNotFoundError:
        print(f"ERROR: Compilation failed for {source_file}...\n")