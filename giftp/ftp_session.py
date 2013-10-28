from ftplib import FTP

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


class BaseException(Exception):
	pass


class ConnectionErrorException(BaseException):
	""" When something wrong with the connection. """
	pass


class RemotePathNotExistException(BaseException):
	""" If remote path not exist """
	pass


class OperationStatus(object):
	""" Simple wrapper to store Operation status """
	def __init__(self, op, path, reason=None):
		self.operation = op
		self.path = path
		self.reason = reason

	def __repr__(self):
		if self.operation == 'A' and not self.reason:
			return u'Successfully add %s' % self.path
		elif self.operation == 'A' and self.reason:
			return u'Failed add %s' % self.path
		elif self.operation == 'M' and not self.reason:
			return u'Successfully update %s' % self.path
		elif self.operation == 'M' and self.reason:
			return u'Failed update %s' % self.path
		elif self.operation == 'D' and not self.reason:
			return u'Successfully delete %s' % self.path
		elif self.operation == 'D' and self.reason:
			return u'Failed delete %s' % self.path


class FTPSession(object):
	"""
	A class that handle all FTP operation.
	"""
	
	def __init__(self, host, username=None, password=None, path=None):
		"""
		Get FTP credentials during initialization.
		:host - required.
		:username and :password are optional, and the default connection will be
		anonymous FTP connection.
		"""
		self.host = host
		self.username = username
		self.password = password
		self.path = path

		self.session = None
		self.success_operation = []
		self.failed_operation = []


	def start(self):
		"""
		Start the connection.
		"""
		try:
			self.session = FTP(self.host)
			if self.username and self.password:
				self.session.login(self.username, self.password)
		except:
			raise ConnectionErrorException('> [ERROR] Failed connecting to server.\n')

		if self.path:
			try:
				self.session.cwd(self.path)
			except:
				self.stop()
				raise RemotePathNotExistException(
					'> [ERROR] Path "%s" does not exists on the server\n' % self.path)


	def stop(self):
		"""
		Stop connection.
		"""
		self.session.quit()


	def mkdir(self, segments):
		"""
		Handle directory creation if not yet exists on the server.
		"""
		dirs = []
		for segment in segments:
			dirs.append(segment)
			path = '/'.join(dirs)
			try:
				self.session.mkd(path)
			except Exception as e:
				# let's ignore it for now.
				# its means the dir already exist.
				pass
		return


	def push(self, path, stream, is_new=True):
		"""
		Add new file to remote server.
		"""
		segments = path.split('/')

		operation = 'A'
		if not is_new: operation = 'M'

		# Check if the file is located inside directory structure.
		# If yes, create the dirs if not exists.
		if len(segments) > 1: self.mkdir(segments[:-1])

		try:
			# Let's just always transfer the file as binary.
			self.session.storbinary('STOR %s' % path, stream)
		except Exception as e:
			# We don't want the whole operation stopped
			# instead, just log the status.
			self.failed_operation.append(OperationStatus(operation, path, e))
		else:
			self.success_operation.append(OperationStatus(operation, path))


	def delete(self, path):
		"""
		Delete file on the remote server.
		"""
		operation = 'D'
		try:
			self.session.delete(path)
		except Exception as e:
			self.failed_operation.append(OperationStatus(operation, path, e))
		else:
			self.success_operation.append(OperationStatus(operation, path))
