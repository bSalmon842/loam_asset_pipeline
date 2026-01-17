/*
Project: Loam Asset Pipeline
File: build.jai
Author: Brock Salmon
Created: 16JAN2026
*/


#import "Basic";
#import "Compiler";
#import "File";
#import "File_Utilities";
#import "Math";
#import "Metaprogram_Plugins";
#import "Process";
#import "String";

INTER_PROCESS_FILE :: "inter_process.jai";
INTER_PROCESS_NAME :: "inter_process";

#run build_main();

build_main :: () {    
    buildFolderPath := "../exe_bin/";
    make_directory_if_it_does_not_exist(buildFolderPath);

    build_program(buildFolderPath, INTER_PROCESS_FILE, INTER_PROCESS_NAME);
}

build_program :: (buildFolder : string, mainFile : string, appName : string) {
    workspaceName := appName;
    workspace := compiler_create_workspace(workspaceName);
    if !workspace {
        compiler_report(tprint("Failed to create workspace: %", workspaceName));
        return;
    }
    
    dt := to_calendar(current_time_consensus(), .LOCAL);
    dtString := tprint("(%/%/% %:%:%)", dt.year, formatInt(dt.month_starting_at_0 + 1, minimum_digits=2), formatInt(dt.day_of_month_starting_at_0 + 1, minimum_digits=2), formatInt(dt.hour, minimum_digits=2), formatInt(dt.minute, minimum_digits=2), formatInt(dt.second, minimum_digits=2));
    print("Compiling % @ %\n", workspaceName, dtString);
    
    targetOptions := get_build_options(workspace);
    targetOptions.output_executable_name = appName;
    targetOptions.output_path = buildFolder;
    targetOptions.os_target = OS;
    
    add_generic_build_options(*targetOptions, false);
    set_optimization(*targetOptions, .VERY_OPTIMIZED);
    set_build_options(targetOptions, workspace);
    
    if OS == .WINDOWS {
        set_build_options_dc(.{do_output=false, append_linker_arguments=.["/SUBSYSTEM:windows", "/ENTRY:mainCRTStartup"]});
    }
    
    compiler_begin_intercept(workspace);
    add_build_file(tprint("%/%", #filepath, mainFile), workspace);
    compiler_end_intercept(workspace);
}

add_generic_build_options :: (options : *Build_Options, timing : bool) {
    options.text_output_flags = 2;
    options.dead_code_elimination = .ALL;
    options.use_visual_studio_message_format = false;
    options.additional_linker_arguments = .[ "/NOIMPLIB", "/NOEXP" ];
    options.text_output_flags = ifx timing then .OUTPUT_TIMING_INFO else cast(type_of(Build_Options.text_output_flags)) 0;
    
    modulesPaths : [..] string;
    array_add(*modulesPaths, ..options.import_path);
    #if OS == .WINDOWS {
	array_add(*modulesPaths, "C:/work/bs_modules");
    } else {
	array_add(*modulesPaths, "~/work/bs_modules");
    }
    options.import_path = modulesPaths;
}

