---
name: ship
description: Commit and push the current change, then deploy it to the Raspberry Pi if the Pi is reachable on the network. Use when the user runs /ship or asks to ship, deploy, or sync the current change to the device.
---

# ship

Push the working tree to GitHub, then, only if the Pi answers on the network, pull and
restart it there. Never blocks waiting for a Pi that is off. A short timeout decides
that and the skill moves on.

Device: `admin@raspberrypi.local` (fall back to the last known IP, `192.168.28.243`, only
if the hostname fails to resolve or connect). SSH uses the key already installed on this
Mac. Never prompt for or hardcode the Pi's password, and never write it into this file
or any command.

## 1. Git: commit and push

1. `git status --short`. If there are staged, unstaged, or untracked changes:
   - `git add -A`
   - Commit with a short, specific summary of what changed (6-7 words, like a changelog
     line, not "update"). Follow this conversation's own attribution instructions for the
     commit message trailer, when one is present.
2. Compare against the remote (`git rev-list --count origin/<branch>..HEAD` after a
   `git fetch -q`, or just attempt the push). If there is nothing to commit and nothing
   unpushed, say so and skip straight to step 2. A device sync can still be worth doing
   if the last push never made it there.
3. `git push`. If it fails (e.g. diverged from origin), stop and report the error. Do
   not force-push.

## 2. Check whether the Pi is on

Use a short, non-interactive SSH probe so an offline Pi is detected in a few seconds,
not a hang:

```
ssh -o BatchMode=yes -o ConnectTimeout=4 -o ConnectionAttempts=1 admin@raspberrypi.local 'true'
```

- Success (exit 0): the Pi is reachable, continue to step 3.
- Failure: report that the change was pushed to git but the Pi is offline (or
  unreachable), so nothing was deployed. Stop here. Do not try the fallback IP unless the
  hostname attempt failed to resolve at all (name lookup error, not a timeout/refusal).

## 3. Deploy on the Pi

Run as one SSH command (sudo is passwordless for this user, no prompt occurs):

```
ssh admin@raspberrypi.local '
  set -e
  cd ~/W/pi
  git pull --ff-only
  ~/rfid_env/bin/pip install -q -r requirements-pi.txt
  sudo systemctl restart pi-rfid
  sleep 2
  systemctl is-active pi-rfid
  curl -s -m 5 localhost:8080/api/state
'
```

Notes on this step:
- `git pull --ff-only` refuses instead of merging or clobbering if the Pi's tree has
  diverged (it shouldn't, since `data/` and `music/*` are gitignored there). If it fails,
  report the exact git error and stop. Do not force, reset, or clean anything on the Pi.
- The venv path (`~/rfid_env`) and service name (`pi-rfid`) come from `pi-rfid.service`'s
  `ExecStart`/`WorkingDirectory`. Re-check that file if either ever changes.
- After the restart, confirm `systemctl is-active` prints `active` and the `curl` to
  `/api/state` returns JSON (not empty/error) before declaring success.

## 4. Report

One short summary: what was committed (if anything) and pushed, whether the Pi was on,
and if deployed, that the service restarted and the dashboard is responding. If the Pi
was off, say so plainly. That is a normal outcome, not a failure. The user runs `/ship`
again once it's powered on.
