#!/opt/softs/anaconda3/envs/Py37nomkl/bin/python

import os
import sys
import subprocess
import pandas as pd
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
NOT_AVAIL="*** Not available ***"




class Job:

    def __init__(self, jobid=None):
        
        self.JobID = jobid
        self.Cluster = ""
        self.JobName = ""
        self.Account= ""
        self.User = ""
        self.UID = ""
        self.Group = ""
        self.GID = ""
        self.Partition = ""
        self.QOS = ""
        self.Nodelist = ""
        self.NNodes = ""
        self.State = ""
        self.ExitCode = ""
        self.DerivedExitCode = ""
        self.Submit = ""
        self.Start = ""
        self.End = ""
        self.Elapsed = ""
        self.Timelimit = ""
        self.Command = ""
        self.StdOut = ""
        self.StdErr = ""
        self.ArchiveLocation = ""
        self.Nsteps = 0
        self.StepIDs = []
        self.TotalCPU = ""
        self.CPUTime = ""
        self.ConsumedEnergyRaw = ""
        self.MaxDiskRead = ""
        self.MaxDiskWrite = ""
        self.MaxRSS = ""
        self.MaxRSSTask = ""
        self.MaxRSSNode = ""

        self.ishetjob = self._check_hetjob()
        self._get_data_from_sacct()


    def _check_hetjob(self):
        """check if job ID refers to heterogenous job"""
        rc = subprocess.Popen(["/usr/bin/sacct", "-j", self.JobID, "--duplicate", "--noheader", "--parsable2", "--format=JobID"], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                universal_newlines=True)
        hetjob = False
        for line in iter(rc.stdout.readline, ""):
            jobid = line.strip().split(".")[0]
            if "+" in jobid:
                hetjob = True
        return hetjob


    def _run_cmd(self, cmd):
        """
        Run shell command and return its output as text

        Parameters
        ----------
        cmd : List
                Contains the command in string form separated by a coma

        Return
        ------
        String
                
        """

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] Command failed: {' '.join(cmd)}\n{e.stderr.strip()}")
            return None

    def _get_data_from_sacct(self):
        """
        """

        fields = ["Cluster",
                "JobName",
                "Account",
                "User",
                "Group",
                "Partition",
                "QOS",
                "NNodes",
                "Nodelist",
                "State",
                "ExitCode",
                "Submit",
                "Start",
                "End",
                "Elapsed",
                "Timelimit",
                "TotalCPU",
                "CPUTime",
                "ConsumedEnergyRaw",
                "MaxDiskRead",
                "MaxDiskWrite",
                "MaxRSS",
        ]
        fmt = ",".join(fields)
        # cmd = ["sacct", "-j", self.JobID, "--noheader", "--parsable2", "-o", f"--format={fmt}"]
        cmd = ["sacct", "-j", self.JobID, "-X", "--noheader", "--parsable2", f"--format={fmt}"]
        output = self._run_cmd(cmd=cmd)
         
        for idx, field in enumerate(fields):
            
            print(f"{field} : {output.split('|')[idx]}")

# ------------------------------------------------------------------------------------


def _recover_JobID(self):

    try:
        jobid = os.environ["SLURM_JOB_ID"]
    except:
        print("Error : variable SLURM_JOB_ID not found in your environment!")
        sys.exit(1)

    return jobid


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
    ext_args = []

    # Using sacct command to get info on jobs
    rc = subprocess.Popen(["/usr/bin/sacct", "--duplicate", "--noheader", "--parsable2", "--format=JobID"], 
                            stdout=subprocess.PIPE, 
                            stderr=subprocess.PIPE, 
                            universal_newlines=True)
    # Retrieve all jobs
    list_id = []
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
    parser = argparse.ArgumentParser()
    #-- positional parameters
    parser.add_argument('jobid', type=str, nargs='?', help='displays information about the specified job or a list of job')
    #-- optional parameters
    parser.add_argument('-r', '--replace', action="store_true", help="replace parent jobID by their children job id")
    parser.add_argument('--range', type=str, nargs='?', help="define the range of job array ton print")
    args = parser.parse_args()
    args.progname = os.path.basename(argv[0])
    # Postprocess
    if args.jobid:
        # Check if the id is correctly given
        try:
            args.jobid = [int(item) for item in args.jobid.split(",")]
            args.jobid = list(map(str, args.jobid))

        except:
            if "_" in args.jobid:
                args.jobid = [item for item in args.split(',')]
            else:
                print("["+args.progname+"] Error : Wrong input jobid (digits only)!\nTry '"+args.progname+" --help' for more information")
                sys.exit(1)
    
        args = isjobarray(args)
    
        if args.range:
            args.range = _get_range(args)
            args = _remove_id(args)

    # If no job ID was given
    else:
        try:
            jobid = os.environ["SLURM_JOB_ID"]

        except:
            print("["+args.progname+"] Error : variable SLURM_JOB_ID not found in your environment!\nTry '"+args.progname+" --help' for more information")
            sys.exit(1)
    
    return args


def main(argv):
    args = getargs(argv)
    for id in args.jobid:
        job = Job(jobid=id)
        # print(job.JobID, job.ishetjob)
        


if __name__ == "__main__":
    
    jobid = "7280800" 
    # job = Job(jobid=jobid)
    main(sys.argv)


