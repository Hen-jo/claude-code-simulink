result = struct('ok', false, 'stage', 'clone', 'source', '/Users/jo/LBD/PIDDemo.slx', 'output', '/Users/jo/LBD/PIDDemo_copy.slx', 'error', '');
try
    bdclose('all');
    load_system('/Users/jo/LBD/PIDDemo.slx');
    [~, modelName, ~] = fileparts('/Users/jo/LBD/PIDDemo.slx');
    save_system(modelName, '/Users/jo/LBD/PIDDemo_copy.slx');
    result.ok = true;
catch ME
    result.error = getReport(ME, 'extended', 'hyperlinks', 'off');
end

fid = fopen('/Users/jo/LBD/PIDDemo_copy_clone_artifacts/clone_report.json', 'w');
if fid ~= -1
    fwrite(fid, jsonencode(result), 'char');
    fclose(fid);
end

if ~result.ok
    error(result.error);
end
