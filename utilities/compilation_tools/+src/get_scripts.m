function get_scripts(path)
    py_files = dir(path);
    src.log.write("Scanning script path...");

    for script=1:length(py_files)
        py_file = fullfile(py_files(script).folder, py_files(script).name);
        if isfile(py_file) && endsWith(py_file, '.py')
            src.log.write(sprintf("Found %s", py_file));
            src.gui.components.add_script(py_files(script).name);
        end
    end
end

