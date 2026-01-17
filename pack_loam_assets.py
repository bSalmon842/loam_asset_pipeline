
# Project: Loam Asset Pipeline
# File: pack_loam_assets.py
# Author: Brock Salmon
# Created: 09JAN2025

import sys, os
from termcolor import colored
import json

import convert_to_intermediate as inter

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

    check_for_valid_base_json_field('is_mod',    bool, dictKeys, jsonDict)
    check_for_valid_base_json_field('game_code', str,  dictKeys, jsonDict)
    check_for_valid_base_json_field('assets',    dict, dictKeys, jsonDict)
    
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

    imageFolderPath = "image"
    audioFolderPath = "audio"
    videoFolderPath = "video"
    jsonFolderPath = "json"
    fontFolderPath = "font"
    typeFolderPaths = [ imageFolderPath, audioFolderPath, videoFolderPath, jsonFolderPath, fontFolderPath ]
    
    rawFolderPath = "raw"
    intermediateFolderPath = "inter"
    packagedFolderPath = "packaged"
    
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
        print("> " + colored("is_mod: ", 'white') + "A true/false value denoting if this input file is being used to modify an existing Loam game")
        print("> " + colored("assets: ", 'white') + "The JSON object holding info for each asset to be packaged\n")

        print(colored("Required Fields (Assets)", 'white'))
        print(colored("NOTE:", 'light_yellow') + "The name of each asset info object is packaged and used by the engine as an identifier for the asset")
        print("> " + colored("type: ", 'white') + "Denotes which raw/ (generated with --setup-file-dir) folder contains the asset")
        print("> " + colored("filename: ", 'white') + "The actual filename and extension of the asset\n")
        
        with open('example.json', 'w') as file:
            file.write(
"""
{
\t"is_mod": false,
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
\t\t}
\t}
}
""")
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
    for asset in jsonDict['assets'].items():
        assetName = asset[0]
        assetInfo = asset[1]
        
        assetType = assetInfo['type']
        assetFilename = assetInfo['filename']
        assetTags = assetInfo['tags']
        
        if   assetType == imageFolderPath:
            inter.convert_image(assetName, assetFilename, assetTags, rawFolderPath + '\\' + imageFolderPath + "\\", intermediateFolderPath + '\\' + imageFolderPath + '\\')
        elif assetType == audioFolderPath:
            print(colored("AUDIO NOT IMPLEMENTED", 'light_red'))
        elif assetType == videoFolderPath:
            print(colored("VIDEO NOT IMPLEMENTED", 'light_red'))
        elif assetType == jsonFolderPath:
            print(colored("JSON NOT IMPLEMENTED", 'light_red'))
        elif assetType == fontFolderPath:
            print(colored("FONT NOT IMPLEMENTED", 'light_red'))
    
    # Package assets


        
if __name__ == '__main__':
    main()

