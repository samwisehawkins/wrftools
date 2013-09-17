function [ succes rank_unsorted rank_sorted ] = do_rank_histogram( Namelist,model,domaine,exp_name,analogs )
%DO_rank_unsorted_HISTOGRAM Summary of this function goes here
%   Detailed explanation goes here
%get the damm data
    file_path=['C:\Users\jnini\MATLAB\work\AnEn\data\workspace\',model,'\out\experiments\',exp_name]
    filename=strcat('\turbine_time_series_for_nr_analogs_',num2str(analogs))
    load([file_path,filename])
% do concanation of all turbines 
    obs=[];model=[];model_ensembles=[];model_ensembles_variance=[];
    [m n]=size(turbine_time_series)
    
        for i=1:n
            % concanate loop
            good_idx{i}=find(turbine_time_series(1,i).data{2,15}~=Namelist{1}.missing_value );
            obs=vertcat(turbine_time_series(1,i).data{2,15}(good_idx{i})/Namelist{10}.rated_capasity_kw,obs);
            model=vertcat(turbine_time_series(1,i).data{2,2}(good_idx{i})/Namelist{10}.rated_capasity_kw,model);
            model_ensembles=vertcat(turbine_time_series(1,i).data{2,18}(good_idx{i},:)/Namelist{10}.rated_capasity_kw,model_ensembles);
        end
        for i=1:analogs+1
            rank_unsorted(i)=0;
            rank_sorted(i)=0;
        end
        %Do rank_unsorteding of ensemble members
        for i=1:length(obs)
            %bin ensemble members
            [diff,index] = min(abs(obs(i)-model_ensembles(i,:)));
            max_member=max(model_ensembles(i,:));
            min_member=min(model_ensembles(i,:));
            switch 1
                case not(model_ensembles(i,index)==min_member)% meaning obs is less than the non smallest ensemble member 
                    rank_unsorted(index+1)=rank_unsorted(index+1)+1
                case (model_ensembles(i,index)==min_member)& obs(i)<model_ensembles(i,index) % meaning we are below the smallest ensemble member and therefore out
                    rank_unsorted(1)=rank_unsorted(1)+1
                case not(model_ensembles(i,index)==max_member)% meaning obs is bigger than than the non biggest ensemble member  
                    rank_unsorted(index+1)=rank_unsorted(index+1)+1
                case(model_ensembles(i,index)==max_member)& obs(i)>model_ensembles(i,index)% meaning obs is bigger than than the non biggest ensemble member  
                    rank_unsorted(analogs+1)=rank_unsorted(analogs+1)+1
            end % switch 
            
            [diff,index_sorted] = min(abs(obs(i)-sort(model_ensembles(i,:))));
            
            switch 1
                case not(model_ensembles(i,index_sorted)==min_member)% meaning obs is less than the non smallest ensemble member 
                    rank_sorted(index_sorted+1)=rank_sorted(index_sorted+1)+1
                case (model_ensembles(i,index_sorted)==min_member) & obs(i)<model_ensembles(i,index_sorted)% meaning we are below the smallest ensemble member 
                    rank_sorted(1)=rank_sorted(1)+1
                case not(model_ensembles(i,index_sorted)==max_member)% meaning obs is bigger than than the non biggest ensemble member  
                    rank_sorted(index_sorted+1)=rank_sorted(index_sorted+1)+1
                case (model_ensembles(i,index_sorted)==max_member)& obs(i)>model_ensembles(i,index)% meaning obs is bigger than than the biggest ensemble member  
                    rank_sorted(analogs+1)=rank_sorted(analogs+1)+1
            end %Switch 
        end
        if not(isempty(rank_unsorted))
            succes=1
        else
             succes=0
        end
        
end

