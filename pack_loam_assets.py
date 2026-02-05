
# Project: Loam Asset Pipeline
# File: pack_loam_assets.py
# Author: Brock Salmon
# Created: 09JAN2025

import sys, os
from termcolor import colored
import json
import subprocess
import ast

import convert_to_intermediate as inter

imageFolderPath = "image"
audioFolderPath = "audio"
videoFolderPath = "video"
jsonFolderPath = "json"
fontFolderPath = "font"
typeFolderPaths = [ imageFolderPath, audioFolderPath, videoFolderPath, jsonFolderPath, fontFolderPath ]

validPackTypes = [ "engine", "game", "mod", "expac" ]
    
rawFolderPath = "raw"
intermediateFolderPath = "inter"
packagedFolderPath = "packaged"

EXAMPLE_JSON_FILE_CONTENTS = """
{
\t"pack_type": "game",
\t"game_code": "TEST",
\t"assets": {
\t\t"my_asset_engine_name1": {
\t\t\t"type": "image",
\t\t\t"filename": "test.png",
\t\t\t"tags": [ "test", "tagged" ]
\t\t},
\t\t
\t\t"my_asset_engine_name2": {
\t\t\t"type": "image",
\t\t\t"filename": "test2.ktx2",
\t\t\t"tags": []
\t\t},
\t\t
\t\t"my_asset_engine_name3": {
\t\t\t"type": "audio",
\t\t\t"filename": "test_audio.wav",
\t\t\t"tags": [ "background" ]
\t\t},
\t\t
\t\t"my_asset_engine_name4": {
\t\t\t"type": "image",
\t\t\t"filename": "test3.ktx",
\t\t\t"tags": [ "upgraded" ]
\t\t},
\t\t
\t\t"my_asset_test_name5": {
\t\t\t"type": "font",
\t\t\t"filename": "test_font.ttf",
\t\t\t"tags": [ "mono", "internal" ]
\t\t},
\t\t
\t\t"my_asset_test_name6": {
\t\t\t"type": "json",
\t\t\t"filename": "test_json.json",
\t\t\t"tags": [ "sprite_data" ]
\t\t}
\t}
}
"""

binPath = os.path.dirname(os.path.abspath(__file__)) + '\\exe_bin\\'

def error(errorMsg):
    print(colored(errorMsg, 'light_red'))
    raise SystemExit

def make_folder_if_does_not_exist(basePath, stagePath, typePath):
    folderPath = basePath + stagePath
    if typePath != None:
         folderPath += '\\' + typePath
    if not os.path.isdir(folderPath):
        os.makedirs(folderPath)
        print(colored("Created path: " + folderPath, "light_green"))
    else:
        print(colored(folderPath + " already exists, skipping", "light_yellow"))

def make_folder_paths_for_type(typePath):
    return rawFolderPath + '\\' + typePath + '\\', intermediateFolderPath + '\\' + typePath + '\\'

def check_for_valid_base_json_field(expectedName, expectedType, keys, dictionary):
    if expectedName not in keys:
        error("Could not find base value '" + expectedName + "'")

    foundType = type(dictionary[expectedName])
    if foundType is not expectedType:
        error("'" + expectedName + "' value is not expected type '" + expectedType + "', instead found '" + foundType + "'")

def check_for_valid_asset_json_field(expectedName, expectedType, keys, assetDictionary, assetName):
    if expectedName not in keys:
        error("Could not find asset value '" + expectedName + "' for asset '" + assetName + "'")

    foundType = type(assetDictionary[expectedName])
    if foundType is not expectedType:
        error("'" + expectedName + "' value in asset '" + assetName + "' is not expected type '" + expectedType + "', instead found '" + foundType + "'")

def verify_json_contents(jsonDict, validTypes):
    dictKeys = jsonDict.keys()

    check_for_valid_base_json_field('pack_type', str,  dictKeys, jsonDict)
    check_for_valid_base_json_field('game_code', str,  dictKeys, jsonDict)
    check_for_valid_base_json_field('assets',    dict, dictKeys, jsonDict)

    if any(not c.isalnum() for c in jsonDict['game_code']):
        error("game_code cannot contain special characters, must be alphanumeric")

    if len(jsonDict['game_code']) > 4:
        error("game_code must be at most 4 characters long")

    if jsonDict['pack_type'] not in validPackTypes:
        error("pack_type must be one of: " + str(validPackTypes))

    if jsonDict['pack_type'] == "engine" and jsonDict['game_code'] != "LOAM":
        error("pack_type of 'engine' can only be used with the Loam engine's code")
    
    assetsDict = jsonDict["assets"]
    if len(assetsDict) == 0:
        error("No assets were found in 'assets' object, exiting")

    for asset in assetsDict.items():
        assetName = asset[0]
        if len(assetName) > 32:
            error("Asset name '" + assetName + "' is too long, asset names must be a maximum of 32 characters")
        
        assetInfo = asset[1]
        if type(assetInfo) is not dict:
            error(assetName + " is not an expected asset object value in ")

        check_for_valid_asset_json_field('type',     str, assetInfo.keys(), assetInfo, assetName)
        if assetInfo['type'] not in validTypes:
            error(assetName + " type is invalid: '" + assetInfo['type'] + "'")
        check_for_valid_asset_json_field('filename', str, assetInfo.keys(), assetInfo, assetName)
        check_for_valid_asset_json_field('tags',     list, assetInfo.keys(), assetInfo, assetName)

def check_for_assets(jsonDict):
    assetsDict = jsonDict['assets']
    allAssetsFound = True
    for asset in assetsDict.values():
        filepath = "raw\\" + asset["type"] + "\\" + asset["filename"]
        print("\t Checking for '" + filepath + "'... ", end="")
        if os.path.isfile(filepath):
            print(colored("Found", "light_green"))
        else:
            print(colored("Missing", "light_red"))
            allAssetsFound = False
        
    if not allAssetsFound:
        error("Could not find all assets, exiting...")
        
def main():
    # Read command arguments
    if len(sys.argv) < 2:
        error("Too few arguments")
        
    workingDirectory = os.getcwd() + "\\"
    if sys.argv[1] != '--help':
        print(colored('Working Directory: "' + workingDirectory + '"\n', 'light_cyan'))
    
    if sys.argv[1] == '--help':
        print(colored("Valid Arguments:", 'white'))
        print("> " + colored("*.json:", 'white') + " Defines an input json file, this is required to create an asset pack")
        print("> " + colored("--setup-file-dir:", 'white') + " Creates a file structure that the asset packer pipeline understands")
        print("> " + colored("--create-json-example:", 'white') + " Creates a short example input JSON file. Note this will not work if run on its own as it does not also generate mentioned assets")
        raise SystemExit
    elif sys.argv[1] == '--setup-file-dir':
        print(colored("Setting up folder structure at working directory...", 'white'))
        
        for typeFolder in typeFolderPaths:
            make_folder_if_does_not_exist(workingDirectory, rawFolderPath, typeFolder)
        
        for typeFolder in typeFolderPaths:
            make_folder_if_does_not_exist(workingDirectory, intermediateFolderPath, typeFolder)
        
        make_folder_if_does_not_exist(workingDirectory, packagedFolderPath, None)
        raise SystemExit
    elif sys.argv[1] == '--create-json-example':
        print(colored("\nRequired Fields (Base)", 'white'))
        print("> " + colored("game_code: ", 'white') + "An identifier for the game this pack is to be used with, e.g. Loam's built in asset packs use LOAM")
        print("> " + colored("pack_type: ", 'white') + "A string value denoting if this input file is being used to modify an existing Loam game, is a base game file, an expansion file, or an internal engine asset package")
        print("> " + colored("assets: ", 'white') + "The JSON object holding info for each asset to be packaged\n")

        print(colored("Required Fields (Assets)", 'white'))
        print(colored("NOTE:", 'light_yellow') + "The name of each asset info object is packaged and used by the engine as an identifier for the asset")
        print("> " + colored("type: ", 'white') + "Denotes which raw/ (generated with --setup-file-dir) folder contains the asset")
        print("> " + colored("filename: ", 'white') + "The actual filename and extension of the asset\n")
        
        with open('example.json', 'w') as file:
            file.write(EXAMPLE_JSON_FILE_CONTENTS)
        print(colored("Wrote example.json", 'light_green'))
        raise SystemExit

    inputFilepath = sys.argv[1]
    inputExt = os.path.splitext(inputFilepath)[-1].lower()
    if inputExt != ".json":
        error("Input file is expected to be a JSON file, see --create-json-example")
    
    # Read JSON input file
    jsonDict = dict()
    with open(inputFilepath, 'r') as file:
        jsonContents = file.read()
        jsonDict = json.loads(jsonContents)

    # Verify contents as valid
    print(colored("Verifying input file is valid...", 'white'))
    verify_json_contents(jsonDict, typeFolderPaths)    
    print(colored("Input JSON fields valid\n", 'light_green'))

    # Fields valid, now check that each raw asset actually exists
    print(colored("Verifying defined assets are present...", 'white'))
    check_for_assets(jsonDict)
    print(colored("All expected assets found\n", 'light_green'))
    
    # Write each file into an engine friendly intermediate file, store in intermediate directory
    print("Processing asset files to intermediate files...")
    intersToPackage = []
    interAssetNames = []
    for asset in jsonDict['assets'].items():
        assetName = asset[0]
        assetInfo = asset[1]
        
        assetType = assetInfo['type']
        assetFilename = assetInfo['filename']
        assetTags = assetInfo['tags']
        packedInterPath = None
        
        if   assetType == imageFolderPath:
            packedInterPath = inter.convert_image(assetName, assetFilename, assetTags, *make_folder_paths_for_type(imageFolderPath))
        elif assetType == audioFolderPath:
            packedInterPath = inter.convert_audio(assetName, assetFilename, assetTags, *make_folder_paths_for_type(audioFolderPath))
        elif assetType == videoFolderPath:
            print(colored("VIDEO NOT IMPLEMENTED", 'light_red'))
        elif assetType == jsonFolderPath:
            packedInterPath = inter.convert_json(assetName, assetFilename, assetTags, *make_folder_paths_for_type(jsonFolderPath))
        elif assetType == fontFolderPath:
            packedInterPath = inter.convert_font(assetName, assetFilename, assetTags, *make_folder_paths_for_type(fontFolderPath))

        if packedInterPath != None:
            intersToPackage.append(packedInterPath)
            interAssetNames.append(assetName)

    if len(jsonDict['assets'].items()) != len(intersToPackage):
        error("Number of Intermediate files does not match the count of requested assets, this is mostly likely a bug in the pipeline rather than an issue with the input JSON")
        
    packageName = packagedFolderPath + '\\a_' + jsonDict['game_code'] + '_' + jsonDict['pack_type'] + '_@.lp'
    mapName = packagedFolderPath + '\\a_' + jsonDict['game_code'] + '_' + jsonDict['pack_type'] + '_@.lm'
    
    # Package assets & Map Offsets
    result = subprocess.run([binPath + 'package.exe', packageName, mapName, str(intersToPackage), str(interAssetNames)], capture_output=True, text=True)
    outputFiles = None
    if result.returncode != 0:
        print("\t" + colored("Failed to package assets with error " + str(result.returncode) + ":", 'light_red'))
        print("\t\t" + colored(result.stderr, 'light_red'))
        raise SystemExit
    if result.stdout is not None and len(result.stdout) > 0:
        outputs = result.stdout.split('\n')
        for output in outputs:
            if output != outputs[-1]:
                print(output)
        
        outputFiles = ast.literal_eval(outputs[-1])
    
    print("\t" + colored("Successfully processed assets into package(s): ", 'light_green'))
    index = 0
    for file in outputFiles:
        if index % 2 == 0:
            print(colored('\t\t' + file, 'light_cyan'), end="")
        else:
            print(" (" + colored("Map", 'light_magenta') + ': ' + colored(file, 'white') + ")")
                  
        index += 1
        
if __name__ == '__main__':
    main()

