#!/bin/bash

# Will take a new machine and install the necessary tools to build and package ORE

sudo apt update
sudo apt upgrade -y
sudo apt install build-essential g++ python3-dev autotools-dev libicu-dev libbz2-dev cmake git -y

