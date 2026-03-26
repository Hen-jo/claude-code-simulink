result = struct('ok', false, 'stage', 'compile', 'model', '/Users/jo/LBD/PIDDemo.slx', 'error', '');
try
    bdclose('all');
    load_system('/Users/jo/LBD/PIDDemo.slx');
    [~, modelName, ~] = fileparts('/Users/jo/LBD/PIDDemo.slx');
    set_param(modelName, 'SimulationCommand', 'update');
    feval(modelName, [], [], [], 'compile');
    feval(modelName, [], [], [], 'term');
    result.ok = true;
catch ME
    result.error = getReport(ME, 'extended', 'hyperlinks', 'off');
end

fid = fopen('/Users/jo/LBD/PIDDemo_compile_artifacts/compile_report.json', 'w');
if fid ~= -1
    fwrite(fid, jsonencode(result), 'char');
    fclose(fid);
end

if ~result.ok
    error(result.error);
end
