#!/usr/bin/env python
#Copyright (c) 2014, Paessler AG <support@paessler.com>
#All rights reserved.
#Redistribution and use in source and binary forms, with or without modification, are permitted provided that the
# following conditions are met:
#1. Redistributions of source code must retain the above copyright notice, this list of conditions
# and the following disclaimer.
#2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions
# and the following disclaimer in the documentation and/or other materials provided with the distribution.
#3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse
# or promote products derived from this software without specific prior written permission.

#THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
# INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT,
# INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,
# EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


### PRTG Python Miniprobe
### Miniprobe needs at least Python 2.7 because of "importlib"
### If older python version is used you will have to install "importlib"

# import general modules
import sys
import hashlib
import importlib
import gc
import logging
from logging.handlers import WatchedFileHandler


# import own modules
sys.path.append('./')

try:
    import sensors
    import requests
except Exception as e:
    print e
    #sys.exit()


class MiniProbe(object):
    """
    Main class for the Python Mini Probe
    """
    def __init__(self):
        gc.enable()
        rlogger = logging.getLogger() # get root logger
        fh = WatchedFileHandler("./logs/probe.log")
        fh.setLevel(logging.DEBUG)
        fmt = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s", '%m/%d/%Y %H:%M:%S')
        fh.setFormatter(fmt)
        rlogger.addHandler(fh) # add WatchedFileHandler to root logger
        rlogger.setLevel(logging.DEBUG)

    def get_import_sensors(self):
        """
        import available sensor modules and return list of sensor objects
        """
        sensor_objects = []
        for mod in sensors.__all__:
            try:
                sensor_objects.append(self.load_class("sensors.%s.%s" % (mod.lower(), mod)))
            except Exception as import_error:
                print import_error
        return sensor_objects

    @staticmethod
    def load_class(full_class_string):
        """
        dynamically load a class from a string
        """
        class_data = full_class_string.split(".")
        module_path = ".".join(class_data[:-1])
        class_str = class_data[-1]
        module = importlib.import_module(module_path)
        return getattr(module, class_str)

    def read_config(self, path):
        """
        read configuration file and write data to dict
        """
        config = {}
        try:
            conf_file = open(path)
            for line in conf_file:
                if not (line == '\n'):
                    if not (line.startswith('#')):
                        config[line.split(':')[0]] = line.split(':')[1].rstrip()
            conf_file.close()
            return config
        except Exception as read_error:
            logging.error("No config found! Error Message: %s Exiting!" % read_error)
            sys.exit()

    @staticmethod
    def hash_access_key(key):
        """
        create hash of probes access key
        """
        return hashlib.sha1(key).hexdigest()

    def create_parameters(self, config, jsondata, i=None):
        """
        create URL parameters for announce, task and data requests
        """
        if i == 'announce':
            return {'gid': config['gid'], 'key': self.hash_access_key(config['key']), 'protocol': config['protocol'],
                    'name': config['name'], 'baseinterval': config['baseinterval'], 'sensors': jsondata}
        else:
            return {'gid': config['gid'], 'key': self.hash_access_key(config['key']), 'protocol': config['protocol']}

    def create_url(self, config, i=None):
        """
        creating the actual URL
        """
        if not (i is None) and (i != "data"):
            return "https://%s:%s/probe/%s" % (
                config['server'], config['port'], i)
        elif i == "data":
            return "https://%s:%s/probe/%s?gid=%s&protocol=%s&key=%s" % (config['server'], config['port'], i,
                                                                         config['gid'], config['protocol'],
                                                                         self.hash_access_key(config['key']))
            pass
        else:
            return "No method given"

    def build_announce(self, sensor_list):
        """
        build json for announce request
        """
        sensors_avail = []
        for sensor in sensor_list:
            sensors_avail.append(sensor.get_sensordef())
        return sensors_avail