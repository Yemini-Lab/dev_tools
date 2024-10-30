classdef components
    
    properties
        lamp_on = [0, 1, 0];
        lamp_off = [1, 0, 0];
    end
    
    methods
        function toggle_path(path, mode)
            button = app.(sprintf('SelectFolderButton_%s', mode));
            button.Text = path;
            button.BackgroundColor = src.gui.variables.valid_color;
        end

        function toggle_dependency(dependency)
            lamp = components.(sprintf('%_lamp', dependency));

            if lamp.Color == src.gui.variables.lamp_off
                lamp.Color = src.gui.variables.lamp_on;
                
            else
                lamp.Color = src.gui.variables.lamp_off;
            end
        end

        function toggle_scripts()
            app = src.gui.variables.app();
        end

        function add_script(name)
            app = src.gui.variables.app();
            uitreenode("Text", name, "Parent", components.script_tree());
            app.(src.gui.variables.script_tree).CheckedNodes = [];
        end
    end
end

