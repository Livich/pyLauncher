import argparse
import json
import os
import subprocess
import schedule
import time
import socket
import atexit
import requests
import psutil


# Installation: pip install atexit requests psutil schedule argparse

class VAction(argparse.Action):
    """Allows users to call application with -v[v[v[v[v]]]] argument"""

    def __call__(self, parser, args, values, option_string=None):
        # print 'values: {v!r}'.format(v=values)
        if values == None:
            values = '1'
        try:
            values = int(values)
        except ValueError:
            values = values.count('v') + 1
        setattr(args, self.dest, values)


parser = argparse.ArgumentParser(description='pyLauncher')

parser.add_argument('-p',
                    '--profile',
                    type=str,
                    help='Profile to work with')

parser.add_argument('-v',
                    nargs='?',
                    default=4,
                    action=VAction,
                    dest='verbose',
                    help="verbosity levels: "
                         "-2    necessary output. "
                         "-1    system messages. "
                         "0     status info. "
                         "1     information. "
                         "2     messages. "
                         "3     extra information. "
                         "4     debug information")

args = parser.parse_args()

pids = []


def verbose(lvl: int, message: str):
    """Logger routine
    Keyword arguments:
        lvl     --  message priority level
        message --  message text
    """
    hdr = {
        -2: "WARN: ",
        -1: "SYS: ",
        0: "STATUS: ",
        1: "INFO: ",
        2: "MSG: ",
        3: "EXTRA: ",
        4: "DBG: "
    }
    if args.verbose >= lvl:
        print("%s%s" % (hdr[lvl], message))


def kill(process: psutil.Popen):
    """Kill process

    Keyword arguments:
    :param process: psutil.Popen instance
    :return: None
    """
    verbose(1, "terminate pid %i and all its children" % process.pid)
    if not process.is_running():
        verbose(1, "pid %i is already gone" % process.pid)
        return
    procToKill = process.children(True)
    for proc in procToKill:
        verbose(4, str(proc))
        if proc.is_running():
            proc.terminate()
        gone, alive = psutil.wait_procs([proc], timeout=3)
        for p in alive:
            p.kill()
            verbose(-2, "kill pid %i" % p.pid)
    try:
        pids.remove(process.pid)
    except:
        pass


def check_bind(addr: str):
    """Bind checker
    Try to bind address:port
    :param addr: str "ip:port"
    :return: in case of binding error returns True, False otherwise
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    addr, port = addr.split(":")
    try:
        s.bind((addr, int(port)))
    except socket.error as e:
        if e.errno == 98:
            return True
    s.close()
    verbose(-2, "network activity check failed")
    return False


def check_http(url: str):
    """HTTP checker
    Try to load URL and check HTTP code
    :param url: str url
    :return: in case of response code 200 returns True, False otherwise
    """
    response = requests.get(url)
    return response.status_code == 200


def on_startup(proc: psutil.Popen, app: dict):
    """Startup task
    Performs startup checks (if needed). The routine will restart the process in case of check failure
    :param proc: psutil.Popen instance
    :param app: profile record
    :return: schedule.CancelJob
    """
    verbose(1, "performing startup checks for %s" % str(app['app']))
    result = True
    if 'bind' in app:
        result = check_bind(app['bind'])
    if 'http' in app:
        result = check_http(app['http'])

    if not result:
        verbose(-2, "process %s restart" % str(app['app']))
        schedule.clear(proc.pid)
        kill(proc)
        launch(app)
    verbose(1, "startup checks OK for %s" % str(app['app']))
    return schedule.CancelJob


def on_timeout(proc: psutil.Popen, app: dict):
    """Interrupt application task
    Kill application and re-launch task
    :param proc: psutil.Popen
    :param app: profile record
    :return: schedule.CancelJob
    """
    verbose(1, "process %s timeout" % str(app['app']))
    kill(proc)
    launch(app)
    return schedule.CancelJob


def launch(app: dict):
    """Launch task
    Create psutil.Popen instance and schedule on_startup and on_timeout activities
    :param app: profile record
    :return: None
    """
    verbose(1, "launching %s" % str(app['app']))

    if 'cwd' in app:
        cwd = app['cwd']
    else:
        cwd = None

    if 'delay' in app:
        time.sleep(float(app['delay']))
        delay = float(app['delay'])
    else:
        delay = 0

    proc = psutil.Popen(app['app'], shell=True, cwd=cwd, creationflags=subprocess.CREATE_NEW_CONSOLE)
    pids.append(proc.pid)
    verbose(2, "process got pid %i" % proc.pid)
    if 'startup_time' in app:
        schedule.every(int(app['startup_time'])).seconds.do(on_startup, proc, app).tag(proc.pid)
    if 'timeout' in app:
        schedule.every(int(app['timeout']) - delay).seconds.do(on_timeout, proc, app).tag(proc.pid)


def exit_handler():
    """Kill all active tasks
    :return: None
    """
    for pid in pids:
        verbose(-2, "kill pid %i and children" % pid)
        try:
            procToKill = psutil.Process(pid).children(True)
            for proc in procToKill:
                verbose(4, str(proc))
                if proc.is_running():
                    proc.kill()
        except:
            verbose(-2, "pid %i gone" % pid)


# ---------------------

if not os.path.isfile(args.profile):
    raise FileNotFoundError("%s profile configuration is not found" % args.profile)

atexit.register(exit_handler)

profile = json.load(open(args.profile))
for item in profile:
    verbose(4, str(item))
    launch(item)

while True:
    schedule.run_pending()
    time.sleep(1)
