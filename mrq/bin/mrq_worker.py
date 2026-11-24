#!/usr/bin/env python
import os
from future.builtins import str
import sys

# This must be done asap in the worker
from mrq.gevent_setup import patch_unless_job_process, start_job_processes_without_gevent
patch_unless_job_process()

import tempfile
import signal
import psutil
import argparse
import shlex

sys.path.insert(0, os.getcwd())

from mrq import config
from mrq.utils import load_class_by_path
from mrq.context import set_current_config, set_logger_config


def main():

    start_job_processes_without_gevent()

    parser = argparse.ArgumentParser(description='Start a MRQ worker')

    cfg = config.get_config(parser=parser, config_type="worker", sources=("file", "env", "args"))

    set_current_config(cfg)
    set_logger_config()

    # If we are launching with a --processes option and without MRQ_IS_SUBPROCESS, we are a manager process
    if cfg["processes"] > 0 and not os.environ.get("MRQ_IS_SUBPROCESS"):

        from mrq.supervisor import Supervisor

        command = " ".join(map(shlex.quote, sys.argv))
        w = Supervisor(command, numprocs=cfg["processes"])
        w.work()
        sys.exit(w.exitcode)

    # If not, start an actual worker
    else:

        worker_class = load_class_by_path(cfg["worker_class"])
        w = worker_class()
        w.work()
        sys.exit(w.exitcode)

if __name__ == "__main__":
    main()
