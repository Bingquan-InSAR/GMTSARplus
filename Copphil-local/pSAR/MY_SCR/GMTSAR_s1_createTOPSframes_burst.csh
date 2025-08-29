#!/bin/csh -f
#       $Id$
#
# Xiaohua(Eric) Xu, Mar 18, 2017
# Modified: add iws.in control for subswath selection
#
# used for creating a new frame based on two input frames.
#

echo $#argv
if ($#argv <= 4) then
    echo ""
    echo "Usage: GMTSAR_s1_createTOPSframes.csh SAFE_filelist ****.EOF two_pins.ll [mode] [outdir]"
    echo "       create one frame based on the two input frames, precise/restituted orbit is required"
    echo ""
    echo "  format of two_pins.llt (lon2/lat2 comes later than lon1/lat1 in orbit time):"
    echo "    lon11 lat11 [lon12 lat12] [lon13 lat13]"
    echo "    lon21 lat21 [lon22 lat22] [lon23 lat23]"
    echo "    (drop more columns if you want subsath 2 and 3 to have different boundaries)"
    echo ""
    echo "  outputs:"
    echo "    new.SAFE --> datetime1-datetime2.SAFE"
    echo ""
    echo "  Note:"
    echo "    The two input .SAFE file should be in time order, if the two_pin.llt is at wrong location, the program will output all the bursts."
    echo "    mode = 1, output vv; mode = 2, output vh; default is vv"
    echo "    Files listed in SAFE_filelist should be the absolute path"
    echo ""
    exit 1
endif

if ($#argv == 3) then
    set mode = `echo "vv"`
else 
    if ($4 == 1) then
        set mode = `echo "vv"`
    else
        set mode = `echo "vh"`
    endif
endif
if ($#argv < 5) then
    set outdir = `pwd`
else
    set outdir = $5
endif

set ncol = `awk '{print NF}' $3 | head -1`
echo "Combining $mode data..."

set pth = `pwd`
set filelist = $1
set orb = $2
set tps = $3

if (-d new.SAFE) then
    rm -r new.SAFE
endif
mkdir new.SAFE
mkdir new.SAFE/annotation new.SAFE/measurement

# ---- read iws.in and decide which subswaths to process ----
# iws.in can be "0,1,0" or "0 1 0"; default to 1 1 1 if missing
if (-e /mnt/Test/iws.in) then
    set iws = (`sed 's/,/ /g' /mnt/Test/iws.in`)
else
    set iws = (1 1 1)
endif

# ensure we have 3 numbers
if ($#iws < 3) then
    if ($#iws == 0) then
        set iws = (1 1 1)
    else if ($#iws == 1) then
        set iws = ($iws[1] 1 1)
    else if ($#iws == 2) then
        set iws = ($iws[1] $iws[2] 1)
    endif
endif
set do_iw1 = $iws[1]
set do_iw2 = $iws[2]
set do_iw3 = $iws[3]
echo "IWS selection -> iw1=$do_iw1 iw2=$do_iw2 iw3=$do_iw3"

# prevent running with 0,0,0
if ($do_iw1 == 0 && $do_iw2 == 0 && $do_iw3 == 0) then
    echo "iws.in is 0,0,0 -> no subswath selected. Exiting."
    exit 2
endif
# -----------------------------------------------------------

# work on the first subswath
if ($do_iw1 == 1) then
    echo ""
    echo "Working on subswath 1 ..."
    set a = `awk NR==1'{print $0}' $filelist`
    cd $a/measurement
    set f0 = `ls *iw1*$mode*tiff | awk '{print substr($1,1,length($1)-5)}'`
    set head1 = `echo $f0 | awk '{print substr($1,1,15)}'`
    cd $pth
    set a = ""
    foreach line (`awk '{print $0}' $filelist`)
        cd $line/measurement
        set f1 = `ls *iw1*$mode*tiff | awk '{print substr($1,1,length($1)-5)}'`
        cd $pth
        set a = `echo $a $f1`
        cd new.SAFE
        if (-e $f1.xml) rm $f1.xml -f
        if (-e $f1.tiff) rm $f1.tiff -f
        ln -s $line/annotation/$f1.xml    .
        ln -s $line/measurement/$f1.tiff  .
        cd ..
    end
    cd new.SAFE 
    make_s1a_tops $f0.xml $f0.tiff tmp1 0
    ext_orb_s1a tmp1.PRM $orb tmp1
    set ll1 = `awk NR==1'{print $1,$2}' ../$tps`
    set ll2 = `awk NR==2'{print $1,$2}' ../$tps`
    set tmpazi = `echo "$ll1 0" | SAT_llt2rat tmp1.PRM 1 | awk '{print $2}'`
    shift_atime_PRM.csh tmp1.PRM $tmpazi
    set azi1 = `echo "$ll1 0" | SAT_llt2rat tmp1.PRM 1 | awk '{printf("%d",$2+0.5 + '$tmpazi')}'`
    set azi2 = `echo "$ll2 0" | SAT_llt2rat tmp1.PRM 1 | awk '{printf("%d",$2+0.5 + '$tmpazi')}'`
    assemble_tops $azi1 $azi2 $a new
    set tail1 = `echo $f1 | awk '{print substr($1,length($1)-16,17)}'`
    set date = `grep startTime new.xml | awk -F">" '{print $2}' | awk -F"<" '{print substr($1,1,4)substr($1,6,2)substr($1,9,2)}'`
    set t1 = `grep startTime new.xml | awk -F">" '{print $2}' | awk -F"<" '{print substr($1,12,2)substr($1,15,2)substr($1,18,9)}' | awk '{printf("%.6d",$1+0.5)}'`
    set t2 = `grep stopTime new.xml | awk -F">" '{print $2}' | awk -F"<" '{print substr($1,12,2)substr($1,15,2)substr($1,18,9)}' | awk '{printf("%.6d",$1+0.5)}'`
    mv new.xml annotation/$head1$date"t"$t1"-"$date"t"$t2"-"$tail1.xml
    mv new.tiff measurement/$head1$date"t"$t1"-"$date"t"$t2"-"$tail1.tiff
    rm *.tiff *.xml tmp1*
    cd ..
endif

# work on the second subswath
if ($do_iw2 == 1) then
    echo ""
    echo "Working on subswath 2 ..."
    set a = `awk NR==1'{print $0}' $filelist`
    cd $a/measurement
    set f0 = `ls *iw2*$mode*tiff | awk '{print substr($1,1,length($1)-5)}'`
    set head1 = `echo $f0 | awk '{print substr($1,1,15)}'`
    cd $pth
    set a = ""
    foreach line (`awk '{print $0}' $filelist`)
        cd $line/measurement
        set f1 = `ls *iw2*$mode*tiff | awk '{print substr($1,1,length($1)-5)}'`
        cd $pth
        set a = `echo $a $f1`
        cd new.SAFE
        if (-e $f1.xml) rm $f1.xml -f
        if (-e $f1.tiff) rm $f1.tiff -f
        ln -s $line/annotation/$f1.xml .
        ln -s $line/measurement/$f1.tiff .
        cd ..
    end
    cd new.SAFE
    make_s1a_tops $f0.xml $f0.tiff tmp1 0
    ext_orb_s1a tmp1.PRM $orb tmp1
    if ($ncol >= 4) then
        set ll1 = `awk NR==1'{print $3,$4}' ../$tps`
        set ll2 = `awk NR==2'{print $3,$4}' ../$tps`
    else
        set ll1 = `awk NR==1'{print $1,$2}' ../$tps`
        set ll2 = `awk NR==2'{print $1,$2}' ../$tps`
    endif
    set tmpazi = `echo "$ll1 0" | SAT_llt2rat tmp1.PRM 1 | awk '{print $2}'`
    shift_atime_PRM.csh tmp1.PRM $tmpazi
    set azi1 = `echo "$ll1 0" | SAT_llt2rat tmp1.PRM 1 | awk '{printf("%d",$2+0.5 + '$tmpazi')}'`
    set azi2 = `echo "$ll2 0" | SAT_llt2rat tmp1.PRM 1 | awk '{printf("%d",$2+0.5 + '$tmpazi')}'`
    assemble_tops $azi1 $azi2 $a new 
    set tail1 = `echo $f1 | awk '{print substr($1,length($1)-16,17)}'`
    set date = `grep startTime new.xml | awk -F">" '{print $2}' | awk -F"<" '{print substr($1,1,4)substr($1,6,2)substr($1,9,2)}'`
    set t1 = `grep startTime new.xml | awk -F">" '{print $2}' | awk -F"<" '{print substr($1,12,2)substr($1,15,2)substr($1,18,9)}' | awk '{printf("%.6d",$1+0.5)}'`
    set t2 = `grep stopTime new.xml | awk -F">" '{print $2}' | awk -F"<" '{print substr($1,12,2)substr($1,15,2)substr($1,18,9)}' | awk '{printf("%.6d",$1+0.5)}'`
    mv new.xml annotation/$head1$date"t"$t1"-"$date"t"$t2"-"$tail1.xml
    mv new.tiff measurement/$head1$date"t"$t1"-"$date"t"$t2"-"$tail1.tiff
    rm *.tiff *.xml tmp1*
    cd ..
endif

# work on the third subswath
if ($do_iw3 == 1) then
    echo ""
    echo "Working on subswath 3 ..."
    set a = `awk NR==1'{print $0}' $filelist`
    cd $a/measurement
    set f0 = `ls *iw3*$mode*tiff | awk '{print substr($1,1,length($1)-5)}'`
    set head1 = `echo $f0 | awk '{print substr($1,1,15)}'`
    cd $pth
    set a = ""
    foreach line (`awk '{print $0}' $filelist`)
        cd $line/measurement
        set f1 = `ls *iw3*$mode*tiff | awk '{print substr($1,1,length($1)-5)}'`
        cd $pth
        set a = `echo $a $f1`
        cd new.SAFE
        if (-e $f1.xml) rm $f1.xml -f
        if (-e $f1.tiff) rm $f1.tiff -f
        ln -s $line/annotation/$f1.xml .
        ln -s $line/measurement/$f1.tiff .
        cd ..
    end 
    cd new.SAFE
    make_s1a_tops $f0.xml $f0.tiff tmp1 0
    ext_orb_s1a tmp1.PRM $orb tmp1
    if ($ncol >= 6) then
        set ll1 = `awk NR==1'{print $5,$6}' ../$tps`
        set ll2 = `awk NR==2'{print $5,$6}' ../$tps`
    else
        set ll1 = `awk NR==1'{print $1,$2}' ../$tps`
        set ll2 = `awk NR==2'{print $1,$2}' ../$tps`
    endif
    set tmpazi = `echo "$ll1 0" | SAT_llt2rat tmp1.PRM 1 | awk '{print $2}'`
    shift_atime_PRM.csh tmp1.PRM $tmpazi
    set azi1 = `echo "$ll1 0" | SAT_llt2rat tmp1.PRM 1 | awk '{printf("%d",$2+0.5 + '$tmpazi')}'`
    set azi2 = `echo "$ll2 0" | SAT_llt2rat tmp1.PRM 1 | awk '{printf("%d",$2+0.5 + '$tmpazi')}'`
    assemble_tops $azi1 $azi2 $a new
    set tail1 = `echo $f1 | awk '{print substr($1,length($1)-16,17)}'`
    set date = `grep startTime new.xml | awk -F">" '{print $2}' | awk -F"<" '{print substr($1,1,4)substr($1,6,2)substr($1,9,2)}'`
    set t1 = `grep startTime new.xml | awk -F">" '{print $2}' | awk -F"<" '{print substr($1,12,2)substr($1,15,2)substr($1,18,9)}' | awk '{printf("%.6d",$1+0.5)}'`
    set t2 = `grep stopTime new.xml | awk -F">" '{print $2}' | awk -F"<" '{print substr($1,12,2)substr($1,15,2)substr($1,18,9)}' | awk '{printf("%.6d",$1+0.5)}'`
    mv new.xml annotation/$head1$date"t"$t1"-"$date"t"$t2"-"$tail1.xml
    mv new.tiff measurement/$head1$date"t"$t1"-"$date"t"$t2"-"$tail1.tiff
    rm *.tiff *.xml tmp1*
    cd ..
endif

# copy manifest and rename new SAFE
set a = `awk NR==1'{print $0}' $filelist`
cp $a/manifest.safe new.SAFE/
echo ""
echo "Editing name of the new file..."
set tail2 = `echo $a | awk '{print substr($1,length($1)-22,23)}'`
set t1 = `ls new.SAFE/annotation/*.xml | awk '{print substr($1,length($1)-43,6)}' | gmt gmtinfo -C | awk '{printf("%.6d", $1)}'`
set t2 = `ls new.SAFE/annotation/*.xml | awk '{print substr($1,length($1)-27,6)}' | gmt gmtinfo -C | awk '{printf("%.6d", $2)}'`
set date1 = `ls new.SAFE/annotation/*.xml | awk '{print substr($1,length($1)-52,8)}' | gmt gmtinfo -C | awk '{print $1}'`
set head2 = `echo $a | awk '{print substr($1,length($1)-71,17)}'`
set newname = `echo $head2$date1"T"$t1"_"$date1"T"$t2"_"$tail2`
if (-d $newname) rm -r $outdir/$newname
mv new.SAFE $outdir/$newname

grep -Hn '<sliceList count="0">' $outdir/$newname/annotation/*xml
foreach f ($outdir/$newname/annotation/*xml)
    sed -i.bak 's#<sliceList count="0">#<sliceList count="0"></sliceList>#g' "$f"
    rm -f "$f.bak"
end
