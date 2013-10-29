#!/usr/bin/env python

"""
giFTP - Git commit to FTP upload made easy.

The MIT License (MIT)

Copyright (c) 2013 Eka Putra

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
the Software, and to permit persons to whom the Software is furnished to do so,
subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

import os
import sys
import ftplib
import argparse
import json

from git import Repo
from git.exc import NoSuchPathError, InvalidGitRepositoryError

from ftp_session import (FTPSession, ConnectionErrorException,
                         RemotePathNotExistException)
from giftp import __VERSION__

CONFIG_FILE = 'gtp.json'


def generate_initial_config():
    """
    Generate config template.
    """
    config = {
        'host': {
            'url': 'example.com',
            'username': '',
            'password': '',
            'path': '',
        },
        'repo': {
            'path': '/absolute/path/to-your/git-repo',
            'branch': 'master',
            'latest_commit': '',
        },
    }

    # Check if config file already exist.
    if os.path.isfile(CONFIG_FILE):
        print '> [WARNING] Config file already exist.\n'
        sys.exit(0)

    try:
        fp = open(CONFIG_FILE, 'w')
        json.dump(config, fp, indent=4)
    except:
        print '> [ERROR] Please make sure you have a write permission to this directory.'
        sys.exit(0)
    else:
        print '> Config file has been generated...'
        print '> Now edit "%s" and fill with your FTP and GIT information.\n' % CONFIG_FILE
    finally:
        fp.close()


def run_update(test=False, simulate=False):
    """
    Run update to remote server.
    """
    # Check if config file exist.
    if not os.path.isfile(CONFIG_FILE):
        print '> [WARNING] Config file doesn\'t exist.'
        print '> Generate one with command "gtp init"\n'
        sys.exit(0)

    # open the config file
    try:
        fp = open(CONFIG_FILE, 'r')
    except:
        print '> [ERROR] Please make sure you have a read access to "%s".' % CONFIG_FILE
        sys.exit(0)

    # read config file
    try:
        config = json.load(fp)
    except:
        print '> [ERROR] "%s" has invalid JSON format.\n' % CONFIG_FILE
    else:
        fp.close()
        if not test:
            inspect_repo(config.get('repo'), config.get('host'), simulate)
        else:
            test_connection(config.get('host'))


def test_connection(ftp_creds):
    """
    Test a FTP connection based on supplied credentials.
    """
    print '> [INFO] Connecting...'
    try:
        sess = FTPSession(ftp_creds.get('url'), ftp_creds.get('username'),
                          ftp_creds.get('password'), path=ftp_creds.get('path'))
        sess.start()
    except (ConnectionErrorException, RemotePathNotExistException) as e:
        print e
    else:
        print '> [INFO] Connection success.\n'
        sess.stop()
        sys.exit(0)


def inspect_repo(repo_config, ftp_creds, simulate):
    """
    Inspect target Git repository.
    """
    branch = repo_config.get('branch')
    last_commit = repo_config.get('latest_commit')

    try:
        repo = Repo(repo_config.get('path'))
    except (NoSuchPathError, InvalidGitRepositoryError) as e:
        print '> [ERROR] Repo does not exist or invalid. %s\n' % e.message
        sys.exit(1)

    print '> [INFO] Checking repository...'
    # Count how many commit after the last commit
    commit_num = 0
    for commit in repo.iter_commits(branch, max_count=50):
        commit_num += 1
        if commit.hexsha == last_commit:
            break

    # Loop on each commit and detect changes from previous commit.
    # Gather changed file data and update remote file.
    counter = commit_num

    print '> [INFO] Found %s new commit...' % (commit_num-1)

    # Exit if no new commit available
    if commit_num-1 == 0:
        print '> [INFO] Nothing to update. Exit.\n'
        sys.exit(0)

    for i in range(commit_num):
        counter -= 1

        if counter - 1 < 0:
            break

        tip_branch = '%s~%s' % (branch, counter)
        tip_next_branch = '%s~%s' % (branch, counter-1)

        tip = repo.commit(tip_branch)
        tip_next = repo.commit(tip_next_branch)

        # print '(%s) %s --> (%s) %s' % (tip_branch, tip, tip_next_branch, tip_next)

        diffs = tip.diff(tip_next)

        try:
            sess = FTPSession(ftp_creds.get('url'), ftp_creds.get('username'),
                              ftp_creds.get('password'), path=ftp_creds.get('path'),
                              simulate=simulate)
            sess.start()
        except (ConnectionErrorException, RemotePathNotExistException) as e:
            print e
            sys.exit(1)
        else:
            update_changes(sess, diffs, tip_next)
            sess.stop()

            if not simulate:
                # Once updating success (non simulate)
                # record the current last commit ID.
                save_latest_commit(tip_next.hexsha)


def update_changes(sess, diffs, commit):
    """
    Update associated file on the remote server based on the diffs infomation.
    This will allow us to work only with file that has changed, new or deleted.
    """

    print "\n> [INFO] Processing commit: %s" % commit.message.strip('\n')

    for diff in diffs.iter_change_type('D'):
        print '> |__[INFO] Deleting [%s]...' % diff.a_blob.path
        sess.delete(diff.a_blob.path)

    for diff in diffs.iter_change_type('A'):
        print '> |__[INFO] Adding [%s]...' % diff.b_blob.path
        sess.push(diff.b_blob.path, diff.b_blob.data_stream.stream)

    for diff in diffs.iter_change_type('M'):
        print '> |__[INFO] Updating [%s]...' % diff.b_blob.path
        sess.push(diff.b_blob.path, diff.b_blob.data_stream.stream, is_new=False)


def save_latest_commit(hexsha):
    """
    Get latest commit ID for current branch.
    """
    try:
        fp = open(CONFIG_FILE, 'r')
        config = json.load(fp)
    except Exception as e:
        print '\n> [ERROR] %s.' % e.message
    else:
        fp.close()

        config.get('repo')['latest_commit'] = hexsha
        try:
            fp = open(CONFIG_FILE, 'w')
            json.dump(config, fp, indent=4)
        except:
            print '\r> [ERROR] Please make sure you have a write permission to this directory.'
        else:
            fp.close()


def runner():
    """
    giFTP runner function.
    """
    parser = argparse.ArgumentParser(description='giFTP version %s' % __VERSION__,
                                     epilog='Fork me on GitHub https://github.com/ekaputra07/giFTP')
    parser.add_argument('-i', '--init', action='store_true',
                        help='Generate initial giFTP config on current directory.')
    parser.add_argument('-u', '--update', action='store_true',
                        help='Update changes to the server.')
    parser.add_argument('-t', '--test', action='store_true',
                        help='Test connection to the server.')
    parser.add_argument('-s', '--simulate', action='store_true',
                        help='Run simulation for the upload process.')
    args = parser.parse_args()

    print
    if args.init:
        generate_initial_config()
    elif args.update:
        run_update()
    elif args.test:
        run_update(test=True)
    elif args.simulate:
        run_update(simulate=True)
    print


if __name__ == '__main__':
    runner()
