function update_path(event, valid_formats, msg_string)
    component = event.Source;
    default_path = src.helper.sys.default_path();

    path = uigetdir(default_path, msg_string);

    app.npal_path = 
    if ~isempty(app.npal_path)
        app.SelectFolderButton_NPAL.Text = app.npal_path;
        
        if isfile(fullfile(app.npal_path, 'visualize_light.mlapp'))
            validation_color = [0.52, 1, 0.52];
            app.visualize_lightLamp.Color = [0, 1, 0];
        else
            validation_color = [1, 1, 0.52];
            app.write_log("WARNING: visualize_light.mlapp not found in selected NeuroPAL_ID path!");
        end

        app.SelectFolderButton_NPAL.BackgroundColor = validation_color;

        app.script_path = fullfile(app.npal_path, '+Wrapper');
        app.SelectFolderButton_Script.Text = app.script_path;

        if isfile(fullfile(app.script_path, 'recommend_frames.py'))
            validation_color = [0.52, 1, 0.52];
        else
            validation_color = [1, 1, 0.52];
            app.write_log("WARNING: recommend_frames.py not found in selected script path!");
        end
        app.SelectFolderButton_Script.BackgroundColor = validation_color;


        if ~isempty(app.script_path)
            py_files = dir(app.script_path);
            app.write_log("Scanning script path...");
            for script=1:length(py_files)
                py_file = fullfile(py_files(script).folder, py_files(script).name);
                if isfile(py_file) && endsWith(py_file, '.py')
                    app.write_log(sprintf("Found %s", py_file));
                    uitreenode("Text", py_files(script).name, "Parent", app.ScriptTree);
                end
            end

            app.ScriptTree.CheckedNodes = [];
        end

        app.dist_path = fullfile(app.npal_path, sprintf('%s_visualize', app.os.short), 'for_redistribution_files_only', 'lib', 'bin', app.os.long);
        app.SelectFolderButton_Dist.Text = app.dist_path;
    end
    
end

