function [ data ] = get_time_series_WRFforecast_updates(Namelist);
%UNTITLED Summary of this function goes here
%   Detailed explanation goes here
%init
  first_time=1;

% list all dirs 
input_list=dir(Namelist{1,1}.forcast_data_timerseries)
nr_dirs=size(input_list)

for i=1:nr_dirs
    if length(input_list(i).name)==21
        % read the righ files in current lib 
        currentlib=[Namelist{1,1}.forcast_data_timerseries '/' input_list(i).name ]
        cd(currentlib) 
        % make filename 
        % get ddtg 
        ddtg=input_list(i).name(12:21);
        domaine_group=['_','d0',num2str(Namelist{4}.nwp_model_domain),'_'];
        file_name=strcat(currentlib,'/',Namelist{2}.location{1},domaine_group,ddtg(1:length(ddtg)),'.dat');
        
        fileInfo = dir(file_name);
        if not(isempty(fileInfo))
        fileSize = fileInfo.bytes; % make sure something is in the file 
        end
        fid = fopen(file_name)
        if not(fid==-1) & not(fileSize==0)
            format='%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s'
            [headers]=textscan(fid,format,1,'HeaderLines',3); % to get whole data set remove 100 when done testing 
            format='%s%s%f%f%f%f%f%f%f%f%f%f%f%f%f%f%f%f%f%f%f%f%f%f%f%f%f%f%f%f%f%f%f%f%f%f%f%f%f%f%f'

            [data_tempo position]=textscan(fid,format); % to get whole data set remove 100 when done testing 

       %first make sure that data looks like eta     
            tempo{1}= datestr(datenum(data_tempo{1},Namelist{1}.datstr_WRF_input_format),Namelist{1}.datstr_general_format);
            tempo{2,1}=cell2mat(headers{1})
            tempo{1,2}= datestr(datenum(data_tempo{2},Namelist{1}.datstr_WRF_input_format),Namelist{1}.datstr_general_format);
            tempo{2,2}=cell2mat(headers{2});
            tempo{1,3}= data_tempo{6}; %t2
            tempo{2,3}=cell2mat(headers{6});
            tempo{1,4}= data_tempo{6}; %tmp0_30mb
            tempo{2,4}=cell2mat(headers{6});
            tempo{1,5}= data_tempo{8}; %rh2 m
            tempo{2,5}=cell2mat(headers{8});
            tempo{1,6}= data_tempo{3}; %wspd 10
            tempo{2,6}=cell2mat(headers{3});
            tempo{1,7}= data_tempo{4}; %wdir
            tempo{2,7}=cell2mat(headers{4});
            tempo{1,8}= data_tempo{3}; %wspd 0_30_mb Not existing
            tempo{2,8}=cell2mat(headers{3});
            tempo{1,9}= data_tempo{4}; %wspd 0_30_mb Not existing
            tempo{2,9}=cell2mat(headers{4});
            tempo{1,10}= data_tempo{5}; %mslp
            tempo{2,10}=cell2mat(headers{5});
            tempo{1,11}= data_tempo{11}; % ustar
            tempo{2,11}=cell2mat(headers{11});
            tempo{1,12}= data_tempo{13}; % Rho 10m
            tempo{2,12}=cell2mat(headers{13});
            tempo{1,13}= data_tempo{13}; % rho 0_30mb
            tempo{2,13}=cell2mat(headers{13});
            tempo{1,14}=get_lead_time_2( Namelist,tempo);
            tempo{2,14}='Lead time'        
            
            tempo{2,15}=cell2mat(headers{15});
            tempo{1,15}=data_tempo{15}
            tempo{2,16}=cell2mat(headers{16});
            tempo{1,16}= data_tempo{16}; %t2
            tempo{2,17}=cell2mat(headers{17});
            tempo{1,17}= data_tempo{17}; %tmp0_30mb
            tempo{2,18}=cell2mat(headers{18});
            tempo{1,18}= data_tempo{18}; %rh2 m
            tempo{2,19}=cell2mat(headers{19});
            tempo{1,19}= data_tempo{19}; %wspd 10
            tempo{2,20}=cell2mat(headers{20});
            tempo{1,20}= data_tempo{20}; %wdir
            tempo{2,21}=cell2mat(headers{21});
            tempo{1,21}= data_tempo{21}; %wspd 0_30_mb Not existing
            tempo{2,22}=cell2mat(headers{22});
            tempo{1,22}= data_tempo{22}; %wspd 0_30_mb Not existing
            tempo{2,23}=cell2mat(headers{23});
            tempo{1,23}= data_tempo{23}; %mslp
            tempo{2,24}=cell2mat(headers{24});
            tempo{1,24}= data_tempo{24}; % ustar
            tempo{2,25}=cell2mat(headers{25});
            tempo{1,25}= data_tempo{25}; % Rho 10m
            tempo{2,26}=cell2mat(headers{26});
            tempo{1,26}= data_tempo{26}; % rho 0_30mb
            tempo{2,27}=cell2mat(headers{27});
            tempo{1,27}= data_tempo{27}; %t2
            tempo{2,28}=cell2mat(headers{28});
            tempo{1,28}= data_tempo{28}; %tmp0_30mb
            tempo{2,29}=cell2mat(headers{29});
            tempo{1,29}= data_tempo{29}; %rh2 m
            tempo{2,30}=cell2mat(headers{30});
            tempo{1,30}= data_tempo{30}; %wspd 10
            tempo{2,31}=cell2mat(headers{31});
            tempo{1,31}= data_tempo{31}; %wdir
            tempo{2,32}=cell2mat(headers{32});
            tempo{1,32}= data_tempo{32}; %wspd 0_30_mb Not existing
            tempo{2,33}=cell2mat(headers{33});
            tempo{1,33}= data_tempo{33}; %wspd 0_30_mb Not existing
            tempo{2,34}=cell2mat(headers{34});
            tempo{1,34}= data_tempo{34}; %mslp
            tempo{2,35}=cell2mat(headers{35});
            tempo{1,35}= data_tempo{35}; % ustar
            tempo{2,36}=cell2mat(headers{36});
            tempo{1,36}= data_tempo{36}; % Rho 10m
            tempo{2,37}=cell2mat(headers{37});
            tempo{1,37}= data_tempo{37}; % rho 0_30mb
            tempo{2,38}=cell2mat(headers{38});
            tempo{1,38}= data_tempo{38}; % rho 0_30mb
            tempo{2,39}=cell2mat(headers{39});
            tempo{1,39}= data_tempo{39}; % rho 0_30mb
            tempo{2,40}=cell2mat(headers{40});
            tempo{1,40}= data_tempo{40}; % rho 0_30mb
            tempo{2,41}=cell2mat(headers{41});
            tempo{1,41}= data_tempo{41}; % rho 0_30mb
           
            fclose(fid);
            % advance by 1 day
            
      % update time serie 
      if first_time
            data{1,1}= tempo{1,1} ;
            data{2,1}=tempo{2,1};
            data{1,2}=tempo{1,2};
            data{2,2}=tempo{2,2};
            data{1,3}=tempo{1,3};
            data{2,3}=tempo{2,3};
            data{1,4}=tempo{1,4};
            data{2,4}=tempo{2,4};
            data{1,5}=tempo{1,5};
            data{2,5}=tempo{2,5};
            data{1,6}=tempo{1,6};
            data{2,6}=tempo{2,6};
            data{1,7}=tempo{1,7};
            data{2,7}=tempo{2,7};
            data{1,8}=tempo{1,8};
            data{2,8}=tempo{2,8};
            data{1,9}=tempo{1,9};
            data{2,9}=tempo{2,9};
            data{1,10}=tempo{1,10};
            data{2,10}=tempo{2,10};
            data{1,11}=tempo{1,11};
            data{2,11}=tempo{2,11};
            data{1,12}=tempo{1,12};
            data{2,12}=tempo{2,12};
            data{1,13}=tempo{1,13};
            data{2,13}=tempo{2,13};
            data{1,14}=tempo{1,14};
            data{2,14}=tempo{2,14};
            data{1,15}=tempo{1,15};
            data{2,15}=tempo{2,15};
            data{1,16}=tempo{1,16};
            data{2,16}=tempo{2,16};
            data{1,17}=tempo{1,17};
            data{2,17}=tempo{2,17};
            data{1,18}=tempo{1,18};
            data{2,18}=tempo{2,18};
            data{1,19}=tempo{1,19};
            data{2,19}=tempo{2,19};
            data{1,20}=tempo{1,20};
            data{2,20}=tempo{2,20};
            data{1,21}=tempo{1,21};
            data{2,21}=tempo{2,21};
            data{1,22}=tempo{1,22};
            data{2,22}=tempo{2,22};
            data{1,23}=tempo{1,23};
            data{2,23}=tempo{2,23};
            data{1,24}=tempo{1,24};
            data{2,24}=tempo{2,24};
            data{1,25}=tempo{1,25};
            data{2,25}=tempo{2,25};
            data{1,26}=tempo{1,26};
            data{2,26}=tempo{2,26};
            data{1,27}=tempo{1,27};
            data{2,27}=tempo{2,27};
            data{1,28}=tempo{1,28};
            data{2,28}=tempo{2,28};
            data{1,29}=tempo{1,29};
            data{2,29}=tempo{2,29};
            data{1,30}=tempo{1,30};
            data{2,30}=tempo{2,30};
            data{1,31}=tempo{1,31};
            data{2,31}=tempo{2,31};
            data{1,32}=tempo{1,32};
            data{2,32}=tempo{2,32};
            data{1,33}=tempo{1,33};
            data{2,33}=tempo{2,33};
            data{1,34}=tempo{1,34};
            data{2,34}=tempo{2,34};
            data{1,35}=tempo{1,35};
            data{2,35}=tempo{2,35};
            data{1,36}=tempo{1,36};
            data{2,36}=tempo{2,36};
            data{1,37}=tempo{1,37};
            data{2,37}=tempo{2,37};
            data{1,38}=tempo{1,38};
            data{2,38}=tempo{2,38};
            data{1,39}=tempo{1,39};
            data{2,39}=tempo{2,39};
            data{1,40}=tempo{1,40};
            data{2,40}=tempo{2,40};
            data{1,41}=tempo{1,41};
            data{2,41}=tempo{2,41};
            first_time=0;
      else
            data{1,1}= vertcat(data{1,1},tempo{1,1}); 
            data{1,2}=vertcat(data{1,2},tempo{1,2});
            data{1,3}=vertcat(data{1,3},tempo{1,3});
            data{1,4}=vertcat(data{1,4},tempo{1,4});
            data{1,5}=vertcat(data{1,5},tempo{1,5});
            data{1,6}=vertcat(data{1,6},tempo{1,6});
            data{1,7}=vertcat(data{1,7},tempo{1,7});
            data{1,8}=vertcat(data{1,8},tempo{1,8});
            data{1,9}=vertcat(data{1,9},tempo{1,9});
            data{1,10}=vertcat(data{1,10},tempo{1,10});
            data{1,11}=vertcat(data{1,11},tempo{1,11});
            data{1,12}=vertcat(data{1,12},tempo{1,12});
            data{1,13}=vertcat(data{1,13},tempo{1,13});
            data{1,14}=vertcat(data{1,14},tempo{1,14});
            
            data{1,15}= vertcat(data{1,15},tempo{1,15}); 
            data{1,16}=vertcat(data{1,16},tempo{1,16});
            data{1,17}=vertcat(data{1,17},tempo{1,17});
            data{1,18}=vertcat(data{1,18},tempo{1,18});
            data{1,19}=vertcat(data{1,19},tempo{1,19});
            data{1,20}=vertcat(data{1,20},tempo{1,20});
            data{1,21}=vertcat(data{1,21},tempo{1,21});
            data{1,22}=vertcat(data{1,22},tempo{1,22});
            data{1,23}=vertcat(data{1,23},tempo{1,23});
            data{1,24}=vertcat(data{1,24},tempo{1,24});
            data{1,25}=vertcat(data{1,25},tempo{1,25});
            data{1,26}=vertcat(data{1,26},tempo{1,26});
            data{1,27}=vertcat(data{1,27},tempo{1,27});
            data{1,28}=vertcat(data{1,28},tempo{1,28});

            data{1,29}= vertcat(data{1,29},tempo{1,29}); 
            data{1,30}=vertcat(data{1,30},tempo{1,30});
            data{1,31}=vertcat(data{1,31},tempo{1,31});
            data{1,32}=vertcat(data{1,32},tempo{1,32});
            data{1,33}=vertcat(data{1,33},tempo{1,33});
            data{1,34}=vertcat(data{1,34},tempo{1,34});
            data{1,35}=vertcat(data{1,35},tempo{1,35});
            data{1,36}=vertcat(data{1,36},tempo{1,36});
            data{1,37}=vertcat(data{1,37},tempo{1,37});
            data{1,38}=vertcat(data{1,38},tempo{1,38});
            data{1,39}=vertcat(data{1,39},tempo{1,39});
            data{1,40}=vertcat(data{1,40},tempo{1,40});
            data{1,41}=vertcat(data{1,41},tempo{1,41});
            first_time=0;
        end % if length
    end 
% run trough all dirs and grab data 
    end
end % for nr directories 

