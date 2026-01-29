% Clear existing data
clear;
clc;
close all;

%% Import data for inspection

% If using HDF5, parameters are imported one a time to save on memory.
% Note as well that the data is converted to 'double' after import. This is
% required for a lot of the processing that is done. To instead work with
% integers, simply delete the 'double' conversion.
tk = double(h5read('./Data/events_recording_20260127_jackW.h5', '/timestamp'));
xk = double(h5read('./Data/events_recording_20260127_jackW.h5', '/x'));
yk = double(h5read('./Data/events_recording_20260127_jackW.h5', '/y'));
pk = double(h5read('./Data/events_recording_20260127_jackW.h5', '/polarity'));

% It is often convinient to convert the time into something with useful
% units. By default, the time vector is in microseconds AND time since
% start of the week. 
tk = (tk-tk(1))/1e6;  % [second]

%% Slice data into smaller range for processing
% Define start and end time to process [seconds]
t_start_process = 60.0; 
t_end_process   = 120.0; 

% Find indices within the valid range
valid_idx = tk >= t_start_process & tk <= t_end_process;

% Filter the data vectors
tk = tk(valid_idx);
xk = xk(valid_idx);
yk = yk(valid_idx);
pk = pk(valid_idx);

% Shift time to start at 0 for the new window
% This ensures your frame loop starts correctly at frame 1
tk = tk - t_start_process; 