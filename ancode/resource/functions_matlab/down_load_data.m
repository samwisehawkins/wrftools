function [ new_timeseries_data new_2d_data ] = down_load_data( Namelist )
%DOWN_LOAD_DATA Summary of this function goes here
%   Detailed explanation goes here
% 
system('set path="C:\Program Files\WinRAR\";%path%');
get_all_files_on_ftp=0;
total_size=0;
try
    mw=ftp('ftp.risoe.dk');
catch err
    display('Ftp site not open. exiting')
    exit
end

cd(mw,'pub/met/ahah/ForVestas');
forecast_freq=Namelist{1,1}.forecast_initial_time(2)-Namelist{1,1}.forecast_initial_time(1)

%tjeck size of data dir befor download
cd(Namelist{1}.forcast_data_timerseries);
% size of data-dir before download
[file_info]=dir(Namelist{1}.forcast_data_timerseries);
[nr_file dummy]=size(file_info);

        warning off ; % get content of ftp site 
            [Files,Bytes,Dates] = dirr(Namelist{1}.forcast_data_timerseries,'\.dat\>','name');
                total_timeseries_size_before_download=Bytes.total;
            [Files,Bytes,Dates] = dirr(Namelist{1}.forcast_data_2d_fileds,'\.nc\>','name');
                total_2d_size_before_download=Bytes.total;
        warning on 
               display(['Download time is: ', datestr(now,'yyyy-mm-dd HH:MM')])

%first look for closetst date the date 12 hou old then 24 
forecast_date=datenum(now);
for j=1:Namelist{1}.look_back_cycles
        cd(Namelist{1}.forcast_data_timerseries);
        [Y, M, D, H, MN, S] = datevec(forecast_date);
        ftp_info=dir(mw)
        %ftp_filenames=ftp_info(2:length(ftp_info).name)
        for i=1:length(ftp_info)
            ftp_filenames{i,:}=ftp_info(i,:).name;
        end

               %find closest initial time
               [val idx]=min(abs(H-Namelist{1}.forecast_initial_time));
               switch 1 % currently only two options but could be more with more initial times 
                   case (H-Namelist{1}.forecast_initial_time(idx))<0 %initial time later then now
                       init_time=Namelist{1}.forecast_initial_time(idx-1);
                   case (H-Namelist{1}.forecast_initial_time(idx))>=0
                       init_time=Namelist{1}.forecast_initial_time(idx);
               end
               display(['closest available run initilized at: ', datestr([Y M D init_time 0 0],'yyyy-mm-dd HH:MM')])

               %D=D-1; 
               %generate file name 
               timeserie_file_names=['TimeSeries_' num2str(Y) sprintf('%02d',(M)) sprintf('%02d',(D)),sprintf('%02d',(init_time)) '*' ];
               timeserie_all_file_names=['TimeSeries_*'];
               % GET all files from today 
               if get_all_files_on_ftp
                   display('Download everyting from Risø ftp')
                   mget(mw,timeserie_all_file_names)
                   files=dir('*.gz')
                   % extract 
                   for i=1:length(files)
                        warning off 
                        if files(i).isdir==0 & files(i).bytes>10000% only untar if directory does not allready exist
                            untar(files(i).name,files(i).name(1:length(files(i).name)-7))
                        end
                        display(['extracting:',files(i).name])
                        warning on

                   end
               else

                        display(['Downloading from dates:',timeserie_file_names(12:length(timeserie_file_names)-1),' from ftp'])
                        mget(mw,timeserie_file_names);
                        files=dir(timeserie_file_names);
                for i=1:length(files)
                        warning off %title(name(i));%warning on MATLAB:tex;
                        if files(i).isdir==0 % only untar if directory does not allready exist
                            warning off
                            display(['extracting:',files(i).name])
                            untar(files(i).name,files(i).name(1:length(files(i).name)-7))
                            warning on
                        end
                    end

               end

                % clean all.tar.gz 
                delete('*.tar.gz')

               %generate file names for 2 d fields
                forecast_data_2_d_data_domaine_1_file_names=['Vestas_d01_' num2str(Y) '-' sprintf('%02d',M) '-' sprintf('%02d',(D)) '_' sprintf('%02d',(init_time)) '.nc' ];
                forecast_data_2_d_data_domaine_1_all_file_names=['Vestas_d01_*'];

                forecast_data_2_d_data_domaine_2_file_names=['Vestas_d02_'  num2str(Y) '-' sprintf('%02d',M) '-' sprintf('%02d',(D)) '_' sprintf('%02d',(init_time)) '.nc' ];
                forecast_data_2_d_data_domaine_2_all_file_names=['Vestas_d02_*' ];

                forecast_data_2_d_data_domaine_3_file_names=['Vestas_d03_'  num2str(Y) '-' sprintf('%02d',M) '-' sprintf('%02d',(D)) '_' sprintf('%02d',(init_time)) '.nc' ];
                forecast_data_2_d_data_domaine_3_all_file_names=['Vestas_d03_*' ];

                cd(Namelist{1}.forcast_data_2d_fileds)   
               % GET all files from today 
               if get_all_files_on_ftp
                 mget(mw,forecast_data_2_d_data_domaine_1_all_file_names)    ;
                 mget(mw,forecast_data_2_d_data_domaine_2_all_file_names)    ;
                 mget(mw,forecast_data_2_d_data_domaine_3_all_file_names)    ;
               else
                   if not(exist(forecast_data_2_d_data_domaine_3_file_names,'file')) & ~isempty(find(strcmp(ftp_filenames,forecast_data_2_d_data_domaine_3_file_names)))
                       % if file notpresent on local mashine and exist on ftp then
                       % download
                       display(['downloading:',forecast_data_2_d_data_domaine_1_file_names])
                          mget(mw,forecast_data_2_d_data_domaine_1_file_names);
                       display(['downloading:',forecast_data_2_d_data_domaine_2_file_names])
                          mget(mw,forecast_data_2_d_data_domaine_2_file_names);    
                       display(['downloading:',forecast_data_2_d_data_domaine_3_file_names])
                         mget(mw,forecast_data_2_d_data_domaine_3_file_names);    
                   end
               end

             forecast_date=addtodate(forecast_date,-forecast_freq, 'hour');
end% for number of lookback cykles 

% now tjeck if new data arrived 
                warning off ;
               [Files,Bytes,Dates] = dirr(Namelist{1}.forcast_data_timerseries,'\.dat\>','name');
               total_timeseries_size_after_download=Bytes.total;
               clear Bytes
               [Files,Bytes,Dates] = dirr(Namelist{1}.forcast_data_2d_fileds,'\.nc\>','name');
               total_2d_size_after_download=Bytes.total;
               warning on ;

                 if total_timeseries_size_before_download<total_timeseries_size_after_download
                    new_timeseries_data=1 % check is any data is downloaded then set to 1 
                 else
                     new_timeseries_data=0;
                 end
                 if total_2d_size_before_download<total_2d_size_after_download
                    new_2d_data=1 ;% check is any data is downloaded then set to 1 
                 else
                     new_2d_data=0;
                 end
              display(['total size of time series files after download: ',sprintf('%2.2f',total_timeseries_size_after_download/1000000),' mb and ',sprintf('%2.2f',total_timeseries_size_before_download/1000000),' mb before download '])
              display(['     total size of 2d .nc files after download: ',sprintf('%2.2f',total_2d_size_after_download/1000000),' mb and ',sprintf('%2.2f',total_2d_size_before_download/1000000),' mb before download '])
             

end

