SHSHDump is a Python3 automated script to extract a shsh/ticket from disk1, which contains an illb
which we can extract a good shsh/ticket since it contains a generator, which is needed.

Why use this?

Well, the first benefit is that this script grabs a useable shsh/ticket which will contain a generator.
Since the apticket in /System/Library/Caches/ will only contain a signature and no generator.

# Installation

pip3 install -r requirements.txt

# Usage

./dump.py

--ip (your ip, e.g. 192.168.0.10/localhost)
--port 22 (default ssh port)
--user root
--password (your root password, default is alpine)

# Issues

Seems like using TotallyNotSpyware (Meridian/jailbreakd) doesn't correct codesigning so unfortunately,
if you're using it to jailbreak, using the modified dd will not work as it gets killed each time :(
I haven't tested the doubleH3lix counterpart within the Spyware jailbreak, so it may or may not work, idk.

# After dumping

I have everything kept in a 'hidden' folder called '.tmp'. This folder will contain your dump as well as the extracted shsh/ticket.

Pretty much can just use the command: 'cp -rv .tmp/blob.shsh2 .' to copy it to the main directory.

# Note

Checkra1n will allow dd to copy the contents of /dev/disk1 without any other modifications.

Unc0ver v5.0.1+ relaxes the Sandbox a bit when copying /dev/disk1 with dd, so no modifications are needed
if you're running v5.0.1+.

# Entitlements

The entitlement "com.apple.private.security.disk-device-access" is needed if the Sandbox isn't modified to allow
this process without adding the entitlement. Other than that, nothing else is needed.
