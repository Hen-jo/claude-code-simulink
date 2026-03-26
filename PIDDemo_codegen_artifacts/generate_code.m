result = struct('ok', false, 'stage', 'codegen', 'model', '/Users/jo/LBD/PIDDemo.slx', 'target', 'ert.tlc', 'artifactDir', '/Users/jo/LBD/PIDDemo_codegen_artifacts', 'error', '');
try
    bdclose('all');
    load_system('/Users/jo/LBD/PIDDemo.slx');
    [~, modelName, ~] = fileparts('/Users/jo/LBD/PIDDemo.slx');
    cd('/Users/jo/LBD/PIDDemo_codegen_artifacts');
    set_param(modelName, 'SystemTargetFile', 'ert.tlc');
    slbuild(modelName);
    result.ok = true;
catch ME
    result.error = getReport(ME, 'extended', 'hyperlinks', 'off');
end

fid = fopen('/Users/jo/LBD/PIDDemo_codegen_artifacts/codegen_report.json', 'w');
if fid ~= -1
    fwrite(fid, jsonencode(result), 'char');
    fclose(fid);
end

if ~result.ok
    error(result.error);
end
