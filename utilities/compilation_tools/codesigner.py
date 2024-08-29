"""
codesigner.py: Handles codesigning routine.

Usage:
    codesigner.py -h | --help
    codesigner.py [options]

Options:
    -h --help                           	show this message and exit.
    --file=<file>  			                path containing the file to be codesigned.
    --files=<files>                         path to a textfile containing the paths of all files to be codesigned.
    --env                                   flags presence of local env file for developer identity details [default: False]
    --dev-id=<dev-id>                       developer identity
    --apple-id=<apple-id>                    lab apple id
    --password=<password>                   app password
    --team-id=<team-id>                     team id
    --entitlements=<entitlements>           path to plist file
"""

import os
import time
import easygui
import datetime
import subprocess
from pathlib import Path
from docopt import docopt
from dotenv import load_dotenv
from tqdm import tqdm


def grab_env():
    secret = Path(os.getcwd()) / ".env"

    if not os.path.isfile(secret):
        raise FileNotFoundError(
            "Could not find codesign secret. Instantiate repo secrets in local directory."
        )

    load_dotenv(dotenv_path=secret)
    dev_id = os.getenv("DEVELOPER_IDENTITY")
    apple_id = os.getenv("APPLE_ID")
    password = os.getenv("PASSWORD")
    team_id = os.getenv("TEAM_ID")
    plist = os.getenv("ENTITLEMENTS")

    return dev_id, plist, apple_id, password, team_id


def codesign_batch(files, args):
    files = [file.strip() for file in files]
    with tqdm(total=len(files), desc="Processing files", unit="file") as pbar:
        for file in files:
            file_path = Path(file)
            codesign_routine(file_path, args, pbar)
            pbar.update(1)


def codesign_routine(file, args, pbar):
    pbar.set_description(f"Codesigning {file.name}")
    cmd = "codesign --verbose=4 "

    if args['--env']:
        dev_id, plist, _, _, _ = grab_env()
    else:
        dev_id = args['--dev-id']
        plist = args['--entitlements']

    if file.suffix == '.py':
        cmd += "--force --deep "

    cmd += f"--options=runtime -s {dev_id} --entitlements={plist} {str(file)}"
    subprocess.call(cmd, shell=True)

    code = notarization_routine(file, args, pbar)


def notarization_routine(file, args, pbar):
    pbar.set_description(f"Notarizing {file.name}")
    cmd = "xcrun notarytool submit "

    if args['--env']:
        _, _, apple_id, password, team_id = grab_env()
    else:
        apple_id = args['--apple-id']
        password = args['--password']
        team_id = args['--team-id']

    cmd += f"--apple-id {apple_id} --password {password} --team-id {team_id} {str(file)}"
    process = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    sub_time = datetime.datetime.now()
    sub_output = process.stdout.split("\n")

    sub_id = None
    for line in sub_output:
        if "id:" in line:
            sub_id = line[5:]

    if sub_id is None:
        pbar.set_description(f"Failed notarizing {file.name}")
        return 0

    cmd = cmd.replace("submit", "log").replace(f" {str(file)}", "") + f" {sub_id}"

    log_ready = 0
    while log_ready == 0:
        log_output = subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout
        if "logFormatVersion" in log_output:
            log_ready = 1

            if "error" in log_output:
                pbar.set_description(f"Failed to notarize {file.name}")
                return 0
            else:
                pbar.set_description(f"Succesfully notarized {file.name}")
                return 1

        else:
            current_time = datetime.datetime.now()
            time_diff = (current_time - sub_time).total_seconds() / 60.0

            if time_diff > 30:
                easygui.msgbox(f"Notarization for {str(file)} has been taking more than 30 minutes. This is unusual, and you may want to cancel the process and check for issues.", title="Warning!")
                time.sleep(60)
            else:
                time.sleep(60)


if __name__ == "__main__":
    args = docopt(__doc__, version=f'Codesigning Utility')
    
    if args['--file'] is not None:
        codesign_routine(Path(args['--file']), args, tqdm(total=1))

    elif args['--files'] is not None:
        files = open(args['--files'], 'r').readlines()
        codesign_batch(files, args)


