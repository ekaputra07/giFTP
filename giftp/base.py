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

from setuptools import setup, find_packages
"""

import sys, os
import ftplib
import argparse
import json

from git import Repo
from git.exc import NoSuchPathError, InvalidGitRepositoryError

from ftp_session import FTPSession, ConnectionErrorException, RemotePathNotExistException

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
			'head': '',
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


def run_update():
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
		inspect_repo(config.get('repo'), config.get('host'))


def inspect_repo(repo_config, ftp_creds):
	"""
	Inspect target Git repository.
	"""
	branch = repo_config.get('branch')
	last_commit = repo_config.get('head')

	try:
		repo = Repo(repo_config.get('path'))
	except (NoSuchPathError, InvalidGitRepositoryError) as e:
		print '> [ERROR] Repo does not exist or invalid. %s\n' % e.message
		sys.exit()


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
							  ftp_creds.get('password'), path=ftp_creds.get('path'))
			sess.start()
		except (ConnectionErrorException, RemotePathNotExistException) as e:
			print e
			sys.exit(0)
		else:
			update_changes(sess, diffs, tip_next)
			sess.stop()



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
		print '> |___[INFO] Updating [%s]...' % diff.b_blob.path
		sess.push(diff.b_blob.path, diff.b_blob.data_stream.stream, is_new=False)


def build_arguments():
	parser = argparse.ArgumentParser()
	parser.add_argument('action', help='init: Generate initial Giftp config on current directory. update: Update changes to remote server.')
	args = parser.parse_args()

	if args.action == 'init':
		print
		generate_initial_config()
	elif args.action == 'update':
		print
		run_update()
