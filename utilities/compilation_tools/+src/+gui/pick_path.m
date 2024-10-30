function pick_path(event, msg_string)
    default_path = src.helper.sys.default_path();
    target_path = uigetdir(default_path, msg_string);
    mode = lower(event.Source.Tag);

    if ~isempty(target_path)
        if src.helper.sys.validate_path(target_path, mode)
            src.helper.gui.set_path(app, target_path, mode);
        end
    end
end