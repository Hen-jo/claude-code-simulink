result = struct('ok', false, 'stage', 'build', 'model', '/Users/jo/LBD/PIDDemo.slx', 'error', '');
try
    bdclose('all');
    new_system('PIDDemo');
    open_system('PIDDemo');
    add_block('simulink/Sources/In1', 'PIDDemo/Reference', 'Position', [40 130 70 150], 'MakeNameUnique', 'off');
    add_block('simulink/Math Operations/Sum', 'PIDDemo/ErrorSum', 'Position', [120 120 150 150], 'MakeNameUnique', 'off');
    set_param('PIDDemo/ErrorSum', 'Inputs', '+-');
    add_block('simulink/Math Operations/Gain', 'PIDDemo/Kp', 'Position', [220 60 270 90], 'MakeNameUnique', 'off');
    set_param('PIDDemo/Kp', 'Gain', '1.0');
    add_block('simulink/Continuous/Integrator', 'PIDDemo/Ki', 'Position', [220 120 250 150], 'MakeNameUnique', 'off');
    add_block('simulink/Continuous/Derivative', 'PIDDemo/Kd', 'Position', [220 180 250 210], 'MakeNameUnique', 'off');
    add_block('simulink/Math Operations/Sum', 'PIDDemo/ControlSum', 'Position', [320 115 350 155], 'MakeNameUnique', 'off');
    set_param('PIDDemo/ControlSum', 'Inputs', '+++');
    add_block('simulink/Continuous/Transfer Fcn', 'PIDDemo/Plant', 'Position', [420 120 500 150], 'MakeNameUnique', 'off');
    set_param('PIDDemo/Plant', 'Denominator', '[1 1]', 'Numerator', '[1]');
    add_block('simulink/Sinks/Out1', 'PIDDemo/Output', 'Position', [600 130 630 150], 'MakeNameUnique', 'off');
    add_block('simulink/Sinks/Scope', 'PIDDemo/Scope', 'Position', [600 40 630 70], 'MakeNameUnique', 'off');
    add_line('PIDDemo', 'Reference/1', 'ErrorSum/1', 'autorouting', 'on');
    add_line('PIDDemo', 'ErrorSum/1', 'Kp/1', 'autorouting', 'on');
    add_line('PIDDemo', 'ErrorSum/1', 'Ki/1', 'autorouting', 'on');
    add_line('PIDDemo', 'ErrorSum/1', 'Kd/1', 'autorouting', 'on');
    add_line('PIDDemo', 'Kp/1', 'ControlSum/1', 'autorouting', 'on');
    add_line('PIDDemo', 'Ki/1', 'ControlSum/2', 'autorouting', 'on');
    add_line('PIDDemo', 'Kd/1', 'ControlSum/3', 'autorouting', 'on');
    add_line('PIDDemo', 'ControlSum/1', 'Plant/1', 'autorouting', 'on');
    add_line('PIDDemo', 'Plant/1', 'Output/1', 'autorouting', 'on');
    add_line('PIDDemo', 'Plant/1', 'Scope/1', 'autorouting', 'on');
    add_line('PIDDemo', 'Plant/1', 'ErrorSum/2', 'autorouting', 'on');
    set_param('PIDDemo', 'Solver', 'ode45');
    set_param('PIDDemo', 'StopTime', '10');
    save_system('PIDDemo', '/Users/jo/LBD/PIDDemo.slx');
    result.ok = true;
catch ME
    result.error = getReport(ME, 'extended', 'hyperlinks', 'off');
end

fid = fopen('/Users/jo/LBD/PIDDemo_artifacts/build_report.json', 'w');
if fid ~= -1
    fwrite(fid, jsonencode(result), 'char');
    fclose(fid);
end

if ~result.ok
    error(result.error);
end
