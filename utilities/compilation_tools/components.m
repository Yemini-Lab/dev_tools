classdef components
    %COMPONENTS Summary of this class goes here
    %   Detailed explanation goes here
    
    properties
    end
    
    methods
        function obj = script_tree()
            persistent tree

            if isempty(tree)
                app = src.gui.variables.app();
                tree = app.(src.gui.variables.script_tree);
            end

            obj = tree;
        end

        function obj = neuropal_lamp()
            persistent npal_lamp

            if isempty(npal_lamp)
                app = src.gui.variables.app();
                npal_lamp = app.(src.gui.variables.lamps.npal);
            end

            obj = npal_lamp;
        end
    end
end

