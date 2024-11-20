function dh_struct = dehandler(in_struct)
    in_fields = fieldnames(in_struct);

    for f=1:length(in_fields)
        field_name = in_fields{f};
        in_value = in_struct.(field_name);

        if isstruct(in_value)
            tValue = Program.Validation.dehandler(in_value);

        elseif isnumeric(in_value)
            tValue = in_value;

        elseif isgraphics(in_value) & ~isnumeric(in_value)
            tValue = Program.Validation.graphics_to_struct(in_value);

        else
            tValue = in_value;

        end

        if ~exist('tValue', 'var')
            keyboard
        end

        if ~exist('dh_struct', 'var')
            dh_struct = struct(field_name, {tValue});

        else
            dh_struct.(field_name) = {tValue};
            
        end
    end
end

