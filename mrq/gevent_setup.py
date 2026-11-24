""" Gevent setup shared by the mrq-worker and mrq-run launchers.

The launchers run on gevent, but processes they start with multiprocessing (for example a task
that runs its job in a child process) run without it: mixing gevent's monkey-patching with
asyncio in those processes can leave the asyncio event loop waiting forever. Those processes are
started with "spawn", so they are fresh interpreters, and they re-import the launcher module;
the environment flag below tells that import to skip the patching.
"""
import os
import sys

# Only os and sys are imported here: this module runs before gevent patches threading and socket.

JOB_PROCESS_ENV = "MRQ_JOB_PROCESS"


def is_job_process():
    return os.environ.get(JOB_PROCESS_ENV) == "1"


def patch_unless_job_process():
    """ Monkey-patches with gevent, except in a process started by start_job_processes_without_gevent() """

    if is_job_process():
        return

    # Needed to make getaddrinfo() work in pymongo on Mac OS X
    # Docs mention it's a better choice for Linux as well.
    if "GEVENT_RESOLVER" not in os.environ and "__pypy__" not in sys.builtin_module_names:
        os.environ["GEVENT_RESOLVER"] = "ares"

    from gevent import monkey

    # subprocess stays unpatched: once gevent's subprocess has run a child, gevent's SIGCHLD
    # handling also reaps the spawned job processes, so multiprocessing never sees them exit.
    monkey.patch_all(subprocess=False)


def start_job_processes_without_gevent():
    """ Makes multiprocessing start fresh, unpatched interpreters for the processes this one starts """

    import multiprocessing

    multiprocessing.set_start_method("spawn", force=True)
    os.environ[JOB_PROCESS_ENV] = "1"
