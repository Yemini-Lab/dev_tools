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
    --apple-id<apple-id>                    lab apple id
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


def grab_env()
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
    for file in files:
        if file.endswith('\n'):
            file = Path(file[:-1])
        else:
            file = Path(file)

        codesign_routine(file, args)


def codesign_routine(file, args):
    cmd = "codesign --verbose=4 "

    if args['--env']:
        dev_id, plist, _, _, _ = grab_env()
    else:
        dev_id = args['--dev-id']
        plist = args['--entitlements']

    if file.suffix == '.py':
        cmd = "--force --deep "

    cmd += f"--options=runtime -s {dev_id} --entitlements={plist} {str(file)}"
    subprocess.call(cmd, shell=True)

    code = notarization_routine(file, args)


def notarization_routine(file, args):
    cmd = "xcrun notarytool submit "

    if args['--env']:
        _, _, apple_id, password, team_id = grab_env()
    else:
        apple_id = args['--apple-id']
        password = args['--password']
        team_id = args['--team-id']

    cmd += f"--apple-id {apple_id} --password {password} --team-id {team_id} {str(file)}"
    process = subprocess.call(cmd, shell=True, capture_output=True)

    sub_time = datetime.datetime.now()
    sub_output = process.stdout.split("\n")

    for line in sub_output:
        if "id:" in line:
            sub_id = line[5:]

    cmd = cmd.replace("submit", "log") + f" {sub_id}"

    log_ready = 0
    while log_ready == 0:
        log_output = subprocess.call(cmd, shell=True, capture_output=True)
        if "logFormatVersion" in log_output:
            log_ready = 1

            if "error" in log_output:
                return 0
            else:
                return 1

        else:
            current_time = datetime.datetime.now()
            time_diff = (current_time - sub_time).total_seconds() / 60.0

            if time_diff > 20:
                easygui.msgbox(f"Notarization for {str(file)} has been taking more than 20 minutes. This is unusual, and you may want to cancel the process and check for issues.", title="Warning!")
                time.sleep(60)
            else:
                time.sleep(60)


if __name__ == "__main__":
    args = docopt(__doc__, version=f'NeuroPAL_ID Codesigning Utility')
    print(args)
    if args['--file'] is not None:
        codesign_routine(Path(args['--file']), args)

    elif args['--files'] is not None:
        files = open(args['--files'], 'r').readlines()
        codesign_batch(files, args)


