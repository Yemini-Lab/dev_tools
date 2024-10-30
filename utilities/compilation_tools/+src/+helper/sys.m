classdef sys

    properties
        Property1
    end
    
    methods (Static)
        function path = default_path()
            path = fullfile('C:', 'Users', getenv('username'), 'Documents', 'GitHub', 'NeuroPAL_ID');
        end

        function code = validate_path(path, type)
            switch type
                case 'neuropal'
                    must_find = {'visualize_light.mlapp', '+Wrapper'};

                case 'scripts'
                    must_find = {'recommend_frames.py'};

                case 'dist'
                    must_find = {'for_redistribution_files_only'};

                case 'dev_tools'
                    must_find = {'utilities'};

            end

            code = 1;
            for n=1:length(must_find)
                req = must_find{n};

                if contains(req, '.')
                    has_req = isfile(path, req);

                else
                    has_req = isfolder(path, req);

                end

                if ~has_req
                    src.log.write(sprintf("WARNING: %s not found in %s!", req, path));
                    code = 0;
                end
            end
        end

    end
end

