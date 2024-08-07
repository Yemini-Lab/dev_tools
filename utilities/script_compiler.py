import os
import subprocess
from pathlib import Path

hidden_imports = [
    'xml.etree',
    'xml.etree.ElementTree',
    'scikit-image',
    'mx.DateTime'
]


def list_python_files(path):
    files = os.listdir(path)
    python_files = [file for file in files if file.endswith('.py')]
    return python_files


# Define directories using Path
npal_directory = Path('C:/Users/YeminiPC/Documents/GitHub/NeuroPAL_ID')
script_directory = npal_directory / '+Wrapper'
distribution_directory = script_directory / 'dist'
compile_directory = npal_directory.parent.parent / 'win_visualize' / 'for_redistribution_files_only' / 'lib'

# List Python files in the directory
python_files = list_python_files(script_directory)

# Add Python files to hidden imports
hidden_imports.extend(python_files)

# Process each Python file
for file in python_files:
    file_path = script_directory / file
    cmd = f"pyinstaller {file_path}"

    # Add hidden imports to the command
    hidden_imports_string = ' '.join(f"--hidden-import={eachImport[:-3]}" for eachImport in hidden_imports)
    cmd += f" {hidden_imports_string} --onefile"

    print(cmd)

    subprocess.call(cmd, shell=True)

    # Define source and destination directories for moving files
    source_dir = distribution_directory
    destination_dir = compile_directory

    # Move files from source to destination
    print(f"\nMove from {source_dir} to {destination_dir}\n\n")
