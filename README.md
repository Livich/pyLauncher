# PyLauncher

PyLauncher is a tool to control multiple simultaneously running applications. Created for mining purposes.
PyLauncher allows:

* Run executables, _obviously_;
* Switch working directories for each app;
* Re-launch each application by:
    * timeout;
    * port binding failure;
    * HTTP unavailability.
    
## Installation

PyLauncher is pure Python 3 software, so you'll need:
* Python 3
* Some modules, run: `pip install atexit requests psutil schedule argparse`

## Usage

CLI interface:
`launcher.py -p <profile filename> -v[v[v[v[v]]]]`
* `-p` profile file name. Required.
* `-v[v[v[v[v]]]]` verbosity level from 1`v` to 4 `v`'s.  Also you can call it like `-v 1`.

### Profile file

Create `json` file like (this one is for Windows):

```json
[
	{
		"app": "start eth-proxy.exe",
		"cwd": "C:/Users/miner/Desktop/exp/eth-proxy/",
		"timeout": "3600",
		"startup_time": "30",
		"http": "http://127.0.0.1:8080/rig1"
	},
	{
		"delay": "10",
		"app": "start ethminer.exe --farm-recheck 200 -G -F http://127.0.0.1:8080/rig1",
		"cwd": "C:/Users/miner/Desktop/exp/",
		"timeout": "3590",
		"bind": "127.0.0.1:8080"
	}
]
```

There are two application entries. Each entry may have such attributes:
* `app` application executable;
* `cwd` application working dir;
* `timeout` relaunch timeout;
* `startup_time` delay before startup tests:
    * `http` to check HTTP response code (will relaunch application if HTTP code is not 200)
    * `bind` to check port availability (will relaunch application if port free)