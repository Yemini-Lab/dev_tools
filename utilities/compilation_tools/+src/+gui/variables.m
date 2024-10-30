classdef variables < dynamicprops

    properties
        valid_color = [0.52, 1, 0.52];
        invalid_color = [1, 1, 0.52];

        script_tree = 'ScriptTree';
    end
    
    methods
        function obj = app()
            persistent app
            if isempty(app)
                app = src.helper.gui.get_app();
            else
                obj = app;
            end
        end

        function set_path(path, mode)
            app = src.helper.gui.app();

            switch mode
                case 'neuropal'
                    app.npal_path = path;
                    src.gui.variables.set_path(fullfile(path, '+Wrapper'), 'script');

                case 'script'
                    app.script_path = path;

                case 'dist'
                    app.dist_path = path;

                case 'dev_tools'

            end
            
            src.gui.components.toggle_path(path, mode);
        end
    end
end

