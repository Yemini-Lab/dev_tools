"""
script_compiler.py: Runs pyinstaller compilation & codesigning routines on NeuroPAL_ID/+Wrapper scripts.

Usage:
    script_compiler.py -h | --help
    script_compiler.py [options]

Options:
    -h --help                           	show this message and exit.
    --input_path=<input_path>  			    path containing the scripts to be compiled.
    --output_path=<output_path>  			path to which compiled applications should be moved.
    --validate_files=<validate_files>  	    run validation routine after compilation. [default: False]
    --on_fail=<on_fail>                     what to do if validation fails. options include skipmove, deletefile, raiseerror.
    --select_scripts=<select_scripts>       comma-separated list of specific scripts to compiler.
"""

import os
import h5py
import hdmf
import pynwb
import shutil
import platform
import subprocess
from pathlib import Path
from docopt import docopt
from dotenv import load_dotenv

def list_files(path, fmts):
    """List all files of the given format(s) within the giving directory."""
    files = os.listdir(path)
    files = [os.path.join(path, file) for file in files if file.endswith(fmts)]
    return files


def compare_output(cmd_1, cmd_2):
    """Compare the output of two different system calls."""

    try:
        output_1 = subprocess.run(cmd_1, check=True, capture_output=True)
        output_1 = output_1.stdout
    except subprocess.CalledProcessError as e:
        output_1 = e.output.decode()

    try:
        output_2 = subprocess.run(cmd_2, check=True, capture_output=True)
        output_2 = output_2.stdout
    except subprocess.CalledProcessError as e:
        output_2 = e.output.decode()

    is_within = output_1 in output_2

    if not is_within:
        print(f"{cmd_1}:\n{output_1}")
        print(f"{cmd_2}:\n{output_2}")

    return is_within


def validate_file(paths, file, cmd):
    """Check whether the compiled file executes the same as the python original."""

    print(f"\nValidating {file}...")
    script_file = paths["script"] / file
    executable_file = paths["distribution"] / file.replace("py", "exe")

    state = compare_output(f"python {str(script_file)}", executable_file)

    if state:
        print(f"Successfully compiled {destination_file}.\n")
        return state
    elif (state != 1) and ("--onefile" in cmd):
        print(f"Failed to compile {file}. Attempting to salvage with expanded packaging...\n")
        cmd = cmd.replace("--onefile", "--onedir --noconfirm")
        subprocess.call(cmd, shell=True)
        validate_file(paths, file, cmd)
    else:
        print(f"FAILED VALIDATION: {file}.\n")
        return state


def clear_cache(path):
    """Deletes all pyinstaller-related cache files."""
    print(f"Clearing {path} cache...")
    for root, dirs, files in os.walk(path, topdown=False):
        for file in files:
            if file.endswith(".spec") or file.endswith(".exe"):
                file_path = os.path.join(root, file)

                try:
                    if platform.system().lower() == "darwin":
                        os.chmod(file_path, 0o777)

                    os.remove(file_path)
                    print(f"Deleted cache file: {file_path}")
                except:
                    print(f"Failed to delete cache file: {file_path}")

        for dir_name in dirs:
            if dir_name in ("build", "dist", "__pycache__"):
                dir_path = os.path.join(root, dir_name)

                try:
                    if platform.os_platform().lower() == "darwin":
                        os.chmod(dir_path, 0o777)

                    shutil.rmtree(dir_path)
                    print(f"Deleted cache directory: {dir_path}")
                except:
                    print(f"Failed to delete cache directory: {dir_path}")


def get_os():
    """Retrieve operating system."""
    return platform.system().lower().replace("darwin", "macos")


def formulate_cmd(dirs, blindspots, file_path):
    """Compose pyinstaller command."""
    os_platform = get_os()

    hidden_imports_string = " ".join(
        f"--hidden-import={import_name}" for import_name in blindspots["hidden_imports"]
    )
    paths_string = " ".join(
        f"--paths={dirs['script'] / local_file}" for local_file in blindspots["hidden_paths"]
    )
    data_string = " ".join(f"--add-data={data_file}:." for data_file in blindspots["data_files"])

    if os_platform == "windows":
        cmd = f"pyinstaller {paths_string} {data_string} {file_path} {hidden_imports_string} --onefile"
    elif os_platform == "macos":
        cmd = f"alias pip=pip3;pyinstaller {paths_string} {data_string} {file_path} {hidden_imports_string} --onefile"

    return cmd


def codesign(file):
    secret = Path(os.getcwd()) / ".env"

    if not os.path.isfile(secret):
        raise FileNotFoundError(
            "Could not find codesign secret. Instantiate repo secrets in local directory."
        )

    load_dotenv(dotenv_path=secret)
    dev_id = os.getenv("DEVELOPER_IDENTITY")
    plist = os.getenv("ENTITLEMENTS")

    cmd = f'codesign --deep --force --verbose=4 --options=runtime -s {dev_id} --entitlements {plist} {file_path.replace(".py", "")}'
    subprocess.call(cd_cmd, shell=True)


def compilation_routine(os_platform, user, args):
    blindspots = {
        "schema_libraries": [hdmf, h5py, pynwb],
        "hidden_paths": [],
        "data_files": [],
        "hidden_imports": [
            "xml.etree",
            "xml.etree.ElementTree",
            "scikit-image",
            "mx.DateTime",
            "h5py.defs",
            "h5py.utils",
            "h5py.h5ac",
            "h5py._proxy",
        ]
    }
    
    # Find rest of the paths we'll be using.
    dirs = {"npal": Path(os.path.join(user, "Documents", "GitHub", "NeuroPAL_ID"))}
    dirs["distribution"] = Path(".") / "dist"

    if args["--input_path"] is not None:
        dirs["script"] = Path(args["--input_path"])
    else:
        dirs["script"] = dirs["npal"] / "+Wrapper"

    if args["--output_path"] is not None:
        dirs["compilation"] = Path(args["--output_path"])
    else:
        dirs["compilation"] = (
            dirs["npal"]
            / f"{os_platform[:3]}_visualize"
            / "for_redistribution_files_only"
            / "lib"
            / "bin"
            / os_platform
        )

    # List Python files in the script directory
    python_files = list_files(dirs["script"], ".py")
    blindspots["hidden_imports"].extend([os.path.basename(script) for script in python_files])
    blindspots["hidden_paths"] += [dirs["script"]]

    for eachLib in blindspots["schema_libraries"]:
        lib_path = Path(eachLib.__file__).parent
        sub_directories = [p[0] for p in os.walk(lib_path)]
        for sub_dir in sub_directories:
            blindspots["data_files"].extend(list_files(sub_dir, (".yaml", ".dll")))

    # Clear pyinstaller cache
    for thisDir in dirs.values():
        clear_cache(thisDir)
        
    # Process each Python file
    for file in python_files:
        file = os.path.basename(file)

        if args["--select_scripts"] is not None and file not in args["--select_scripts"]:
            continue

        file_path = dirs["script"] / file

        print(f"\nCompiling {file}...")
        cmd = formulate_cmd(dirs, blindspots, file_path)
        code = subprocess.call(cmd, shell=True)

        if code != 0:
            return

        if os_platform == 'macos':
            cd_cmd = codesign(file_path)

        if args["--validate_files"] is True:
            state = validate_file(dirs, file, cmd)
        else:
            state = 1

        if state or args["--on_fail"] is None:
            executable_file = dirs["distribution"] / file.replace("py", "exe")
            destination_file = dirs["compilation"] / file.replace("py", "exe")
            shutil.move(str(executable_file), str(destination_file))
        else:
            if args["--on_fail"] == "deletefile":
                os.remove(file_path.replace('py', 'exe'))
            elif args["--on_fail"] == "raiseerror":
                raise RuntimeError(f"Failed to validate {file.replace('py', 'exe')}!")

if __name__ == "__main__":
    args = docopt(__doc__, version=f'NeuroPAL_ID Script Compiler')

    os_platform = get_os()
    if os_platform == "windows":
        user = Path(f"C:\\Users\\{os.environ.get('USER', os.environ.get('USERNAME'))}")
    else:
        user = Path(f"/Users/{os.environ.get('USER', os.environ.get('USERNAME'))}")

    compilation_routine(os_platform, user, args)


