#!/usr/bin/python
# -*- coding:Utf-8 -*-
#
# (c) 2014, Xavier Le Vaillant <xlevaillant@serviware.com>
#           Serviware / BULL group, France
#           January, 13 2016
#
# Licensed under the terms of the GNU GPL License version 2
#
# ------------------------------------------------------------
#
# History :
#
# 20170515 - TC : invert sacct / scontrol set attributes order to give priority to sacct values (getinfo).
#                 Sometimes, scontrol crushes sacct with incorrects values (eg: nodelist).
#
# 20170810 - TC : add ArchiveLocation parameter
#
'''
ja : JobAccounting
  This script print information about a SLURM job.

 Method:
   1) Get  info from sacct              (online)
   2) Read info from SHOW_SCONTROL      (produced by logJobInfo script during epilog)
   3) Read info from SHOW_OOMKILLER     (procuded by logJobInfo script during epilog)

@author:     Xavier Le Vaillant
@contact:    xlevaillant@serviware.com
@deffield    updated: 2016-01-13
'''

import os
import sys
import datetime, time
import subprocess
import argparse


# SLURM commands
SLURM_TIMEOUT="/usr/bin/timeout 5"
SLURM_BIN_SACCT="/usr/bin/sacct";
SLURM_SACCT_SORT_FIELD="59";
SLURM_BIN_SCONTROL="/usr/bin/scontrol";
# Other commands
SHOW_SCONTROL="/opt/softs/adm/slurm/bin/showJobInfo -c scontrol -j";
SHOW_OOMKILLER="/opt/softs/adm/slurm/bin/showJobInfo -c oom_killer -j"
SHOW_ARCHIVE_LOCATION="/opt/softs/adm/slurm/bin/showJobInfo -c archive_location -j"

# Label
TITLE="BULL - METEO-FRANCE";
NOT_AVAIL="*** Not available ***";

#------------------------
# slurm class
#------------------------
class slurm:

    def __init__(self,jobid=-1, debug=0, args=argparse.ArgumentParser()):
        #
        # --- SACCT ---
        #
        # default_value
        self.AllocCPUS        = "AllocCPUS";
        self.Account          = "Account";
        self.AssocID          = "AssocID";
        self.AveCPU           = "AveCPU";
        self.AveCPUFreq       = "AveCPUFreq";
        self.AveDiskRead      = "AveDiskRead";
        self.AveDiskWrite     = "AveDiskWrite";
        self.AvePages         = "AvePages";
        self.AveRSS           = "AveRSS";
        self.AveVMSize        = "AveVMSize";
        self.BlockID          = "BlockID";
        self.Cluster          = "Cluster";
        self.Comment          = "Comment";
        self.ConsumedEnergy   = "ConsumedEnergy";
        self.CPUTime          = "CPUTime";
        self.CPUTimeRAW       = "CPUTimeRAW";
        self.DerivedExitCode  = "DerivedExitCode";
        self.Elapsed          = "Elapsed";
        self.Eligible         = "Eligible";
        self.End              = "End";
        self.ExitCode         = "Exit";
        self.GID              = "GID";
        self.Group            = "Group";
        self.JobID            = "JobID";
        self.JobName          = "JobName";
        self.Layout           = "Layout";
        self.MaxDiskRead      = "MaxDiskRead";
        self.MaxDiskReadNode  = "MaxDiskReadNode";
        self.MaxDiskReadTask  = "MaxDiskReadTask";
        self.MaxDiskWrite     = "MaxDiskWrite";
        self.MaxDiskWriteNode = "MaxDiskWriteNode";
        self.MaxDiskWriteTask = "MaxDiskWriteTask";
        self.MaxPages         = "MaxPages";
        self.MaxPagesNode     = "MaxPagesNode";
        self.MaxPagesTask     = "MaxPagesTask";
        self.MaxRSS           = "MaxRSS";
        self.MaxRSSNode       = "MaxRSSNode";
        self.MaxRSSTask       = "MaxRSSTask";
        self.MaxVMSize        = "MaxVMSize";
        self.MaxVMSizeNode    = "MaxVMSizeNode";
        self.MaxVMSizeTask    = "MaxVMSizeTask";
        self.MinCPU           = "MinCPU";
        self.MinCPUNode       = "MinCPUNode";
        self.MinCPUTask       = "MinCPUTask";
        self.NCPUS            = "NCPUS";
        self.NNodes           = "NNodes";
        self.NodeList         = "NodeList";
        self.NTasks           = "NTasks";
        self.Priority         = "Priority";
        self.Partition        = "Partition";
        self.QOS              = "QOS";
        self.QOSRAW           = "QOSRAW";
        self.ReqCPUFreq       = "ReqCPUFreq";
        self.ReqCPUs          = "ReqCPUs";
        self.ReqMem           = "ReqMem";
        self.Start            = "Start";
        self.State            = "State";
        self.Submit           = "Submit";
        self.Suspended        = "Suspended";
        self.SystemCPU        = "SystemCPU";
        self.Timelimit        = "Timelimit";
        self.TotalCPU         = "TotalCPU";
        self.UID              = "UID";
        self.User             = "User";
        self.UserCPU          = "UserCPU";
        self.WCKey            = "WCKey";
        self.WCKeyID          = "WCKeyID";
        self.sacct_Format     = "JobID,AllocCPUS,Account,AssocID,AveCPU,AveCPUFreq,AveDiskRead,AveDiskWrite,AvePages,AveRSS,AveVMSize,BlockID,Cluster,Comment,ConsumedEnergy,CPUTime,CPUTimeRAW,DerivedExitCode,Elapsed,Eligible,End,ExitCode,GID,Group,JobName,Layout,MaxDiskRead,MaxDiskReadNode,MaxDiskReadTask,MaxDiskWrite,MaxDiskWriteNode,MaxDiskWriteTask,MaxPages,MaxPagesNode,MaxPagesTask,MaxRSS,MaxRSSNode,MaxRSSTask,MaxVMSize,MaxVMSizeNode,MaxVMSizeTask,MinCPU,MinCPUNode,MinCPUTask,NCPUS,NNodes,NodeList,NTasks,Priority,Partition,QOS,QOSRAW,ReqCPUFreq,ReqCPUs,ReqMem,Start,State,Submit,Suspended,SystemCPU,Timelimit,TotalCPU,UID,User,UserCPU,WCKey,WCKeyID"
        self.sacct_Fields     = self.sacct_Format.split(',');
        #
        # --- SCONTROL ---
        #
        #self.Account          = "Account";     # already in sacct
        self.BatchFlag        = "BatchFlag";
        self.BatchHost        = "BatchHost";
        self.Command          = "Command";
        self.Contiguous       = "Contiguous";
        self.CPUsTask         = "CPUsTask";
        self.Dependency       = "Dependency";
        self.EligibleTime     = "EligibleTime";
        self.ExcNodeList      = "ExcNodeList";
        #self.ExitCode         = "ExitCode";    # already in sacct
        self.Features         = "Features";
        self.Gres             = "Gres";
        self.GroupId          = "GroupId";
        self.JobState         = "JobState";
        self.Licences         = "Licences";
        self.MinCPUsNode      = "MinCPUsNode";
        self.MinMemoryNode    = "MinMemoryNode";
        self.MinTmpDiskNode   = "MinTmpDiskNode";
        self.Network          = "Network";
        #self.NodeList         = "NodeList";    # already in sacct
        self.NumCPUs          = "NumCPUs";
        self.NumNodes         = "NumNodes";
        #self.Partition        = "Partition";   # already in sacct
        self.PreemptTime      = "PreemptTime";
        #self.Priority         = "Priority";    # already in sacct
        #self.QOS              = "QOS";         # already in sacct
        self.Reason           = "Reason";
        self.ReqNodeList      = "ReqNodeList";
        self.ReqSCT           = "ReqS:C:T";
        self.Requeue          = "Requeue";
        self.Reservation      = "Reservation";
        self.Restarts         = "Restarts"
        self.RunTime          = "RunTime";
        self.SecsPreSuspend   = "SecsPreSuspend";
        self.Shared           = "Shared";
        self.StdErr           = "StdErr";
        self.StdIn            = "StdIn";
        self.StdOut           = "StdOut";
        self.SubmitTime       = "SubmitTime";
        self.SuspendTime      = "SuspendTime";
        self.TimeLimit        = "TimeLimit";
        self.TimeMin          = "TimeMin";
        self.UserId           = "UserId";
        self.WorkDir          = "WorkDir";
        self.scontrol_Format  = "Account,BatchFlag,BatchHost,Command,Contiguous,CPUsTask,Dependency,EligibleTime,ExcNodeList,ExitCode,Features,Gres,GroupId,JobState,Licences,MinCPUsNode,MinMemoryNode,MinTmpDiskNode,Network,NodeList,NumCPUs,NumNodes,Partition,PreemptTime,Priority,QOS,Reason,ReqNodeList,ReqSCT,Requeue,Reservation,Restarts,RunTime,SecsPreSuspend,Shared,StdErr,StdIn,StdOut,SubmitTime,SuspendTime,TimeLimit,TimeMin,UserId,WorkDir";
        self.scontrol_Fields   = self.scontrol_Format.split(',');
        #
        # --- ADDONS ---
        #
        self.Data             = list();         # data from sacct
        self.Data2            = list();         # data from scontrol
        self.Steps            = list();
        self.Nsteps           = 0;
        self.StepIDs          = list();
        self.StepID           = "";
        self.Printinfo        = "";
        self.ArchiveLocation  = "";
        #
        # --- OOM_KILLER
        #
        self.oom_exist        = 0;
        #
        # --- INPUT ---
        #
        # input value
        self.JobID            = jobid;
        self.debug            = debug;
        self.args             = args;

    def checkargs(self):
        if self.args.debug:
            self.debug = 1;
        if self.args.jobid:
            self.JobID = str(self.args.jobid);
            rc = os.system(SLURM_TIMEOUT+" "+SLURM_BIN_SACCT+" -j "+self.JobID+" >& /dev/null");
            if rc != 0:
                print("["+self.args.progname+"] Error : Humhum... slurmdbd is not responding :(");
                sys.exit(0);
        else:
            try:
                self.JobID=os.environ["SLURM_JOB_ID"];
            except:
                print("["+self.args.progname+"] Error : SLURM_JOB_ID not found in your environment!\nTry '"+self.args.progname+" --help' for more information");
                sys.exit(1);

    def slurm_sacct(self):
        slurm_cmd = SLURM_TIMEOUT+" "+SLURM_BIN_SACCT+" --duplicates --noheader --parsable2 --format={Fields} --jobs={JobID} 2>/dev/null | sort -t'|' -k{isort},{isort} -k1,1".format(Fields=self.sacct_Format, JobID=self.JobID, isort=SLURM_SACCT_SORT_FIELD);
        if self.debug:
            print("[slurm_sacct] slurm_cmd : "+slurm_cmd);
        command = subprocess.Popen(slurm_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT);
        return command;

    def slurm_scontrol(self):
        # slurm scontrol (when job is running)
        slurm_cmd = SLURM_TIMEOUT+" "+SLURM_BIN_SCONTROL+" --all show job "+self.JobID+" 2>/dev/null";
        try:
            command = subprocess.Popen(slurm_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT);
            retcode = command.wait();
        except:
            print("["+self.args.progname+"] Error : Humhum... slurmctld is not responding :(\n");
            retcode = 1;
        # slurm scontrol (when job is NOT running)
        if (retcode > 0):
             slurm_cmd = SHOW_SCONTROL+" "+self.JobID+" 2>/dev/null";
        if self.debug:
            print("[slurm_scontrol] slurm_cmd : "+slurm_cmd);
        # awk command to split field (should be done in python...)
        awk_cmd = " | awk '{for(i=1; i<=NF; i++){ if( match($i,\"=\") != 0 ){ printf(\"\\n%s\",$i); } else { printf(\" %s\",$i); }}} END { print \"\" }' | sed '/^$/d'";
        command = subprocess.Popen(slurm_cmd+awk_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT);
        command.wait();
        return command;

    def slurm_archive_location(self):
        # get the job's logs location
        slurm_cmd = SHOW_ARCHIVE_LOCATION+" "+self.JobID+" 2>/dev/null";
        if self.debug:
            print("[slurm_archive_location] slurm_cmd : "+slurm_cmd);
        command = subprocess.Popen(slurm_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT);
        command.wait();
        return command;

    def slurm_oomkiller_exist(self):
        # get oom info
        slurm_cmd = SHOW_OOMKILLER+" "+self.JobID+" 1>/dev/null 2>&1";
        if self.debug:
            print("[slurm_oomkiller] slurm_cmd : "+slurm_cmd);
        command = subprocess.Popen(slurm_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT);
        rc = command.wait();
        if (rc == 0):
            exist = 1;
        else:
            exist = 0;
        return exist;

    def slurm_oomkiller_print(self):
        # print oom info
        slurm_cmd = SHOW_OOMKILLER+" "+self.JobID+" 2>/dev/null";
        command = subprocess.Popen(slurm_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT);
        for line in command.stdout.readlines():
            print(f"{line.rstrip('\n')}") ;
        return;

    def getdata(self):
        # get data from slurm database : sacct
        command=self.slurm_sacct();
        for line in command.stdout.readlines():
            self.Data.append(line);
        # job content
        if not self.Data:
            print("INFO => no data about job "+self.JobID);
            sys.exit(0);
        # oom_killer info exist
        self.oom_exist = self.slurm_oomkiller_exist();
        # trick to set a numeric value to "Restarts" field.
        if (self.Restarts == NOT_AVAIL):
            self.Restarts = 0;
        # get data from slurm database : scontrol
        command = self.slurm_scontrol();
        for line in command.stdout.readlines():
            self.Data2.append(line);
        # get the log archive location
        command = self.slurm_archive_location();
        for line in command.stdout.readlines():
            if "ArchiveLocation" in line:
                Values = line.strip().split('=');
                self.ArchiveLocation = Values[1];

    def getinfo(self,line=""):
        # get info (from stored data or argument)
        if (line != ""):
           Values=line.strip().split('|');
           self.Values = Values;
        else:
           for line in self.Data:
              Values=line.strip().split('|');
              if (Values[0] == self.JobID):
                 SelectedValues = Values;
           self.Values = SelectedValues;
        if (len(self.JobID.split('.')) > 1):
            self.StepID = self.JobID.split('.')[-1];

        # set attributes from scontrol
        for i in range(0,len(self.scontrol_Fields)):
            for line in self.Data2:
                Values = line.strip().split('=');
                this_Field = Values[0];
                this_Value = Values[1];
                if (this_Field == self.scontrol_Fields[i]):
                    setattr(self, this_Field, this_Value);
            this_Value = getattr(self, self.scontrol_Fields[i]);
            if (this_Value == self.scontrol_Fields[i]):
                setattr(self, self.scontrol_Fields[i], NOT_AVAIL);
        # set attributes from sacct
        for i in range(1,len(self.sacct_Fields)):
            field=self.sacct_Fields[i]
            # trick to reduce "CANCELLED by ..." => "CANCELLED"
            if (field == "State"):
                if ("CANCELLED" in self.Values[i]):
                    self.Values[i] = "CANCELLED";
            setattr(self, field, self.Values[i])
        if self.debug:
            print("[slurm_getinfo] Values :");
            for i in range(0,len(self.sacct_Fields)):
                print(f"[slurm_getinfo] {self.JobID}, {self.sacct_Fields[i]:20s} : {getattr(self,self.sacct_Fields[i])}");
            for i in range(0,len(self.scontrol_Fields)):
                print(f"[slurm_getinfo] {self.JobID}, {self.scontrol_Fields[i]:20s} : {getattr(self,self.scontrol_Fields[i])}")

    def getstepinfo(self):
        # count all steps
        self.Nsteps = 0;
        for line in self.Data:
            Values=line.strip().split('|');
            self.StepIDs.append(Values[0]);
            self.Nsteps = self.Nsteps + 1;
        if self.Nsteps > 0:
            if self.debug:
                print(f"[slurm_getstepinfo] StepIDs ({self.Nsteps}): {self.StepIDs}")
            # get info for each step
            StepID=0
            for line in self.Data:
                if self.debug:
                    print(f"[slurm_getstepinfo] JobID:{self.JobID} --> Step:[ID->{StepID}, JobID->{self.StepIDs[StepID]}]")
                #exec('self.StepID_'+str(StepID)+' = slurm(jobid=self.StepIDs[StepID],debug=self.debug)');
                setattr(self, f"StepID_{StepID}", slurm(jobid=self.StepIDs[StepID], debug=self.debug))

                #exec('self.StepID_'+str(StepID)+'.getinfo(line)');
                getattr(self, f"StepID_{StepID}").getinfo(line)

                #exec('JobStepID = self.StepID_'+str(StepID)+'.StepID');
                JobStepID = getattr(self, f"StepID_{StepID}").StepID

                if (JobStepID == ""):
                    self.MainID = StepID;
                StepID = StepID + 1;

    def printinfo_header(self):
        #Raymond 11/10/2022 : add if statement to prevent error on different formated datetime
        if self.Elapsed.split(',')[0][1] == '-' or self.Elapsed.split(',')[0][2] == '-':
                TEI = time.strptime(self.Elapsed.split(',')[0],'%d-%H:%M:%S')
                TEI_s = float(self.NCPUS) * datetime.timedelta(days=TEI.tm_mday,hours=TEI.tm_hour,minutes=TEI.tm_min,seconds=TEI.tm_sec).total_seconds();
        else:
                TEI = time.strptime(self.Elapsed.split(',')[0],'%H:%M:%S')
                TEI_s = float(self.NCPUS) * datetime.timedelta(hours=TEI.tm_hour,minutes=TEI.tm_min,seconds=TEI.tm_sec).total_seconds();
        #TEI = time.strptime(self.Elapsed.split(',')[0],'%H:%M:%S'
        #TEI_s = float(self.NCPUS) * datetime.timedelta(days=TEI.tm_mday,hours=TEI.tm_hour,minutes=TEI.tm_min,seconds=TEI.tm_sec).total_seconds();
        #Benj 07/11/2016 : replace NNNODE by NCPUS / 2
        TEI_hms = str(datetime.timedelta(seconds=TEI_s));
        #m, s = divmod(TEI_s, 60);
        #h, m = divmod(m, 60);
        #TEI_hms = "%d:%02d:%02d" % (h, m, s);
        self.Printinfo= f"""
#########################################
#        {TITLE:31.31}#
#        Job Accounting                 #
#########################################
Cluster              : {self.Cluster}
JobID                : {self.JobID}
JobName              : {self.JobName}
Account              : {self.Account}
User                 : {self.User}({self.UID}), {self.Group}({self.GID})
Partition            : {self.Partition}
QOS                  : {self.QOS}
Nodelist             : {self.NodeList} ({self.NNodes})
State                : {self.State}  (Exitcode={self.ExitCode}, DerivedExitCode={self.DerivedExitCode}, Restarts={self.Restarts})
Submit date          : {self.Submit}
Start time           : {self.Start}
End time             : {self.End}
Elapsed time         : {self.Elapsed}  (Timelimit={self.Timelimit}, Suspended={self.Suspended})
TEI                  : {self.TEI_hms}
Command              : {self.Command}
StdOut               : {self.StdOut}
StdErr               : {self.StdErr}
Log archive location : {self.ArchiveLocation}

"""

    def printinfo_onestep(self,step):
        self.Printinfo += """   {StepID:7.7s} | {JobName:12.12s} {State:11.11s} {ExitCode:6.6s} {Start:19.19s} {End:19.19s} {Elapsed:9.9s} {TotalCPU:10.10s} {CPUTime:10.10s} {ConsumedEnergy:>14.14} {MaxDiskRead:>11.11s} {MaxDiskWrite:>12.12s} {MaxRSS:>10.10s} {MaxRSSTask:>10.10s} {MaxRSSNode:>10.10s} {NNodes:>6.6s} {NodeList} {Comment}
""".format(StepID=step.StepID, AllocCPUS=step.AllocCPUS, Account=step.Account, AssocID=step.AssocID, AveCPU=step.AveCPU, AveCPUFreq=step.AveCPUFreq, AveDiskRead=step.AveDiskRead, AveDiskWrite=step.AveDiskWrite, AvePages=step.AvePages, AveRSS=step.AveRSS, AveVMSize=step.AveVMSize, BlockID=step.BlockID, Cluster=step.Cluster, Comment=step.Comment, ConsumedEnergy=step.ConsumedEnergy, CPUTime=step.CPUTime, CPUTimeRAW=step.CPUTimeRAW, DerivedExitCode=step.DerivedExitCode, Elapsed=step.Elapsed, Eligible=step.Eligible, End=step.End, ExitCode=step.ExitCode, GID=step.GID, Group=step.Group, JobID=step.JobID, JobName=step.JobName, Layout=step.Layout, MaxDiskRead=step.MaxDiskRead, MaxDiskReadNode=step.MaxDiskReadNode, MaxDiskReadTask=step.MaxDiskReadTask, MaxDiskWrite=step.MaxDiskWrite, MaxDiskWriteNode=step.MaxDiskWriteNode, MaxDiskWriteTask=step.MaxDiskWriteTask, MaxPages=step.MaxPages, MaxPagesNode=step.MaxPagesNode, MaxPagesTask=step.MaxPagesTask, MaxRSS=step.MaxRSS, MaxRSSNode=step.MaxRSSNode, MaxRSSTask=step.MaxRSSTask, MaxVMSize=step.MaxVMSize, MaxVMSizeNode=step.MaxVMSizeNode, MaxVMSizeTask=step.MaxVMSizeTask, MinCPU=step.MinCPU, MinCPUNode=step.MinCPUNode, MinCPUTask=step.MinCPUTask, NCPUS=step.NCPUS, NNodes=step.NNodes, NodeList=step.NodeList, NTasks=step.NTasks, Priority=step.Priority, Partition=step.Partition, QOS=step.QOS, QOSRAW=step.QOSRAW, ReqCPUFreq=step.ReqCPUFreq, ReqCPUs=step.ReqCPUs, ReqMem=step.ReqMem, Start=step.Start, State=step.State, Submit=step.Submit, Suspended=step.Suspended, SystemCPU=step.SystemCPU, Timelimit=step.Timelimit, TotalCPU=step.TotalCPU, UID=step.UID, User=step.User, UserCPU=step.UserCPU, WCKey=step.WCKey, WCKeyID=step.WCKeyID, Restarts=step.Restarts, BatchHost=step.BatchHost, Command=step.Command, WorkDir=step.WorkDir);

    def printinfo_steps(self):
        step = slurm();
        step.StepID = "StepID";
        step.Nsteps= self.Nsteps;
        if (step.Nsteps > 1):
            step.Nsteps = step.Nsteps - 1;
        self.Printinfo += """STEP(s) : {Nsteps}\n--------- \n""".format(Nsteps=step.Nsteps);
        self.printinfo_onestep(step);
        self.Printinfo += """   {sep} \n""".format(sep="-"*220);
        if (self.Nsteps > 0):
            for StepID in range(0,len(self.StepIDs)):
                if (StepID == self.MainID):
                   continue;
                exec('step = self.StepID_'+str(StepID)+';');
                self.printinfo_onestep(step);
        else:
            step = self;
            step.StepID = "";
            self.printinfo_onestep(step);

    def printinfo(self):
        self.printinfo_header();
        self.printinfo_steps();
        print(self.Printinfo);

    def printinfo_oom(self):
        if (self.oom_exist):
            print("WARNING: OOM KILLER detected !\n--------");
            if (self.args.oom):
                self.slurm_oomkiller_print();
            else:
                print("Use option \"-o\" for more details.\n");
            print("");

#------------------------
# Main functions
#------------------------
def isjobarray(args):
        """
        Replace the master job's ID by the job array ID

        Parameters
        ----------
        args : Namespace
                With args.jobid a list of string corresponding to job ID input
                by user.

        Returns
        -------
        args : Namespace
                With args.jobid a list of string with all the job ID
        """

        # Creation of the new args list
        ext_args = list()

        # Using sacct command to get info on jobs
        rc = subprocess.Popen(["/usr/bin/sacct", "--duplicate", "--noheader", "--parsable2", "--format=JobID"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Retrieve all jobs
        list_id = list()
        for line in iter(rc.stdout.readline, ''):
                clean_line = line.strip().split('.')[0]
                list_id.append(clean_line)

        # Checking if job is a job array
        for id in args.jobid:

                child_flag = True
                # checking if id already in ext_args
                if id in ext_args:
                        pass

                # checking if we already have a children job id
                elif "_" in id:
                        ext_args.append(id)
                        pass
                else:
                        # checking if job id has children job id
                        for id_from_list in list_id:
                                if id_from_list.startswith(id + "_") and id_from_list not in ext_args:
                                        if args.replace or args.range:
                                                ext_args.append(id_from_list)
                                                child_flag = False
                                        else:
                                                print(f"Error : Job {id} is parent to a job array, please enter children job ID (ex : {id}_1) or use --replace flag")
                                                sys.exit(1)
                        if child_flag:
                                if id not in ext_args:
                                        ext_args.append(id)


        args.jobid = ext_args
        return args

def remove_id(args):
        """
        If user gives a range of job's ID to print, remove unwanted job's ID from
        args.jobid

        Parameters
        ----------
        args : Namespace
                With args.jobid a list of string corresponding to job ID input by user.

        Returns
        -------
        args : Namespace
                With args.jobid a list of string with corrected job's ID.
        """

        # Create a list which we will remove id
        corrected_list = args.jobid[:]
        for id in args.jobid:

                # check if the id is a child id
                if "_" in id:

                        # Get the parent id to generate all accepted children id
                        parent_id = id.split("_")[0]
                        accepted_id = [parent_id + "_" + str(index) for index in args.range]

                        # remove child id not wanted by user
                        if not id in accepted_id:
                                corrected_list.remove(id)

        args.jobid = corrected_list
        return args

def _get_range(args):
        """
        From user input, return the range of job's ID

        Parameters
        ----------
        args : Namespace

        Returns
        -------
        List
                Range of the requested job's ID.

        """
        # Delete [] from user input
        str_r = args.range.strip("[]")

        # Get start and end of the range, and convert them into integer
        start, end = str_r.split("-")
        start, end = int(start), int(end)

        return list(range(start, end + 1))



def getargs(argv):
        """
        Create Python object Namespace that contain all the argument to get
        get jobs information from slurm.

        Parameters
        ----------
        argv : list of string
            Input from user.

        Returns
        -------
        args : Namespace.

        """
        parser = argparse.ArgumentParser()
        #-- positional parameters
        parser.add_argument('jobid', type=str, nargs='?', help='displays information about the specified job or a list of job');
        #-- optional parameters
        parser.add_argument('-d', '--debug', action="store_true", help='debug mode (developers)');
        parser.add_argument('-o', '--oom', action="store_true", help='displays all information about OOM Killer');
        parser.add_argument('-r', '--replace', action="store_true", help="replace parent jobID by their children job id");
        parser.add_argument('--range', type=str, nargs='?', help="define the range of job array ton print")
        args = parser.parse_args();
        args.progname = os.path.basename(argv[0]);
        # Postprocess
        if args.jobid:

                # Check if the id is correctly given
                try:
                        args.jobid = [int(item) for item in args.jobid.split(',')];
                        args.jobid = list(map(str, args.jobid));
                except:
                        if "_" in args.jobid:
                                args.jobid = [item for item in args.jobid.split(',')];
                                #print(args.jobid);
                                #sys.exit(1)
                        else:
                                print("["+args.progname+"] Error : Wrong input jobid (digits only)!\nTry '"+args.progname+" --help' for more information");
                                sys.exit(1);

                args = isjobarray(args)

                if args.range:
                        args.range = _get_range(args)
                        args = remove_id(args)
        #--
        if not args.jobid:
            try:
                jobid = os.environ["SLURM_JOB_ID"];
                
                # Check if job is a children job from job array
                try:
                    indexid = os.environ["SLURM_ARRAY_TASK_ID"]
                    jobid += "_" + indexid
                except:
                    indexid = ""
                
                args.jobid = list();
                args.jobid.append(jobid);
            except:
                print("["+args.progname+"] Error : variable SLURM_JOB_ID not found in your environment!\nTry '"+args.progname+" --help' for more information");
                sys.exit(1);
        if args.debug:
             print(args); print("");

        return args;


def main(argv):
        # read args
        args=getargs(argv);
        # do the job
        for id in args.jobid:
            args.jobid = id;
            job = slurm(args=args);
            job.checkargs();
            job.getdata();
            job.getinfo();
            job.getstepinfo();
            job.printinfo();
            job.printinfo_oom();

#------------------------
# Main program
#------------------------
if __name__ == "__main__":
        main(sys.argv);