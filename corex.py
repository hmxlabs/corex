import logging
import json
import time
import subprocess
import os
import math
import xml.etree.ElementTree as ElemTree
from typing import List

class CorexRunner:

    TEMPLATE_INPUT_FILE = "./ore.xml"
    TEMPLATE_INPUT_DIR = "./input/"
    ORE_BINARY = "./ore"
    RESULTS_FILE = "./corex.out.json"

    def __init__(self) -> None:
        pass

    def create_orexml(self, index: int ) -> str:
        input_xml = ElemTree.parse(CorexRunner.TEMPLATE_INPUT_FILE)
        input_root = input_xml.getroot()
        output_path_xml_element = input_root.find('./Setup/Parameter[@name="outputPath"]')
        output_path_xml_element.text = f"{output_path_xml_element.text}-{index}"
        
        orexml_filename = f"ore-{index}.xml"
        with open(orexml_filename, 'wb') as out_file:
            input_xml.write(out_file)
            out_file.flush()

        return orexml_filename

    def extract_runtime(self, output) -> float:
        try:
            return float((str(output).replace("'","").split("\\n")[-3]).split(" ")[2])
        except Exception:
            logging.warning("Unable to determine a runtime from the output")
            return math.nan

    def create_result(self, runtime, output, returncode) -> dict:
        return   {
                    "run_time": runtime,
                    "stdout": str(output),
                    "retcode": returncode
                }

    def run(self) -> None:
        logging.info("Starting CoreX Benchmark run")
        num_cores=os.cpu_count()
        # Sets the num processors to an arbitrary figure based on the content of zip file
        if num_cores > 256 or num_cores < 1 :
            logging.exception(f"Number of reported cores on machine seems invalid: {num_cores}")
            raise Exception("Unable to determine the number of cores on this machine")

        logging.info(f"Detected {num_cores} cores on machine")
        # The input ORE XML contains the output path. This script will start one instance of ORE per core
        # on the machine, as such we need one input file with a unique output location for each instance
        # of ORE that will be run
        logging.info("Creating ORE input files and directories for each core")
        orexml_files: List[str] = []
        for index in range(num_cores):
            orexml_files.append(self.create_orexml(index))
            
        logging.info("Starting ORE binaries")
        procs=[]
        start_time = time.perf_counter()
        for orexml in orexml_files:
            logging.info(f"Starting processs: {orexml}")
            procs.append(subprocess.Popen([CorexRunner.ORE_BINARY, orexml], stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd="./"))

        logging.info("Waiting for ORE binaries to complete")
        runtimes=[]
        core_results=[]
        success = True
        for orexml, proc in zip(orexml_files, procs):
            logging.info(f"Waiting on {orexml}")
            output = proc.communicate()[0]
            logging.debug(f"{orexml} output: {output}")
            logging.info(f"The {orexml} completed with exit code: {proc.returncode}")
            runtime = self.extract_runtime(output)
            runtimes.append(runtime)
            logging.info("The runtime in seconds was: {runtime}")
            core_results.append(self.create_result(runtime, output, proc.returncode))
            if 0 != proc.returncode:
                success = False

        end_time = time.perf_counter()
        wall_time = end_time - start_time

        results =   {
                        "success": success, 
                        "cores": num_cores,
                        "start_time": start_time,
                        "end_time": end_time,
                        "wall_time": wall_time,
                        "results": core_results
                    }

        with open(CorexRunner.RESULTS_FILE, 'w', encoding="utf-8") as results_file:
            json.dump(results, results_file, ensure_ascii=True, indent=4)
            results_file.flush()

        logging.info("Results written to disk. Complete")


if __name__ == "__main__":
    logging.basicConfig(filename="corex.runner.log", filemode='a', level=logging.DEBUG,format="%(asctime)s-%(levelname)-s-%(name)s::%(message)s")
    runner = CorexRunner()
    runner.run()