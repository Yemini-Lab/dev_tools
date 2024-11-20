function out_struct = graphics_to_struct(handle)
    props = properties(handle);

    for p=1:length(props)
        pp = props{p};
        
        if isgraphics(handle.(pp))
            ppValue = Program.Validation.graphics_to_struct(handle.(pp));
        else
            ppValue = handle.(pp);
        end

        if p == 1
            out_struct = struct(pp, {ppValue});

        else
            out_struct.(pp) = {ppValue};

        end
    end

    if ~exist('out_struct', 'var')
        if handle == 0
            out_struct = 0;
        end
    end
end

