import os
import h5py
import hdmf
import pynwb
import shutil
import platform
import subprocess
from pathlib import Path


def clear_cache(path):
    """Deletes all pyinstaller-related cache files."""
    for root, dirs, files in os.walk(path, topdown=False):
        for file in files:
            if file.endswith('.spec'):
                file_path = os.path.join(root, file)
                os.remove(file_path)
                print(f"Deleted file: {file_path}")

        for dir_name in dirs:
            if dir_name in ('build', 'dist', '__pycache__'):
                dir_path = os.path.join(root, dir_name)
                shutil.rmtree(dir_path)
                print(f"Deleted directory: {dir_path}")


def list_data_files(path):
    """Lists all data files paths for given library path."""
    files = listdir(path)
    data_files = [os.path.join(path, file) for file in files if not file.endswith(['.py', 'pyc', 'pyd'])]
    return data_files


def list_python_files(path):
    """List all Python files in the given directory."""
    files = os.listdir(path)
    python_files = [file for file in files if file.endswith('.py')]
    return python_files


# Define directories
os_platform = platform.system().lower().replace('darwin', 'macos')

if os_platform == 'windows':
    npal_directory = Path(
        f"C:\\Users\\{os.environ.get('USER', os.environ.get('USERNAME'))}\\Documents\\GitHub\\NeuroPAL_ID")
else:
    npal_directory = Path(f"/Users/{os.environ.get('USER', os.environ.get('USERNAME'))}/Documents/GitHub/NeuroPAL_ID")

script_directory = npal_directory / '+Wrapper'
distribution_directory = Path('.') / 'dist'
compile_directory = npal_directory / f"{os_platform[:3]}_visualize" / 'for_redistribution_files_only' / 'lib' / 'bin' / os_platform

# List of known hidden imports
hidden_imports = ['xml.etree', 'xml.etree.ElementTree', 'scikit-image', 'mx.DateTime', 'h5py.defs', 'h5py.utils',
                  'h5py.h5ac', 'h5py._proxy']
hidden_paths = [script_directory]
data_files = []

# List Python files in the directory
python_files = list_python_files(script_directory)

# Populate contingency lists
schema_libraries = [pynwb, h5py, hdmf]

for eachLib in schema_libraries:
    lib_path = Path(eachLib.__file__).parent
    hidden_paths.extend([str(lib_path)])
    data_files.extend(list_data_files(lib_path))

# Formulate arguments
hidden_imports_string = ' '.join(f"--hidden-import={import_name}" for import_name in hidden_imports)
paths_string = ' '.join(f"--paths={script_directory / local_file}" for local_file in python_files)
data_string = ' '.join(f"--add-data={data_file}" for data_file in data_files)

# Clear pyinstaller cache
for thisDir in [os. getcwd(), script_directory]:
    clear_cache(thisDir)

# Process each Python file
for file in python_files:
    file_path = script_directory / file

    cmd = f"pyinstaller {paths_string} {data_string} {file_path} {hidden_imports_string} --onefile"

    if os_platform == 'macos':
        subprocess.call('alias pip=pip3', shell=True)

    # Execute the command
    subprocess.call(cmd, shell=True)

    # Define source and destination paths for moving files
    source_file = distribution_directory / file.replace('py', 'exe')
    destination_file = compile_directory / file.replace('py', 'exe')

    # Move files from source to destination
    try:
        shutil.move(str(source_file), str(destination_file))
        print(f"Successfully compiled {destination_file}.\n")
    except FileNotFoundError:
        print(f"ERROR: Compilation failed for {source_file}...\n")
