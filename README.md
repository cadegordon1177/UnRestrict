# UnRestrict

Turns off the iOS background daemons you never asked for — Screen Time, usage
tracking, crash logging, Game Center, location, all of it. Plug in your iPhone,
flip off what you want, hit inject. It reboots and they're gone.

macOS only.

## Download

Grab the latest `.dmg` from [Releases](../../releases) and drag it into
Applications.

If it won't open ("damaged" or "unidentified developer"), that's just
Gatekeeper. It isn't signed, so clear the quarantine flag and it'll open fine:

```bash
xattr -cr /Applications/UnRestrict.app
```

## How it works

No jailbreak, nothing permanent. It builds a fake backup and lets iOS restore
it, slipping a few files into system spots iOS normally won't let you touch —
the sparserestore trick, a path-traversal in the backup restore. One reboot and
it's done. Changed your mind? Hit Restore and it puts the daemons back.

Works on iOS 17 through 26. Turn Find My off first or it won't run.

## Heads up

- Killing Screen Time wipes its data. The old limits don't come back, but you
  can switch the service back on with Restore.
- Don't run this on a managed school or work device.
