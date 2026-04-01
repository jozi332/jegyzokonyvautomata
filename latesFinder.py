import os
import re
import runpy
import sys

# The directory where your scripts are located
SCRIPT_DIR = "/home/wj/Documents/JegyzokonyvAutomata"

# Regex pattern to match "vX.Y.py" and extract X and Y
PATTERN = re.compile(r"^v(\d+)\.(\d+)\.py$")


def get_latest_script(directory):
    valid_scripts = []

    # Scan the directory
    for filename in os.listdir(directory):
        match = PATTERN.match(filename)
        if match:
            main_version = int(match.group(1))  # The 'X'
            sub_version = int(match.group(2))  # The 'Y'
            valid_scripts.append(((main_version, sub_version), filename))

    if not valid_scripts:
        return None

    # Sort the list based on the version tuple (X, Y) in descending order
    # This ensures v7.1 > v6.6 > v6.5 > v5.4
    valid_scripts.sort(key=lambda item: item[0], reverse=True)

    # Return the filename of the first item (the highest version)
    return valid_scripts[0][1]


if __name__ == "__main__":
    latest_file = get_latest_script(SCRIPT_DIR)

    if latest_file:
        full_path = os.path.join(SCRIPT_DIR, latest_file)
        print(f"=== Automata Runner: Executing {latest_file} ===")

        # Adjust sys.argv so the target script receives any command line arguments
        sys.argv = [full_path] + sys.argv[1:]

        # Execute the latest script as if it were the main program
        runpy.run_path(full_path, run_name="__main__")
    else:
        print(f"Error: No scripts matching 'vX.Y.py' found in {SCRIPT_DIR}")