
# Project: Loam Asset Pipeline
# File: convert_to_intermediate.py
# Author: Brock Salmon
# Created: 14JAN2025

import os
from termcolor import colored
import subprocess

def convert_image(assetName, filename, tags, rawFolderPath, interFolderPath):
    print("\tProcessing " + colored(assetName, 'light_cyan') + " at " + colored(rawFolderPath + filename + "...", 'white'))

    
    tagOutput = "\t\t" + colored("Tags", 'light_magenta') + ": "
    for index, tag in enumerate(tags):
        tagOutput += '"' + tag + '"'
        if index != (len(tags) - 1):
            tagOutput += ', '
    print(tagOutput)
    
    root, ext = os.path.splitext(filename)
    inputExt = ext.lower()
    expectedKTXFilename = root
    if inputExt == ".ktx":
        print(colored("\t\tNeeds to be updated from ktx to ktx2 format. Updating...", "light_yellow"))
        result = subprocess.run(['ktx2ktx2', '-f', rawFolderPath + filename], capture_output=True, text=True)
        if result.returncode != 0:
            print(colored(result.stderr, 'light_red'))
            raise SystemExit
        print(colored("\t\tSuccessfully updated to ktx2 format", 'light_green'))
    elif inputExt != ".ktx2":
        outFilepath = rawFolderPath + expectedKTXFilename + '.ktx2'
        print(colored("\t\tNeeds to be converted to ktx2 format. Converting...", "light_yellow"))
        result = subprocess.run(['ktx', 'create', '--format', 'R8G8B8A8_SRGB', '--assign-tf', 'KHR_DF_TRANSFER_SRGB',
                                 '--generate-mipmap', '--encode', 'basis-lz', rawFolderPath + filename, outFilepath], capture_output=True, text=True)
        if result.returncode != 0:
            print(colored(result.stderr, 'light_red'))
            raise SystemExit
        print(colored("\t\tSuccessfully converted to " + outFilepath, 'light_green'))
    else:
        print(colored("\t\tAlready the correct format", 'light_green'))

    ktxFile = expectedKTXFilename + '.ktx2'
    print("\tPackaging " + colored(ktxFile, 'light_cyan') + " to intermediate image (.ii) file...")
    scriptPath = os.path.dirname(__file__) + '\\'
    binPath = scriptPath + 'exe_bin\\'
    result = subprocess.run([binPath + 'inter_process.exe', 'i', rawFolderPath + ktxFile, assetName, str(tags)], capture_output=True, text=True)
    if result.stdout is not None and len(result.stdout) > 0:
        print(result.stdout)
    if result.returncode != 0:
        print("\t" + colored("Failed to process file into intermediate file with error " + str(result.returncode) + ":", 'light_red'))
        print("\t\t" + colored(result.stderr, 'light_red'))
        raise SystemExit

    print(colored("\tSuccessfully packaged " + assetName + " to intermediate file '" + expectedKTXFilename + '.ii' + "'", 'light_green'))
        
    print();
