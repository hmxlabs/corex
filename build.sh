#!/bin/bash

# This script will create the input file that corex-unit will expect to find
# and then create an archive including the python scripts and the input file

tar -czf input.tar.gz ore.xml input/
openssl enc -aes-256-cbc -in input.tar.gz -out input.enc -pass pass:123
tar -czf corex.tar.gz input.enc corex-cpu.py corex.py
