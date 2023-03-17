# COREx - A Financial Risk Based HPC Benchmark

## Introduction & Purpose
This is a benchmark with a very specific purpose, to allow the comparison of different (virtualised) hardware for the purposes of running financial risk calculations in High Performance Computing (HPC) grid clusters.

We understand that financial institutions guard their quantitative analytics libraries close to their chest and using their code for such a benchmark is improbably to say the least. Fortunately the existence of [QuantLib](https://www.quantlib.org) and [ORE](https://www.opensourcerisk.org) makes this possible.

The results of the benchmark are (approximately) a representation of the hardware's ability. That is to say hardware with a score of 100 should be able to process the same financial risk calculation on the same portfolio twice as fast as hardware with a score of 50.

## What Does COREx do?
This repository contains all the necessary inputs for ORE to operate (see [ore.xml](https://github.com/hmxlabs/corex/blob/main/ore.xml) and the contents of the [input](https://github.com/hmxlabs/corex/tree/main/input) directory). The inputs contain a portfolio composed of approximately 160 trades, the associated market data and configuration. ORE is configured to calculate the NPV of the portfolio and run simulations. The number of simulations is adjusted by COREx to vary the length of the benchmark run. The above inputs are assembled into a `tar.gz` archive with is then AES encrypted.

Upon being launched COREx will

1. Determine the number of cpus on the machine. This will be equal to `number of sockets x number of cores per socket x number of threads per core`
2. Launch a process for each cpu which will:
3. Copy the input data to the working directory of the process
4. Decrypt the AES encrypted archive of inputs using OpenSSL
5. Expand the archive
6. Update the ORE configuration with the requested number of simulations
7. Invoke ORE
8. Wait till ORE completes and read the execution time from its output
9. AES encrypt the output/results using OpenSSL
10. Record the all the timings and write these to an output file
11. Once all the processes have completed overall results are computed and written to disk

The AES decryption and encryption are to provide a more realistic benchmark. At the very least (under normal circumstances) the inputs will be transferred to the compute engine using TLS and more often than not if using public cloud in addition to this the inputs will also be encrypted.


## Dependencies
Clearly this repository does not contain nearly enough code to even value a simple government bond. As stated earlier it uses ORE. This scripts in the binary simply orchestrate ORE and as such the ORE binaries will also need to be installed to the system under test.

This benchmark uses [ORE Version 8](https://github.com/OpenSourceRisk/Engine/tree/v1.8.8.0). A fork of this repository used by HMx Labs can be found [here](https://github.com/hmxlabs/corex-bin).

Windows binaries are available directly from the [ORE Release](https://github.com/OpenSourceRisk/Engine/releases/tag/v1.8.8.0). Linux (compiled on Ubuntu 22.04 LTS) are available from the HMx Labs website.

ORE itself requires the [boost](https://www.boost.org) libraries which may be installed on an Ubuntu distribution as follows:

    sudo apt install libboost-all-dev

COREx is a python script (well two scripts) and you will require Python3 installed also. Again on an Ubuntu distribution this may be installed as follows:

    sudo apt install python3

## Running COREx
Once the boost libraries and ORE are installed, either clone the COREx repository run the build script to create the appropriate input archive or download the binaries from the [Release](https://github.com/hmxlabs/corex/releases/download/1.0/corex.tar.gz) and extract them.

COREx can take 3 command line inputs of which only one is mandatory

- The location of the ORE binaries (`--ore-dir`). This is required
- The number of simulations to run (`--sim-count`). Optional. Will default to 500
- The location of the ORE binaries (`--force-cpu`). Optional if you wish to override the number of detected CPUs

The number of simulations will determine the length of execution of the benchmark, however the score is adjusted accordingly and will be the same (ish). A longer benchmark duration will mean a lower IO/AES overhead and should result in a marginally higher score. Conversely, thermal throttling of your hardware may mean a longer run results in a lower score. A minimum value of 50 is recommended. A value of 500 will result in a run time of approximately 20 to 30 minutes.

COREx can be started as follows:

    python3 corex.py --ore-dir /path/to/ore/binaries/ --sim-count 100

The results will be output in a file named `results.json`

If you wish to be informed of changes or releases to COREx please subscribe to our [mailing list](http://hmxlabs.uk/contact/).