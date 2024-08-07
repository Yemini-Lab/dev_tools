import os
import h5py
import hdmf
import pynwb
import shutil
import platform
import subprocess
from subprocess import check_output
from pathlib import Path

def list_data_files(path):
    """Lists all data files paths for given library path."""
    files = os.listdir(path)
    data_files = [os.path.join(path, file) for file in files if not file.endswith(('.py', '.pyc', '.pyd'))]
    return data_files


def list_python_files(path):
    """List all Python files in the given directory."""
    files = os.listdir(path)
    python_files = [file for file in files if file.endswith('.py')]
    return python_files


def validate_file(paths, file, cmd):
    """Check whether the compiled file executes the same as the python original."""

    script_file = paths['compilation'] / file
    executable_file = script_file.replace('py', 'exe')

    state = check_output(f"python {script_file}", stderr=subprocess.STDOUT) in check_output(executable_file, stderr=subprocess.STDOUT)

    if state:
        destination_file = paths['compilation'] / file.replace('py', 'exe')
        shutil.move(str(executable_file), str(destination_file))
        print(f"Successfully compiled {destination_file}.\n\n")
    elif state != 1 and '--onefile' in cmd:
        print(f"Failed to compile {file}. Attempting to salvage with expanded packaging...\n\n")
        cmd = cmd.replace(' --onefile', '')
        subprocess.call(cmd, shell=True)
        validate_file(paths, file, cmd)
    else:
        raise ValueError('ERROR: COULD NOT SALVAGE FILE.')

def clear_cache(path):
    """Deletes all pyinstaller-related cache files."""
    for root, dirs, files in os.walk(path, topdown=False):
        for file in files:
            if file.endswith('.spec') or file.endswith('.exe'):
                file_path = os.path.join(root, file)

                try:
                    if platform.system().lower() == 'darwin':
                        os.chmod(file_path, 0o777)

                    os.remove(file_path)
                    print(f"Deleted cache file: {file_path}")
                except:
                    print(f"Failed to delete cache file: {file_path}")

        for dir_name in dirs:
            if dir_name in ('build', 'dist', '__pycache__'):
                dir_path = os.path.join(root, dir_name)

                try:
                    if platform.system().lower() == 'darwin':
                        os.chmod(dir_path, 0o777)

                    shutil.rmtree(dir_path)
                    print(f"Deleted cache directory: {dir_path}")
                except:
                    print(f"Failed to delete cache directory: {dir_path}")


# Define directories
os_platform = platform.system().lower().replace('darwin', 'macos')

if os_platform == 'windows':
    npal_directory = Path(
        f"C:\\Users\\{os.environ.get('USER', os.environ.get('USERNAME'))}\\Documents\\GitHub\\NeuroPAL_ID")
else:
    npal_directory = Path(f"/Users/{os.environ.get('USER', os.environ.get('USERNAME'))}/Documents/GitHub/NeuroPAL_ID")

dirs = {
    'npal': npal_directory,
    'script': npal_directory / '+Wrapper',
    'distribution': Path('.') / 'dist',
    'compilation': npal_directory / f"{os_platform[:3]}_visualize" / 'for_redistribution_files_only' / 'lib' / 'bin' / os_platform
}

# List of known hidden imports
hidden_imports = ['xml.etree', 'xml.etree.ElementTree', 'scikit-image', 'mx.DateTime', 'h5py.defs', 'h5py.utils',
                  'h5py.h5ac', 'h5py._proxy']
hidden_paths = [dirs['script']]
data_files = []

# List Python files in the directory
python_files = list_python_files(dirs['script'])

# Populate contingency lists
schema_libraries = [pynwb, h5py, hdmf]

for eachLib in schema_libraries:
    lib_path = Path(eachLib.__file__).parent
    hidden_paths.extend([str(lib_path)])
    data_files.extend(list_data_files(lib_path))

# Formulate arguments
hidden_imports_string = ' '.join(f"--hidden-import={import_name}" for import_name in hidden_imports)
paths_string = ' '.join(f"--paths={dirs['script'] / local_file}" for local_file in python_files)
data_string = ' '.join(f"--add-data={data_file}:." for data_file in data_files)

# Clear pyinstaller cache
for thisDir in dirs.values():
    clear_cache(thisDir)

# Process each Python file
for file in python_files:
    file_path = dirs['script'] / file

    cmd = f"pyinstaller {paths_string} {data_string} {file_path} {hidden_imports_string} --onefile"

    if os_platform == 'macos':
        subprocess.call('alias pip=pip3', shell=True)

    # Execute the command
    subprocess.call(cmd, shell=True)

    # Define source and destination paths for moving files
    validate_file(dirs, file, cmd)
