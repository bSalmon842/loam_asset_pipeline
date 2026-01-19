/*
Project: Loam Asset Pipeline
File: inter_process.jai
Author: Brock Salmon
Created: 16JAN2026
*/

Errors :: enum s32 {
    Success;
    Invalid_Arguments;
    Invalid_Input_Type;
    File_Does_Not_Exist;
    Write_Failure;
}

error_with_code :: (errString : string, errCode : Errors) {
    print(errString, to_standard_error=true);
    exit(cast(s32) errCode);
}

main :: () {
    argv := get_command_line_arguments();
    if argv.count != 5 {
	error_with_code(tprint("Expected 5 arguments, got %", argv.count), .Invalid_Arguments);
    }

    inputType := argv[1];
    inputFile := argv[2];
    inputName := argv[3];
    inputTags := argv[4];
    
    inputTags.data += 1;
    inputTags.count -= 2;
    tagArray := split(inputTags, ",");
    if tagArray.count == 1 && trim(tagArray[0]).count == 0 then tagArray = .[];
    charCount : u16 = 0;
    for tagArray {
	tag := trim(it);
	advance(*tag);
	tag.data[tag.count-1] = #char "\0";
	charCount += xx tag.count;
    }
    
    fileContents, readSuccess := read_entire_file(inputFile);
    if !readSuccess {
	error_with_code(tprint("Failed to read \"%\"", inputFile), .File_Does_Not_Exist);
    }
    
    dataSize : s64;
    data := null;
    outputFilename : string;
    
    if inputType == {
	case "i"; {
	    // NOTE: We don't do any extra processing for ktx files
	    dataSize = fileContents.count;
	    data = fileContents.data;
	    outputFilename = tprint("inter\\image\\%.ii", path_strip_extension(path_filename(inputFile)));
	}

	case "a"; {
	    audioData := load_audio_data(inputName, fileContents);
	    processedData := pack_sound_data(*audioData);
	    
	    dataSize = processedData.count;
	    data = processedData.data;
	    outputFilename = tprint("inter\\audio\\%.ia", path_strip_extension(path_filename(inputFile)));
	}
	
	case; error_with_code(tprint("Invalid input type: %", inputType), .Invalid_Input_Type);
    }

    header : PackagedAssetHeader;
    memcpy(header.name.data, inputName.data, inputName.count);
    header.size = xx dataSize;
    header.tagCount = cast(u16) tagArray.count;
    header.tagCharCount = charCount;
    
    intermediateContents := alloc(size_of(PackagedAssetHeader) + header.tagCharCount + xx header.size);
    memcpy(intermediateContents, *header, size_of(PackagedAssetHeader));
    contentsIndex := size_of(PackagedAssetHeader);
    for tagArray {
	memcpy(intermediateContents + contentsIndex, it.data, it.count);
	contentsIndex += it.count;
    }
    memcpy(intermediateContents + contentsIndex, data, dataSize);
    contentsIndex += dataSize;

    writeSuccess := write_entire_file(outputFilename, intermediateContents, contentsIndex);
    if !writeSuccess {
	error_with_code(tprint("Failed to write \"%\"", outputFilename), .Write_Failure);
    }
}

#import "Basic";
#import "String";
#import "File";

#import "ktx";
#import "Sound_Player_bs842";

#import,file "../../bs_modules/loam/code/shared_asset_info.jai";

