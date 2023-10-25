import logging
import os
import argparse
import shutil
import subprocess
import sys
import time
import math
import json
import xml.etree.ElementTree as ElemTree

LOG_FILE = "./corex-cpu.log"
ENC_INPUT_FILE = "./input.enc"
INPUT_TAR_FILE = "./input.tar.gz"
OUTPUT_TAR_FILE = "./output.tar.gz"
ENC_OUTPUT_FILE = "./output.enc"
RESULTS_FILE = "./results.json"
SIM_FILE = "./input/simulation.xml"
CORE_CALC_COUNT = 163 * 83


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

def set_sim_count(sim_count: int) -> None:
    input_xml = ElemTree.parse(SIM_FILE)
    input_root = input_xml.getroot()
    output_path_xml_element = input_root.find('./Parameters/Samples')
    output_path_xml_element.text = str(sim_count)
    
    with open(SIM_FILE, 'wb') as out_file:
        input_xml.write(out_file)
        out_file.flush()


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

def create_results(sim_count: int, start_time: float, end_time: float, ore_time: float, output_dir: str) -> None:
    wall_time = end_time - start_time
    prep_time = wall_time - ore_time
    corex_score = (CORE_CALC_COUNT * sim_count) / wall_time / 100  # The 100 factor is just to get nicer numbers
    results = { 
                "score": corex_score,
                "sim_count": sim_count,
                "start_time": start_time,
                "end_time": end_time,
                "calc_time": ore_time,
                "feed_time": prep_time,
                "elapsed_time": wall_time
              }
    results_filename = os.path.join(output_dir, RESULTS_FILE)
    with open(results_filename, 'w', encoding="utf-8") as results_file:
        json.dump(results, results_file, ensure_ascii=True, indent=4)
        results_file.flush()


def main() -> None:
    parser = argparse.ArgumentParser(description= "This script should be run once per physical core on the machine under test", 
                                     epilog="(C) HMx Labs Limited 2023. All Rights Reserved")
    parser.add_argument('--input', dest="input", type=str, required=True, help='Filename of the inputs to use for ORE')
    parser.add_argument('--ore-dir', dest="ore_dir", type=str, required=True, help="Location of the ORE binary and libraries")
    parser.add_argument('--sim-count', dest="sim_count", type=int, required=False, default=500, help="The number of simulations to run")
    parser.add_argument('--output-dir', dest="output_dir", type=str, required=False, default="./", help="The directory to write the results to. Defaults to the current directory")


    try:
        args = parser.parse_args()
    except Exception:
        parser.print_help()
        sys.exit(-1)

    try:
        output_dir = args.output_dir
        if not os.path.exists(output_dir):
            print(f"Output directory {output_dir} does not exist")
            sys.exit(1)

        logfile = os.path.join(output_dir, LOG_FILE)
        logging.basicConfig(filename=logfile, filemode='a', level=logging.DEBUG,
                        format="%(asctime)s-%(levelname)-s-%(name)s::%(message)s")
        logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))
        logging.info("STARTING COREX-CPU")
        input_file = args.input
        ore_dir = args.ore_dir
        sim_count = args.sim_count
        set_env(ore_dir)
        start_time = time.perf_counter()
        copy_input(input_file)
        decrypt_input()
        unzip_input()
        set_sim_count(sim_count)
        ore_time = run_ore()
        process_output()
        end_time = time.perf_counter()
        create_results(sim_count, start_time, end_time, ore_time, output_dir)
        logging.info("ENDED COREX-CPU")
    except Exception:
        logging.exception("Failed executing corex-cpu")
        sys.exit(-1)

if __name__ == "__main__":
    main()
