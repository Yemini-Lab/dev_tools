import os
import h5py
import hdmf
import pynwb
import shutil
import platform
import subprocess
from pathlib import Path
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
        destination_file = paths["compilation"] / file.replace("py", "exe")
        shutil.move(str(executable_file), str(destination_file))
        print(f"Successfully compiled {destination_file}.\n")
    elif (state != 1) and ("--onefile" in cmd):
        print(
            f"Failed to compile {file}. Attempting to salvage with expanded packaging...\n"
        )
        cmd = cmd.replace("--onefile", "--onedir --noconfirm")
        subprocess.call(cmd, shell=True)
        validate_file(paths, file, cmd)
    else:
        raise ValueError("ERROR: COULD NOT SALVAGE FILE.")


def clear_cache(path):
    """Deletes all pyinstaller-related cache files."""
    print(f"\nClearing {path} cache...")
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
                    if platform.system().lower() == "darwin":
                        os.chmod(dir_path, 0o777)

                    shutil.rmtree(dir_path)
                    print(f"Deleted cache directory: {dir_path}")
                except:
                    print(f"Failed to delete cache directory: {dir_path}")


def get_os():
    """Retrieve operating system."""
    return platform.system().lower().replace("darwin", "macos")


def formulate_cmd(file_path):
    """Compose pyinstaller command."""
    os_platform = get_os()

    schema_libraries = [pynwb, h5py, hdmf]

    for eachLib in schema_libraries:
        lib_path = Path(eachLib.__file__).parent
        hidden_paths.extend([str(lib_path)])
        sub_directories = [p[0] for p in os.walk(lib_path)]
        for sub_dir in sub_directories:
            data_files.extend(list_files(sub_dir, (".yaml", ".dll")))

    hidden_imports_string = " ".join(
        f"--hidden-import={import_name}" for import_name in hidden_imports
    )
    paths_string = " ".join(
        f"--paths={dirs['script'] / local_file}" for local_file in python_files
    )
    data_string = " ".join(f"--add-data={data_file}:." for data_file in data_files)

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

    cmd = f'codesign --deep --force --verbove=4 --options=runtime -s {dev_id} --entitlements {plist} {file_path.replace(".py", "")}'
    subprocess.call(cd_cmd, shell=True)


if __name__ == "__main__":
    # Get operating system.
    os_platform = get_os()

    # Find user directory.
    if os_platform == "windows":
        user = Path(f"C:\\Users\\{os.environ.get('USER', os.environ.get('USERNAME'))}")
    else:
        user = Path(f"/Users/{os.environ.get('USER', os.environ.get('USERNAME'))}")

    # Find rest of the paths we'll be using.
    dirs = {"npal": Path(os.path.join(user, "Documents", "GitHub", "NeuroPAL_ID"))}
    dirs["script"] = dirs["npal"] / "+Wrapper"
    dirs["distribution"] = Path(".") / "dist"
    dirs["compilation"] = (
        dirs["npal"]
        / f"{os_platform[:3]}_visualize"
        / "for_redistribution_files_only"
        / "lib"
        / "bin"
        / os_platform
    )

    # Initialize list of known hidden imports
    hidden_imports = [
        "xml.etree",
        "xml.etree.ElementTree",
        "scikit-image",
        "mx.DateTime",
        "h5py.defs",
        "h5py.utils",
        "h5py.h5ac",
        "h5py._proxy",
    ]
    hidden_paths = [dirs["script"]]
    data_files = []

    # List Python files in the script directory
    python_files = list_files(dirs["script"], ".py")

    # Clear pyinstaller cache
    for thisDir in dirs.values():
        clear_cache(thisDir)

    # Process each Python file
    for file in python_files:
        file_path = dirs["script"] / file

        print(f"\nCompiling {file}...")
        cmd = formulate_cmd(file_path)
        subprocess.call(cmd, shell=True)

        if os_platform == 'macos':
            cd_cmd = codesign(file_path)

        validate_file(dirs, os.path.basename(file), cmd)
