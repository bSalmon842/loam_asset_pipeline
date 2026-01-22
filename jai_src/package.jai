/*
Project: Loam Asset Pipeline
File: package.jai
Author: Brock Salmon
Created: 21JAN2026
*/

KB :: (value : u64) -> u64 {
    return value * 1024;
}

MB :: (value : u64) -> u64 {
    return KB(value * 1024);
}

GB :: (value : u64) -> u64 {
    return MB(value * 1024);
}

to_size_string :: (value : u64) -> string {
    if value > GB(1) {
	floatValue := cast(float) value / cast(float) GB(1);
	return tprint("% GB", formatFloat(floatValue, 1, 2));
    } else if value > MB(1) {
	floatValue := cast(float) value / cast(float) MB(1);
	return tprint("% MB", formatFloat(floatValue, 1, 2));
    } else if value > KB(1) {
	floatValue := cast(float) value / cast(float) KB(1);
	return tprint("% KB", formatFloat(floatValue, 1, 2));
    } else {
	return tprint("% bytes", value);
    }
}


compress_data :: (data : string) -> bool, string {
    maxCompressedSize := LZ4_compressBound(cast(s32) data.count);
    compressedRawData := alloc(maxCompressedSize);
    bytesWritten := LZ4_compress_default(data.data, compressedRawData, cast(s32) data.count, maxCompressedSize);
    if bytesWritten == 0 {
	return false, .{};
    }
        
    compData := alloc_string(bytesWritten);
    memcpy(compData.data, compressedRawData, bytesWritten);
    free(compressedRawData);
    
    return true, compData;
}


// The maximum size a package can be before we move to a new package
MAX_PACKAGE_SIZE :: cast(s64) #run MB(512);

Errors :: enum s32 {
    Success;
    Invalid_Arguments;
    Package_Mapping_Mismatch;
    File_Does_Not_Exist;
    Write_Failure;
}

error_with_code :: (errString : string, errCode : Errors) {
    print(errString, to_standard_error=true);
    exit(cast(s32) errCode);
}

write_package_and_map :: (packStructure : string, mapStructure : string, fileIndex : *s64,
			  packBuilder : *String_Builder, mapBuilder : *String_Builder, packageFiles : *[..] string, mappingFiles : *[..] string) {
    packageFilepath := replace(packStructure, "@", tprint("%", fileIndex.*));
    mappingFilepath := replace(mapStructure, "@", tprint("%", fileIndex.*));
    
    append(mapBuilder, "}");
    
    startPackSize := builder_string_length(packBuilder);
    startMapSize := builder_string_length(mapBuilder);
    
    array_add(packageFiles, path_filename(packageFilepath));
    array_add(mappingFiles, path_filename(mappingFilepath));
    
    print("\tCompressing...\n");

    packCompSuccess, packCompContents := compress_data(builder_to_string(packBuilder));
    if !packCompSuccess then error_with_code(tprint("Failed to compress \"%\"", packageFilepath), .Write_Failure);
    endPackSize := packCompContents.count;
    print("\tCompressed Pack % from % to %\n", packageFiles.*[packageFiles.count-1], to_size_string(cast(u64) startPackSize), to_size_string(cast(u64) endPackSize));

    mapCompSuccess, mapCompContents := compress_data(builder_to_string(mapBuilder));
    if !mapCompSuccess then error_with_code(tprint("Failed to compress \"%\"", mappingFilepath), .Write_Failure);
    endMapSize := mapCompContents.count;
    print("\tCompressed Map % from % to %\n", mappingFiles.*[mappingFiles.count-1], to_size_string(cast(u64) startMapSize), to_size_string(cast(u64) endMapSize));
    
    packageWriteSuccess := write_entire_file(packageFilepath, packCompContents);
    if !packageWriteSuccess then error_with_code(tprint("Failed to write \"%\"", packageFilepath), .Write_Failure);
    mappingWriteSuccess := write_entire_file(mappingFilepath, mapCompContents);
    if !mappingWriteSuccess then error_with_code(tprint("Failed to write \"%\"", mappingFilepath), .Write_Failure);
    
    print("\tWritten package and mapping files for index %\n", fileIndex.*);

    reset(packBuilder);
    reset(mapBuilder);
    
    append(mapBuilder, "{");
    fileIndex.* += 1;
}

main :: () {
    argv := get_command_line_arguments();
    if argv.count != 5 {
	error_with_code(tprint("Expected 5 arguments, got %", argv.count), .Invalid_Arguments);
    }

    packageFilenameStructure := argv[1];
    mappingFilenameStructure := argv[2];
    filesToBePackaged        := argv[3];
    interFileAssetNames      := argv[4];

    filesToBePackaged.data += 1;
    filesToBePackaged.count -= 2;
    interArray := split(filesToBePackaged, ",");
    if interArray.count == 1 && trim(interArray[0]).count == 0 then interArray = .[];

    interFileAssetNames.data += 1;
    interFileAssetNames.count -= 2;
    assetNameArray := split(interFileAssetNames, ",");
    if assetNameArray.count == 1 && trim(assetNameArray[0]).count == 0 then assetNameArray = .[];

    if interArray.count != assetNameArray.count {
	error_with_code("Did not get the same number of asset names as intermediate files, this is likely a bug with package.exe", .Invalid_Arguments);
    }

    packageFiles : [..] string;
    mappingFiles : [..] string;

    currentFileIndex := 0;
    currentPackageFileContents : String_Builder;
    currentMappingFileContents : String_Builder;
    init_string_builder(*currentPackageFileContents, MAX_PACKAGE_SIZE);
    init_string_builder(*currentMappingFileContents);
    append(*currentMappingFileContents, "{");
    for interArray {
	fileContents, readSuccess := read_entire_file(trim(it, "' "));
	if !readSuccess {
	    error_with_code(tprint("Failed to read \"%\"", it), .File_Does_Not_Exist);
	}

	currentOffset := builder_string_length(*currentPackageFileContents);
	if currentOffset + fileContents.count > MAX_PACKAGE_SIZE {
	    write_package_and_map(packageFilenameStructure, mappingFilenameStructure, *currentFileIndex,
				  *currentPackageFileContents, *currentMappingFileContents, *packageFiles, *mappingFiles);
	}

	currentOffset = builder_string_length(*currentPackageFileContents);
	append(*currentPackageFileContents, fileContents);
	append(*currentMappingFileContents, tprint("\"%\" : %", trim(assetNameArray[it_index], "' "), currentOffset));
	if it_index != interArray.count-1 {
	    append(*currentMappingFileContents, ",");
	}
    }

    if builder_string_length(*currentPackageFileContents) > 0 {
	write_package_and_map(packageFilenameStructure, mappingFilenameStructure, *currentFileIndex,
			      *currentPackageFileContents, *currentMappingFileContents, *packageFiles, *mappingFiles);
    }
    
    if packageFiles.count != mappingFiles.count {
	error_with_code("Did not make the same number of package files as mapping files, this is likely a bug with package.exe", .Package_Mapping_Mismatch);
    }
    
    // NOTE: This program's stdout is piped back to the main pipeline, and the structure of the printed string is important to be preserved
    builder : String_Builder;
    init_string_builder(*builder);
    append(*builder, "[");
    for packageFiles {
	append(*builder, "\"");
	append(*builder, it);
	append(*builder, "\"");
	append(*builder, ",");
    }
    for mappingFiles {
	append(*builder, "\"");
	append(*builder, it);
	append(*builder, "\"");
	if it_index != mappingFiles.count-1 {
	    append(*builder, ",");
	}
    }
    append(*builder, "]");
    print(builder_to_string(*builder));
}

#import "Basic";
#import "String";
#import "File";

#import "lz4_bs842";

