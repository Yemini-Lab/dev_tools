classdef log

    properties
        component_name = 'ConsoleTextArea';
    end
    
    methods (Static)
        function obj = init()
            persistent logger
            if isempty(logger)
                app = src.gui.variables.app();
                logger = src.helper.log.get_gui(app);
            else
                obj = logger;
            end
        end
        
        function write(string)
            component = src.helper.gui.init();
            component.Value{end+1} = sprintf('\n%s', string);
            scroll(component, 'bottom')
        end

        function component = get_gui()
            app = src.gui.variables.app();
            component = app.(src.helper.log.component_name);
        end

    end
end

