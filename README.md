# Daemon Control (daemonctl)

**Description**:  A python framework and tools to manage small applications

  - **Technology stack**: Plain python
  - **Status**:  Running in production [CHANGELOG](CHANGELOG.md).
  - When administrating alot of applications on different servers or developing alot of small services it's often desireable to keep the inhouse services seperate from system services.


## Dependencies

 - python >= 2.6
 - setprocname: to have cleaner names in ps for the daemons (not required)

## Installation

sudo ./setup.py install

## Configuration

configfile in /usr/local/etc/daemonctl.conf (or where DAEMONCTL is installed)

Configformat:
```
logpath = logdir # Path to directory where log files will be placed
pidpath = piddir # Path to directory where pid files will be placed
modules {
 module1 {
  name = modulename # name of daemon in status and other daemonctl commands (should include %(id)s if type=dynamic)
  type = moduletype # single or dynamic
  path = modulepath # Path to where the files are (will do chdir to here before running command)
  execcmd = commandline # Command to run (will be prefixed with path)
  listcmd = listcommand # Command that returns id:s for type=dynamic, one id per row
  logpath = logdir # Can override the global logpath
  pidpath = piddir # Can override the global pidpath
  runas = username # Run daemon as this user
 }
}
```

## Usage

```
Usage: daemonctl [options] <command> [daemon]
     Commands:
        start        Start daemons
        stop         Stop daemons ("-f" to force)
        restart      Restart daemons (stop+start)
        forcestop    Force daemons to stop (kill -9)
        status       Get daemon status
        enable       Enable an application
        disable      Disable an application
        hide         Hide daemon from status
        show         Unhide daemon from status
        tail         Tail a daemon log
        less         Less a daemon log
        csvstatus    Get daemon status in csv format

    Options:
      -h, --help            show this help message and exit
      -f, --force
      -r, --regex           Select daemons using regexp only
      -g, --glob            Select daemons using globbing only
      -e, --exact           Select daemons using exact match only
      -c CONFIG, --config=CONFIG
      -a, --showall         Show hidden
      -v, --version         Print version
```
## Known issues

The code is very messy

## Getting help

If you have questions, concerns, bug reports, etc, please file an issue in this repository's Issue Tracker.

## Getting involved

Feature request with documentation, fixes, new features and general beutification is welcome.

----

## Open source licensing info

GNU General Public License version 3
[LICENSE](LICENSE)

----

