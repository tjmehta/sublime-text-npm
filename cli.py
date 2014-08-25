# copied from https://github.com/benschwarz/sublime-bower/blob/master/bower/utils/cli.py and modified
# original license:
# Copyright © 2013 Ben Schwarz
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

# this is a modified version (ex: overcome python bug 6689)

import sublime
import os
import subprocess

if os.name == 'nt':
    LOCAL_PATH = ';' + os.getenv('APPDATA') + '\\npm'
    BINARY_NAME = 'npm.cmd'
else:
    LOCAL_PATH = ':/usr/local/bin:/usr/local/sbin:/usr/local/share/npm/bin'
    BINARY_NAME = 'npm'

os.environ['PATH'] += LOCAL_PATH

class CLI():
    def find_binary(self):
        print("find_binary")
        for dir in os.environ['PATH'].split(os.pathsep):
            path = os.path.join(dir, BINARY_NAME)
            if os.path.exists(path):
                return path
        sublime.error_message(BINARY_NAME + ' could not be found in your $PATH. Check the installation guidelines - https://github.com/PixnBits/sublime-text-npm')

    def _prepare_command(self, command):
        binary = self.find_binary()
        command.insert(0, binary)

        cflags = 0

        if os.name == 'nt':
            cflags = 0x08000000  # Avoid opening of a cmd on Windows (CREATE_NO_WINDOW)

        # per http://bugs.python.org/issue6689 Popen handles commands differently on Win vs *nix
        # see http://stackoverflow.com/a/1254322/2770309
        if os.name != 'nt':
            command = " ".join(command)

        return [command, cflags]

    def execute(self, command, cwd):
        command, cflags = self._prepare_command(command)
        proc = subprocess.Popen(command, shell=True, cwd=cwd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, creationflags=cflags)

        stdout_data, stderr_data = proc.communicate()
        returncode = proc.wait()

        if stdout_data:
            stdout_data = stdout_data.decode('utf-8')
        if stderr_data:
            stderr_data = stderr_data.decode('utf-8')

        return [returncode, stdout_data, stderr_data]

    # based on http://stackoverflow.com/a/4418193
    def execute_long_running(self, command, cwd, on_readline):
        command, cflags = self._prepare_command(command)
        process = subprocess.Popen(command, shell=True, cwd=cwd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, creationflags=cflags)
        #process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        process_handler = CliLong()
        process_handler.set_process(process)
        process_handler.set_callback(on_readline)

        process_handler.start_reading()

        return process_handler


class CliLong(object):
    def set_process(self, process):
        self.process = process

    def set_callback(self, callback, callback_self=None):
        self.callback = callback
        if callback_self:
            self.callback_self = callback_self

    def start_reading(self, interval=100):
        # TODO: make interval configurable
        self.interval = interval
        sublime.set_timeout(self._readline, interval)

    def _readline(self):
        process = self.process
        nextline = process.stdout.readline()
        nextline = nextline.decode('utf-8')

        if nextline == '' and process.poll() != None:
            output = process.communicate()[0]
            exitCode = process.returncode

            if (exitCode == 0):
                return output
            else:
                raise ProcessException(command, exitCode, output)

        self.callback(nextline)
        # TODO: make interval configurable
        sublime.set_timeout(self._readline, 100)