bdclose('all');
load_system('/Users/jo/LBD/PIDDemo.slx');
[~, modelName, ~] = fileparts('/Users/jo/LBD/PIDDemo.slx');
cases = jsondecode('[{"name": "short_run", "stopTime": "1.0", "parameters": {"StopTime": "1.0"}}, {"name": "longer_run", "stopTime": "5.0", "parameters": {"StopTime": "5.0"}}]');
results = cell(numel(cases), 1);
overallOk = true;
for i = 1:numel(cases)
    caseOk = true;
    caseError = '';
    try
        if isfield(cases(i), 'parameters')
            paramNames = fieldnames(cases(i).parameters);
            for j = 1:numel(paramNames)
                name = paramNames{j};
                value = cases(i).parameters.(name);
                if ischar(value) || isstring(value)
                    set_param(modelName, name, char(value));
                else
                    set_param(modelName, name, num2str(value));
                end
            end
        end
        stopTime = cases(i).stopTime;
        if ~ischar(stopTime) && ~isstring(stopTime)
            stopTime = num2str(stopTime);
        end
        sim(modelName, 'StopTime', char(stopTime));
    catch ME
        caseOk = false;
        caseError = getReport(ME, 'extended', 'hyperlinks', 'off');
        overallOk = false;
    end
    results{i} = struct('name', cases(i).name, 'ok', caseOk, 'error', caseError);
end
result = struct('ok', overallOk, 'stage', 'test', 'model', modelName, 'results', {results});
fid = fopen('/Users/jo/LBD/PIDDemo_test_artifacts/test_report.json', 'w');
fwrite(fid, jsonencode(result), 'char');
fclose(fid);
if ~result.ok
    error('One or more test cases failed. See report JSON.');
end
