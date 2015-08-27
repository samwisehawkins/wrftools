#!/bin/bash
rename "%iY-%im-%id_%iH" "yesterday" SST:*
mv SST:* ../metgrid
