#!/bin/bash    
module add python/2.7
for f in $@ 
do
     echo $f
     
     dimsize=`ncdump -h $f | grep "time = UNLIMITED" | cut -d "(" -f2 | cut -d " " -f1`
     
     str1="time = UNLIMITED ; // ($dimsize currently)"
     str2="time = $dimsize ;"
     ncdump $f | sed -e "s#^.$str1# $str2#" | ncgen -o $f
     ncecat -O $f $f
     python add_time_dimensions.py $f
     ncks -O -x -v old_lat,old_lon,old_height,old_location $f $f
     ncap -O -s "leadtime=int(leadtime)" $f $f
 done
  

