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

import gc
import logging
import paramiko

class MFimPort(object):

    def __init__(self):
        gc.enable()

    @staticmethod
    def get_kind():
        """
        return sensor kind
        """
        return "mpmfimport"

    @staticmethod
    def get_sensordef():
        """
        Definition of the sensor and data to be shown in the PRTG WebGUI
        """
        sensordefinition = {
            "kind": MFimPort.get_kind(),
            "name": "mFi mPort",
            "description": "Monitors a sensor port of a mFi mPort device",
            "help": "",
            "tag": "mpmfimportsensor",
            "groups": [
                {
                    "name": "mPort values",
                    "caption": "mPort values",
                    "fields": [
                        {
                            "type": "edit",
                            "name": "username",
                            "caption": "Username",
                            "default": "admin",
                            "help": "Enter username for mPort device (used for ssh login)"
                        },
                        {
                            "type": "password",
                            "name": "password",
                            "caption": "Password",
                            "required": "1",
                            "help": "Enter password of username for mPort device (used for ssh login)"
                        },

                        {
                            "type": "radio",
                            "name": "port",
                            "caption": "Sensor port",
                            "required": "1",
                            "help": "Select port number of sensor",
                            "options": {
                                "1": "Port 1",
                                "2": "Port 2",
                                "3": "Port 3"
                            },
                            "default": "1"
                        }
                    ]
                }
            ]
        }
        return sensordefinition

    def get_port_data(self, hostname, sshUser, sshPass, port):
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname, username=sshUser, password=sshPass, allow_agent=False)
        logging.info("Execute ssh command...")
        command = "cat /dev/input1%s\nEOF" % str(port)
        stdin, stdout, stderr = client.exec_command(command)
        #logging.info("ssh command executed. Exit status %s" % stdout.channel.recv_exit_status())
        
        value = int(stdout.read())
        #for line in stdout:
        #   print line

        client.close()

        channellist = [
            {
                "name": "Value",
                "mode": "integer",
                "unit": "custom",
                "customunit": "no motion",
                "value": value,
            }
        ]
        return channellist

    @staticmethod
    def get_data(data):
        mFimPort = MFimPort()
        try:
            port_data = mFimPort.get_port_data(data['host'], data['username'], data['password'], data['port'])
            logging.info("Running sensor: %s" % mFimPort.get_kind())
        except Exception as get_data_error:
            logging.error("Ooops Something went wrong with '%s' sensor %s. Error: %s" % (mFimPort.get_kind(),
                                                                                         data['sensorid'],
                                                                                         get_data_error))
            data = {
                "sensorid": int(data['sensorid']),
                "error": "Exception",
                "code": 1,
                "message": "mPort Request failed. See log for details"
            }
            return data

        data = {
            "sensorid": int(data['sensorid']),
            "message": "OK",
            "channel": port_data
        }
        del mFimPort
        gc.collect()
        return data
