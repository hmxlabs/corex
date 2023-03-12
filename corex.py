import logging
import json
import time
import argparse
import subprocess
import os
import sys
import statistics
from pathlib import Path

LOG_FILE = "corex.log"
RESULTS_FILE = "results.json"

def get_core_count() -> int:
    logging.info("Determining how many cores are on this machine")
    num_cores=os.cpu_count()
    if num_cores > 256 or num_cores < 1 :
        logging.exception(f"Number of reported cores on machine seems invalid: {num_cores}")
        raise Exception("Unable to determine the number of cores on this machine")

    logging.info(f"Detected {num_cores} cores on machine")
    return num_cores


def create_corex_unit_dirs(count: int) -> None:
    logging.info("Creating working directories for corex-unit processes")
    for index in range(0,count):
        dir = os.path.join(".", str(index))
        Path(dir).mkdir(parents=False, exist_ok=True)
    logging.info("Completed creating working directories")


def start_corex_unit(count: int, ore_dir: str, sim_count: int) -> list[subprocess.Popen]:
    logging.info("Starting corex-unit")
    procs=[]
    for index in range(0,count):
        logging.info(f"Starting process: {index}")
        cwd = os.path.join(".", str(index))
        corex_unit_command = f"python3 ../corex-unit.py --input ../input.enc --ore-dir {ore_dir} --sim-count {sim_count}"
        procs.append(subprocess.Popen([corex_unit_command], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=cwd))

    logging.info("All corex-unit processes launched")
    return procs


def wait_for_corex(procs: list[subprocess.Popen]) -> bool:
    logging.info("Waiting for corex-unit processes")
    success = True
    for proc in procs:
        output = proc.communicate()[0]
        logging.info(f"Corex-unit completed with exit code: {proc.returncode}")
        if 0 != proc.returncode:
            success = False

    logging.info("All corex-unit processes complete")
    return success

def create_results(count: int, sim_count: int, start_time: float, end_time: float, wall_time: float) -> None:
    logging.info("Creating results")
    unit_results: list[dict[str,str]] = []
    unit_scores: list[float] = []
    unit_wall_times: list[float] = []
    unit_calc_times: list[float] = []
    unit_feed_times: list[float] = [] 

    for index in range(0,count):
        result_filename = os.path.join(".", str(index), RESULTS_FILE)
        with open(result_filename) as results_file:
            results = json.load(results_file)
            unit_scores.append(results["score"])
            unit_wall_times.append(results["elapsed_time"])
            unit_calc_times.append(results["calc_time"])
            unit_feed_times.append(results["feed_time"])
            unit_results.append(results)
    
    corex_score = sum(unit_scores)
    mean_score = corex_score / count
    var_score = max(unit_scores) - min(unit_scores)

    mean_wall_time = sum(unit_wall_times) / count
    mean_calc_time = sum(unit_calc_times) / count
    mean_feed_time = sum(unit_feed_times) / count

    var_wall_time = max(unit_wall_times) - min(unit_wall_times)
    var_calc_time = max(unit_calc_times) - min(unit_calc_times)
    var_feed_time = max(unit_feed_times) - min(unit_feed_times)

    stdev_calc_time = 0
    stdev_wall_time = 0
    stdev_feed_time = 0
    stdev_score = 0
    if count > 1:
        stdev_calc_time = statistics.stdev(unit_calc_times)
        stdev_score = statistics.stdev(unit_scores)
        stdev_feed_time = statistics.stdev(unit_feed_times)
        stdev_wall_time = statistics.stdev(unit_wall_times)

    results = {"sim_count": count,
               "score": corex_score,
               "elapsed_time": wall_time,
               "mean_score": mean_score,
               "var_score": var_score,
               "stdev_score": stdev_score,
               "mean_elapsed_time": mean_wall_time,
               "mean_calc_time": mean_calc_time,
               "mean_feed_time": mean_feed_time,
               "var_elapsed_time": var_wall_time,
               "var_calc_time": var_calc_time,
               "var_feed_time": var_feed_time,
               "stdev_elapsed_time": stdev_wall_time,
               "stdev_calc_time": stdev_calc_time,
               "stdev_feed_time": stdev_feed_time,
               "unit_times": unit_results
               }
    
    output_results_filename = os.path.join(".", RESULTS_FILE)
    with open(output_results_filename, 'w', encoding="utf-8") as output_results:
            json.dump(results, output_results, ensure_ascii=True, indent=4)
            output_results.flush()

    logging.info(f"COREX SCORE: {corex_score}")
    logging.info("Results output complete")

def main() -> None:
    parser = argparse.ArgumentParser(description= "This script should be run once per physical core on the machine under test", 
                                 epilog="(C) HMx Labs Limited 2023. All Rights Reserved")
    parser.add_argument('--ore-dir', dest="ore_dir", type=str, required=True, help="Location of the ORE binary and libraries")
    parser.add_argument('--sim-count', dest="sim_count", type=int, required=False, default=500, help="The number of simulations to run")

    try:
        args = parser.parse_args()
    except Exception:
        parser.print_help()
        sys.exit(-1)

    
    try:
        ore_dir = args.ore_dir
        sim_count = args.sim_count
        core_count = get_core_count()
        create_corex_unit_dirs(core_count)
        start_time = time.perf_counter()
        procs = start_corex_unit(core_count, ore_dir, sim_count)
        success = wait_for_corex(procs)
        if not success:
            logging.error("Some corex-unit processes failed. Exiting")
            sys.exit(-1)

        end_time = time.perf_counter()
        wall_time = end_time - start_time
        create_results(core_count, sim_count, start_time, end_time, wall_time)
    except Exception:
        logging.exception("Failed executing corex")
        sys.exit(-1)


if __name__ == "__main__":
    logging.basicConfig(filename=LOG_FILE, filemode='a', level=logging.DEBUG,
                        format="%(asctime)s-%(levelname)-s-%(name)s::%(message)s")
    logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))
    logging.info("STARTING COREX")
    main()
    logging.info("ENDED COREX")