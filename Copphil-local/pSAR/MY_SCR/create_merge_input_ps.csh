#!/bin/csh -f

# input is list of files in intf_all
###############################################################################
# Create Merge Input Script for STAMPS Subswath Merging
# Updated by Bingquan Li and Ling Chang on August 19, 2025
#
# Purpose:
#   Generate input lines for use in merge_batch.csh by combining PRM files from
#   F1, F2, and F3 subswaths according to selected merge mode.
#   Supports full merging (F1+F2+F3), partial merging (F1+F2 or F2+F3),
#   or single-frame output for a specified subswath (F1/F2/F3).
###############################################################################
if ($#argv != 4) then
  echo ""
  echo "Usage: create_merge_input.csh intf_list path mode"
  echo ""
  echo "    Used to create inputlist for merge_batch.csh "
  echo "    input intf_list is the folder names in F?/intf_all"
  echo "    mode 0 is merging all 3 subswaths, mode 1 is for F1/F2"
  echo "    mode 2 is for F2/F3"
  echo ""
  echo "    Example: create_merge_input.csh intflist .. 0"
  echo ""
  exit 1
endif

set mode = $3
set dir = $2
set F = $4

foreach line (`awk '{print $0}' $1`)
  if ($mode == 0 || $mode == 1) then
    ls $dir/F1/stamps/$line/*F1.PRM > tmp
    set pth = `awk NR==1'{print $1}' tmp | awk -F'/' '{for(i=1;i<NF;i++) printf("%s/",$i)}'`
    set f1 = `awk NR==1'{print $1}' tmp | awk -F'/' '{print $NF}'`
    set f2 = `awk NR==2'{print $1}' tmp | awk -F'/' '{print $NF}'`
    set txt1 = `echo $pth":"$f1":"$f2`
  endif
 
  ls $dir/F2/stamps/$line/*F2.PRM > tmp 
  set pth = `awk NR==1'{print $1}' tmp | awk -F'/' '{for(i=1;i<NF;i++) printf("%s/",$i)}'`
  set f1 = `awk NR==1'{print $1}' tmp | awk -F'/' '{print $NF}'`
  set f2 = `awk NR==2'{print $1}' tmp | awk -F'/' '{print $NF}'`
  set txt2 = `echo $pth":"$f1":"$f2`

  if ($mode == 0 || $mode == 2) then
    ls $dir/F3/stamps/$line/*F3.PRM > tmp 
    set pth = `awk NR==1'{print $1}' tmp | awk -F'/' '{for(i=1;i<NF;i++) printf("%s/",$i)}'`
    set f1 = `awk NR==1'{print $1}' tmp | awk -F'/' '{print $NF}'`
    set f2 = `awk NR==2'{print $1}' tmp | awk -F'/' '{print $NF}'`
    set txt3 = `echo $pth":"$f1":"$f2`
  endif
 
  if ($mode == 0) then
    echo $txt1","$txt2","$txt3
  endif
  if ($mode == 1) then
    echo $txt1","$txt2
  endif
  if ($mode == 2) then
    echo $txt2","$txt3
  endif
  if ("$mode" == "None" && "$F" == "F2") then
    echo $txt2
  endif
  if ("$mode" == "None" && "$F" == "F1") then
    ls $dir/F1/stamps/$line/*F1.PRM > tmp
    set pth = `awk NR==1'{print $1}' tmp | awk -F'/' '{for(i=1;i<NF;i++) printf("%s/",$i)}'`
    set f1 = `awk NR==1'{print $1}' tmp | awk -F'/' '{print $NF}'`
    set f2 = `awk NR==2'{print $1}' tmp | awk -F'/' '{print $NF}'`
    set txt1 = `echo $pth":"$f1":"$f2`
    echo $txt1
  endif
  if ("$mode" == "None" && "$F" == "F3") then
    ls $dir/F3/stamps/$line/*F3.PRM > tmp
    set pth = `awk NR==1'{print $1}' tmp | awk -F'/' '{for(i=1;i<NF;i++) printf("%s/",$i)}'`
    set f1 = `awk NR==1'{print $1}' tmp | awk -F'/' '{print $NF}'`
    set f2 = `awk NR==2'{print $1}' tmp | awk -F'/' '{print $NF}'`
    set txt3 = `echo $pth":"$f1":"$f2`
    echo $txt3
  endif

end

