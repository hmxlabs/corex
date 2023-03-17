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

def get_cpu_count() -> int:
    logging.info("Determining how many CPUs are on this machine")
    cpu_count=os.cpu_count()
    if cpu_count > 256 or cpu_count < 1 :
        logging.exception(f"Number of reported cpus on machine seems invalid: {cpu_count}")
        raise Exception("Unable to determine the number of cores on this machine")

    logging.info(f"Detected {cpu_count} CPUs on machine")
    return cpu_count


def create_corex_unit_dirs(cpu_count: int) -> None:
    logging.info("Creating working directories for corex cpu  processes")
    for index in range(0,cpu_count):
        dir = os.path.join(".", str(index))
        Path(dir).mkdir(parents=False, exist_ok=True)
    logging.info("Completed creating working directories")


def start_corex_unit(cpu_count: int, ore_dir: str, sim_count: int) -> list[subprocess.Popen]:
    logging.info("Starting corex-cpu")
    procs=[]
    for index in range(0,cpu_count):
        logging.info(f"Starting process: {index}")
        cwd = os.path.join(".", str(index))
        corex_unit_command = f"python3 ../corex-cpu.py --input ../input.enc --ore-dir {ore_dir} --sim-count {sim_count}"
        procs.append(subprocess.Popen([corex_unit_command], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=cwd))

    logging.info("All corex-cpu processes launched")
    return procs


def wait_for_corex(procs: list[subprocess.Popen]) -> bool:
    logging.info("Waiting for corex-cpu processes")
    success = True
    for proc in procs:
        output = proc.communicate()[0]
        logging.info(f"Corex-unit completed with exit code: {proc.returncode}")
        if 0 != proc.returncode:
            success = False

    logging.info("All corex-cpu processes complete")
    return success

def create_results(cpu_count: int, sim_count: int, wall_time: float) -> None:
    logging.info("Creating results")
    cpu_results: list[dict[str,str]] = []
    cpu_scores: list[float] = []
    cpu_wall_times: list[float] = []
    cpu_calc_times: list[float] = []
    cpu_feed_times: list[float] = [] 

    for index in range(0,cpu_count):
        result_filename = os.path.join(".", str(index), RESULTS_FILE)
        with open(result_filename) as results_file:
            results = json.load(results_file)
            cpu_scores.append(results["score"])
            cpu_wall_times.append(results["elapsed_time"])
            cpu_calc_times.append(results["calc_time"])
            cpu_feed_times.append(results["feed_time"])
            cpu_results.append(results)
    
    corex_score = sum(cpu_scores)
    mean_score = corex_score / cpu_count
    var_score = max(cpu_scores) - min(cpu_scores)

    mean_wall_time = sum(cpu_wall_times) / cpu_count
    mean_calc_time = sum(cpu_calc_times) / cpu_count
    mean_feed_time = sum(cpu_feed_times) / cpu_count

    var_wall_time = max(cpu_wall_times) - min(cpu_wall_times)
    var_calc_time = max(cpu_calc_times) - min(cpu_calc_times)
    var_feed_time = max(cpu_feed_times) - min(cpu_feed_times)

    stdev_calc_time = 0
    stdev_wall_time = 0
    stdev_feed_time = 0
    stdev_score = 0
    if cpu_count > 1:
        stdev_calc_time = statistics.stdev(cpu_calc_times)
        stdev_score = statistics.stdev(cpu_scores)
        stdev_feed_time = statistics.stdev(cpu_feed_times)
        stdev_wall_time = statistics.stdev(cpu_wall_times)

    results = {"cpu_count": cpu_count,
               "sim_count": sim_count,
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
               "cpu_times": cpu_results
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
    parser.add_argument('--force-cpu', dest="cpu_count", type=int, required=False, default=0, help="Set this if you wish to override the detected number of CPUs")

    try:
        args = parser.parse_args()
    except Exception:
        parser.print_help()
        sys.exit(-1)

    
    try:
        ore_dir = args.ore_dir
        sim_count = args.sim_count
        cpu_count = args.cpu_count
        if 0 == cpu_count:
            cpu_count = get_cpu_count()
        else:
            logging.info(f"Overriding CPU count to: {cpu_count}")

        create_corex_unit_dirs(cpu_count)
        start_time = time.perf_counter()
        procs = start_corex_unit(cpu_count, ore_dir, sim_count)
        success = wait_for_corex(procs)
        if not success:
            logging.error("Some corex-unit processes failed. Exiting")
            sys.exit(-1)

        end_time = time.perf_counter()
        wall_time = end_time - start_time
        create_results(cpu_count, sim_count, wall_time)
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