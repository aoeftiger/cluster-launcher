# cluster-launcher
Launcher scripts for parallel jobs to be run on a cluster environment such as LSF, HTCondor, SLURM etc.

`Launcher.py` can be adapted to include the submission to these systems. 
By default, the launcher emulates a cluster by sequentially launching the tasks in a `tmux` terminal-multiplexer session.

## How it works

`main.py` contains the generic job description (e.g. simulation set-up and run definition).
This file needs to be adapted to the corresponding simulation case.

`Launcher.py` generates the task files for each of the input configuration cases.
Each configuration case has a unique task ID.
The corresponding input parameters are stored in `task.<JOB-ID>.py` files.
They are located in a newly created *working directory* under the `WRKDIRBASE` path,
named by the variable combination `WRKDIR/SRCDIR+SUFFIX/`.

Each of the `task.###.py` files then calls the `main.py` script with its `run` function,
providing a corresponding particular set of keyword arguments passing the specific input parameters.

In the job submission to the cluster within `Launcher.py`, the job arrays on the cluster
would launch a job with its corresponding task via the task script, each identifiable by the JOB-ID.

All output and error logs are stored under the *working directory*`/Output/`.

The resulting data from the simulation should be written to the created directory under *working directory*`/Data/`.
This should be configured within the `main.py` script (in the function `store.py`).
During execution of `main.py` on the cluster node, the `Data` directory is conveniently stored
in the global variable `outputpath`, while the current JOB-ID is accessible via the global variable `it`.
One can/should make use of `outputpath` and `it` to create unique names for the output files to be created
by each simulation instance.

In the default case, the name of the `tmux` session will be printed out to the terminal.
The session with all individual jobs can be accessed via `tmux a -t <session-name>`.
