function total_bytes = get_dir_size(path, fmts, progress)
    app = src.gui.variables.app();
    progress_msg = progress.Message;
    total_bytes = 0;

    progress.Message = "Searching environment...";
    S = dir(path);

    progress.Message = "Grabbing subdirectories...";
    N = setdiff({S([S.isdir]).name},{'.','..'});

    for ii = 1:numel(N)
        p_msg = char(sprintf("%s \nScanning %s...", progress_msg, N{ii}));
        progress.Message = p_msg;
        progress.Value = ii/numel(N);
        app.write_log(p_msg);

        T = dir(fullfile(path,N{ii},fmts));
        C = {T(~[T.isdir]).name};

        for jj = 1:numel(C)
            progress.Message = sprintf("%s -> %s...", p_msg(1:end-3), C{jj});
            progress.Value = min(ii+(jj/numel(C)), 1)/numel(N);
            app.write_log(progress.Message);

            F = dir(fullfile(path,N{ii},C{jj}));
            if size(F, 1) == 1
                total_bytes = total_bytes + F.bytes;
            else
                total_bytes = total_bytes + sum([F.bytes]);
            end
        end
    end
end

