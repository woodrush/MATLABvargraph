function checkvars(a)
    varnames = {'error_vars','nan_vars','inf_vars','complex_vars','real_vars'};
    failedTypes = [1 2 3 4];

    allvars = evalin('base','who');
    nan_vars = {};
    inf_vars = {};
    complex_vars = {};
    real_vars = {};
    error_vars = {};

    ret = 0;
    isFailed = false;
    for ind = 1:length(allvars)
        v = allvars(ind);
        try
            if strcmp('ans',v{1})
                continue
            end
            num = evalin('base',v{1});
            if ~isempty(find(isnan(num)))
                ret = 2;
                nan_vars = [nan_vars v];
            elseif ~isempty(find(isinf(num)))
                ret = 3;
                inf_vars = [inf_vars v];
            elseif ~isempty(find(imag(num)))
                ret = 4;
                complex_vars = [complex_vars v];
            else
                ret = 5;
                real_vars = [real_vars v];
            end
        catch err
            ret = 1;
            error_vars = [error_vars v];
        end
        if ~isempty(find(aaa==failedTypes))
            isFailed = true;
        end
    end

    disp('varcheck:')
    for v = varnames
        v = v{1};
        vval = eval(v);
        [rows,cols]=size(vval);
        fid=fopen(['./',v,'.txt'],'wt');
        for ind=1:rows
            fprintf(fid,'%s ',vval{ind,1:end-1});
            fprintf(fid,'%s',vval{ind,end});
        end
        fclose(fid);
        disp([v,': ', num2str(length(vval))]);
    end
    if isFailed
        ME = MException('MyComponent:checkvarAssertionError', 'assertionError');
        throw(ME)
    end
end
