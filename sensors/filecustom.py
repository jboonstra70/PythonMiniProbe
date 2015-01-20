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

#import sys
import gc
import logging

#try:
#    sys.path.append('../')
#    from pysnmp.entity.rfc3413.oneliner import cmdgen
#except Exception as e:
#    logging.error("PySNMP could not be imported. SNMP Sensors won't work.Error: %s" % e)
#    pass


class FileCustom(object):

    def __init__(self):
        gc.enable()

    @staticmethod
    def get_kind():
        """
        return sensor kind
        """
        return "mpfilecustom"

    @staticmethod
    def get_sensordef():
        """
        Definition of the sensor and data to be shown in the PRTG WebGUI
        """
        sensordefinition = {
            "kind": FileCustom.get_kind(),
            "name": "File Custom",
            "description": "Monitors a numerical value in a specified file",
            "help": "",
            "tag": "mpfilecustomsensor",
            "groups": [
                {
                    "name": "File values",
                    "caption": "File values",
                    "fields": [
                        {
                            "type": "edit",
                            "name": "filename",
                            "caption": "Filename",
                            "required": "1",
                            "help": "Please enter the filename with the sensor value."
                        },
                        {
                            "type": "edit",
                            "name": "unit",
                            "caption": "Unit String",
                            "default": "#",
                            "help": "Enter a 'unit' string, e.g. 'ms', 'Kbyte' (for display purposes only)."
                        },

                        {
                            "type": "radio",
                            "name": "value_type",
                            "caption": "Value Type",
                            "required": "1",
                            "help": "Select type of value given in file ",
                            "options": {
                                "integer": "Integer",
                                "float": "Float",
                                "counter": "Counter"
                            },
                            "default": "integer"
                        }
                    ]
                }
            ]
        }
        return sensordefinition

    def file_get(self, filename, value_mode, value_unit):
        f = open(filename, 'r')
        file_value = f.read()
        if value_mode == "float":
            value = float(file_value)
        else:
            value = int(file_value)

        channellist = [
            {
                "name": "Value",
                "mode": "%s" % value_mode,
                "unit": "custom",
                "customunit": "%s" % value_unit,
                "value": value
            }
        ]
        return channellist

    @staticmethod
    def get_data(data):
        filecustom = FileCustom()
        try:
            file_data = filecustom.file_get(data['filename'], data['value_type'], data['unit'])
            logging.info("Running sensor: %s" % filecustom.get_kind())
        except Exception as get_data_error:
            logging.error("Ooops Something went wrong with '%s' sensor %s. Error: %s" % (filecustom.get_kind(),
                                                                                         data['sensorid'],
                                                                                         get_data_error))
            data = {
                "sensorid": int(data['sensorid']),
                "error": "Exception",
                "code": 1,
                "message": "File Request failed. See log for details"
            }
            return data

        data = {
            "sensorid": int(data['sensorid']),
            "message": "OK",
            "channel": file_data
        }
        del filecustom
        gc.collect()
        return data
