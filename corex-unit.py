import logging
import os
import argparse
import shutil
import subprocess
import sys
import time
import math
import json

LOG_FILE = "./corex-unit.log"
ENC_INPUT_FILE = "./input.enc"
INPUT_TAR_FILE = "./input.tar.gz"
OUTPUT_TAR_FILE = "./output.tar.gz"
ENC_OUTPUT_FILE = "./output.enc"
RESULTS_FILE = "./results.json"


def set_env(ore_dir: str) -> None:
    os.environ["LD_LIBRARY_PATH"] = ore_dir
    curr_path = os.environ["PATH"]
    new_path = f"{curr_path}:{ore_dir}"
    os.environ["PATH"] = new_path


def extract_runtime(output) -> float:
        try:
            return float((str(output).replace("'","").split("\\n")[-3]).split(" ")[2])
        except Exception:
            logging.warning("Unable to determine a runtime from the output")
            return math.nan


def run_shell_command(command: str) -> str:
    logging.info(f"Running command: {command}")
    proc = subprocess.Popen([command], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd="./")
    output = proc.communicate()[0]
    logging.info(f"Command {command} generated output: {output}")
    if 0 != proc.returncode:
        logging.error(f"Failure when running command {command}. Exiting")
        sys.exit(-1)

    return output


def copy_input(input_filename: str) -> None:
    logging.info("Copying input file to working directory")
    shutil.copyfile(input_filename, ENC_INPUT_FILE)
    logging.info("Input file copied")


def decrypt_input() -> None:
    # The key should be in the parent directory
    logging.info("Decrypting input file")
    decrypt_commmand = f"openssl enc -d -aes-256-cbc -in {ENC_INPUT_FILE} -out {INPUT_TAR_FILE} -pass pass:123"
    run_shell_command(decrypt_commmand)
    logging.info("Input file decrypted")


def unzip_input() -> None:
    logging.info("Expanding input file archive")
    untar_command = f"tar -xf {INPUT_TAR_FILE}"
    run_shell_command(untar_command)
    logging.info("Input file archive expanded")


def run_ore() -> float:
    # At this point we should have ore.xml and input directory in the current working directory
    # The ORE executable should be on the path and its dependencies in LD_LIBRARY_PATH
    ore_command = f"ore ./ore.xml"
    results = run_shell_command(ore_command)
    return extract_runtime(results)


def process_output() -> None:
    logging.info("Creating output archive file")
    tar_command = f"tar -czf {OUTPUT_TAR_FILE} ./output"
    run_shell_command(tar_command)
    logging.info("Output archive created")
    logging.info("Creating encrypted output")
    encrypt_command = f"openssl enc -aes-256-cbc -in {OUTPUT_TAR_FILE} -out {ENC_OUTPUT_FILE} -pass pass:123"
    run_shell_command(encrypt_command)
    logging.info("Created encrypted output")


def main() -> None:
    parser = argparse.ArgumentParser(description= "This script should be run once per physical core on the machine under test", 
                                 epilog="(C) HMx Labs Limited 2023. All Rights Reserved")
    parser.add_argument('--input', dest="input", type=str, required=True, help='Filename of the inputs to use for ORE')
    parser.add_argument('--ore-dir', dest="ore_dir", type=str, required=True, help="Location of the ORE binary and libraries")


    try:
        args = parser.parse_args()
    except Exception:
        parser.print_help()
        sys.exit(-1)

    try:
        input_file = args.input
        ore_dir = args.ore_dir
        set_env(ore_dir)
        start_time = time.perf_counter()
        copy_input(input_file)
        decrypt_input()
        unzip_input()
        ore_time = run_ore()
        process_output()
        end_time = time.perf_counter()
        wall_time = end_time - start_time

        results = { 
                    "start_time": start_time,
                    "end_time": end_time,
                    "ore_time": ore_time,
                    "wall_time": wall_time
                  }
        
        with open(RESULTS_FILE, 'w', encoding="utf-8") as results_file:
            json.dump(results, results_file, ensure_ascii=True, indent=4)
            results_file.flush()

    except Exception:
        logging.exception("Failed executing corex-unit")
        sys.exit(-1)

if __name__ == "__main__":
    logging.basicConfig(filename=LOG_FILE, filemode='a', level=logging.DEBUG,
                        format="%(asctime)s-%(levelname)-s-%(name)s::%(message)s")
    logging.info("STARTING COREX-UNIT")
    main()
    logging.info("ENDED COREX-UNIT")
