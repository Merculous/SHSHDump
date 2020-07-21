#!/usr/bin/env python3

import argparse
import os
import platform
import shutil
import subprocess
import sys
import time
from zipfile import ZipFile
from urllib.request import urlretrieve

try:
    import paramiko
except ImportError:
    raise

host_os = platform.system()


def getimg4tool():
    cwd = os.getcwd()

    if host_os == 'Linux':
        print('Ensuring needed dependencies are installed!')

        subprocess.run(
            ('sudo',
             'apt',
             'install',
             'automake',
             'g++',
             'openssl',
             'pkg-config',
             'libtool',
             'python-dev',
             'cmake'))

    elif host_os == 'Darwin':
        pass

    if not os.path.exists('.tmp/libplist'):
        subprocess.run(
            ('git',
             'clone',
             'https://github.com/libimobiledevice/libplist',
             '.tmp/libplist'),
            stdout=subprocess.DEVNULL)

        os.chdir('.tmp/libplist')

        subprocess.run(
            ('./autogen.sh;',
             'make;',
             'sudo',
             'make',
             'install'),
            stdout=subprocess.DEVNULL,
            shell=True)

        os.chdir(cwd)

    if not os.path.exists('.tmp/libgeneral'):
        subprocess.run(
            ('git',
             'clone',
             'https://github.com/tihmstar/libgeneral',
             '.tmp/libgeneral'),
            stdout=subprocess.DEVNULL)

        os.chdir('.tmp/libgeneral')

        subprocess.run(
            ('./autogen.sh;',
             'make;',
             'sudo',
             'make',
             'install'),
            stdout=subprocess.DEVNULL,
            shell=True)

        os.chdir(cwd)

    if not os.path.exists('.tmp/lzfse'):
        subprocess.run(
            ('git',
             'clone',
             'https://github.com/lzfse/lzfse',
             '.tmp/lzfse'),
            stdout=subprocess.DEVNULL)

        os.chdir('.tmp/lzfse')

        if not os.path.exists('build'):
            os.mkdir('build')

        os.chdir('build')

        subprocess.run(('cmake', '..'), stdout=subprocess.DEVNULL)

        os.chdir(cwd)

    if not os.path.exists('.tmp/img4tool'):
        subprocess.run(
            ('git',
             'clone',
             '--recursive',
             'https://github.com/tihmstar/img4tool',
             '.tmp/img4tool'),
            stdout=subprocess.DEVNULL)

        os.chdir('.tmp/img4tool')

        subprocess.run(
            ('./autogen.sh;',
             'make;',
             'sudo',
             'make',
             'install'),
            stdout=subprocess.DEVNULL,
            shell=True)

        os.chdir(cwd)

    if host_os == 'Linux':
        subprocess.run(('sudo', 'ldconfig'))

    try:
        subprocess.run(('which', 'img4tool'), stdout=subprocess.DEVNULL)
    except FileNotFoundError:
        print('Seems like img4tool was not compiled!')
        raise


def getldid():
    url = 'https://github.com/xerub/ldid/releases/download/42/ldid.zip'
    filename = os.path.basename(url)
    path = '.tmp/{}'.format(filename)
    ldid_path = '.tmp/ldid'

    if not os.path.exists('.tmp'):
        os.mkdir('.tmp')

    if not os.path.exists(path):
        print('Downloading ldid!')
        urlretrieve(url, path)

    if not os.path.exists(ldid_path):
        with ZipFile(path, 'r') as f:
            if host_os == 'Darwin':
                print('Extracting MacOS ldid...')
                f.extract('ldid', '.tmp')
                os.chmod(ldid_path, 0o755)
            elif host_os == 'Linux':
                with f.open('linux64/ldid') as yeet, open(ldid_path, 'wb') as yort:
                    print('Extracting Linux ldid...')
                    shutil.copyfileobj(yeet, yort)
                    os.chmod(ldid_path, 0o755)


def dump(host, port, user, password):
    ldid_path = '.tmp/ldid'
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(
            host,
            port=port,
            username=user,
            password=password,
            look_for_keys=False,
            allow_agent=False)
    except ConnectionError:
        raise
    else:
        bad_string = b"dd: failed to open '/dev/disk1': Operation not permitted\n"
        shsh_dump_path = '/tmp/shsh_dump.bin'

        ssh.invoke_shell()
        sftp_client = ssh.open_sftp()

        dd_in, dd_out, dd_err = ssh.exec_command(
            'dd if=/dev/disk1 of={}'.format(shsh_dump_path))

        if dd_err.read() == bad_string:
            print('dd failed to dump, applying entitlements!')

            # NOTE This is very important, so, seems like dropbear doesn't work.
            # This means that we absolutely need something that'll work with
            # paramiko. Thankfully, having OpenSSH installed fixes this issue.

            print('Downloading dd!')
            sftp_client.get('/bin/dd', '.tmp/dd')

            print('Applying entitlements from ent.plist to dd!')
            subprocess.run((ldid_path, '-Sent.plist', '.tmp/dd'))

            print('Uploading modified dd!')
            sftp_client.put('.tmp/dd', '/bin/dd-dump')

            ssh.exec_command('chmod +x /bin/dd-dump')

            dd_dump_in, dd_dump_out, dd_dump_err = ssh.exec_command(
                'dd-dump if=/dev/disk1 of={}'.format(shsh_dump_path))

        try:
            sftp_client.get(shsh_dump_path, '.tmp/shsh_dump.bin')
        except FileNotFoundError:
            print('Somehow {} does not exist!'.format(shsh_dump_path))
            raise
        else:
            sftp_client.close()
            ssh.close()

            # Ensure that '.tmp/shsh_dump.bin' was actually downloaded

            try:
                os.path.exists(shsh_dump_path)
            except FileNotFoundError:
                print('Wut? Somehow the dump does not exist!')
                raise
            else:
                print('Seems like {} exists!'.format(shsh_dump_path))


def extract():
    subprocess.run(
        ('img4tool',
         '-s',
         '.tmp/blob.shsh2',
         '--convert',
         '.tmp/shsh_dump.bin'),
        stdout=subprocess.DEVNULL)

    try:
        os.path.exists('.tmp/blob.shsh2')
    except FileNotFoundError:
        print('Something went wrong extracting the shsh/ticket from the dump!')
        raise
    else:
        print('Seems like everything worked! Enjoy your dumped shsh :P -Merc')


def go():
    argv = sys.argv

    if not os.path.exists('.tmp'):
        has_plist = 'Compiled with plist: YES'
        img4tool_check = subprocess.run(
            ('which',
             'img4tool'),
            stdout=subprocess.DEVNULL)

        if img4tool_check.returncode == 1 or has_plist not in img4tool_check.stdout:
            getimg4tool()

        ldid_check = subprocess.run(
            ('which',
             'ldid'),
            stdout=subprocess.DEVNULL)

        if ldid_check.returncode == 1:
            getldid()

    if not os.path.exists('.tmp/shsh_dump.bin'):
        print('Starting dumping process!')
        dump(argv[2], argv[4], argv[6], argv[8])
        extract()
    else:
        if not os.path.exists('.tmp/blob.shsh2'):
            print('Seems like we already have a dump, just extracting!')
            extract()
        else:
            sys.exit('Nothing to do!')


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '--ip',
        help='Specify address of your device',
        metavar='\b',
        nargs=1,
        required=True)

    parser.add_argument(
        '--port',
        help='Use a different port for SSH',
        metavar='\b',
        nargs=1,
        required=True)

    parser.add_argument(
        '--user',
        help='Username to connect with (default should be root)',
        metavar='\b',
        nargs=1,
        required=True)

    parser.add_argument(
        '--password',
        help='Password of the user you choose (if using root, default password is alpine)',
        metavar='\b',
        nargs=1,
        required=True)

    try:
        args = parser.parse_args()
    except Exception:
        sys.exit(parser.print_help(sys.stderr))
    else:
        start = time.time()
        go()
        end = time.time() - start
        print('We took {:.2f} seconds!'.format(end))


if __name__ == '__main__':
    main()
