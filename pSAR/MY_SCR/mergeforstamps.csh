#!/bin/csh -f 
set mode = $1
set F = $2
set master = $3
set adi = $4
set patch_r = $5
set patch_a = $6
set overlap_r = $7
set overlap_a = $8

cat <<EOL > param_dir.txt
set raw_orig = `pwd`/$F/raw
set raw_data = `pwd`/$F
set topo = `pwd`/$F/topo
set stack = `pwd`/merge_stamps
set PS = `pwd`/merge_stamps/PS
set crop_SM =
EOL



mv param_dir.txt merge_stamps/param_dir.txt

cd merge_stamps
create_merge_input_ps.csh intflist .. $mode $F>merge_list
ln -s -f ../topo/dem.grd .
ln -s -f ../$F/batch_config_ps.cfg .
cp ../$F/intf.in .
sed -i -e 's/[:]/ /g' intf.in
awk '{print substr($1, 4, 8), substr($2, 4, 8)}' intf.in >intf_SM_list

merge_batch_ps.csh merge_list batch_config_ps.cfg $mode $F $master


#merge_swath ADIlist scatter_SM.grd master   

ls -d ../raw/*SAFE | grep -v $master | cut -c25-32 >date_no_master.txt


set XMAX = `grep num_rng_bins master.PRM | awk '{print $3}'`
set yvalid = `grep num_valid_az master.PRM| awk '{print $3}'`
set num_patch = `grep num_patches master.PRM | awk '{print $3}'`
set YMAX = `echo "$yvalid $num_patch" | awk '{print $1*$2}'`
set region = 0/$XMAX/0/$YMAX
echo $region

mkdir -p PS
cd PS
echo "mt_prep_gmtsar_SM $region $patch_r $patch_a $overlap_r $overlap_a $adi $master $F auto"
mt_prep_gmtsar_SM $region $patch_r $patch_a $overlap_r $overlap_a $adi $master $F auto
@ result = $patch_r * $patch_a
fix_pscands_SM.sh $result
