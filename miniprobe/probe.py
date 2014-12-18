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
import json
import time
import gc
import logging
import socket

# import own modules
sys.path.append('./')

try:
    from miniprobe import MiniProbe
    import sensors
    import requests
    import multiprocessing
except Exception as e:
    print e
    #sys.exit()


def main():
        """
        Main routine for MiniProbe (Python)
        """
        # Enable Garbage Collection
        gc.enable()
        # make sure the probe will not stop
        probe_stop = False
        # make sure probe is announced at every start
        announce = False
        # read configuration file (existence check done in probe_controller.py)
        config = mini_probe.read_config('./probe.conf')
        # Doing some startup logging
        logging.info("PRTG Small Probe '%s' starting on '%s'" % (config['name'], socket.gethostname()))
        logging.info("Connecting to PRTG Core Server at %s:%s" % (config['server'], config['port']))
        # create hash of probe access key
        key_sha1 = mini_probe.hash_access_key(config['key'])
        # get list of all sensors announced in __init__.py in package sensors
        sensor_list = mini_probe.get_import_sensors()
        sensor_announce = mini_probe.build_announce(sensor_list)
        announce_json = json.dumps(sensor_announce)
        url_announce = mini_probe.create_url(config, 'announce')
        data_announce = mini_probe.create_parameters(config, announce_json, 'announce')

        while not announce:
            try:
                # announcing the probe and all sensors
                request_announce = requests.get(url_announce, params=data_announce, verify=False)
                announce = True
                logging.info("ANNOUNCE request successfully sent to PRTG Core Server at %s:%s."
                             % (config["server"], config["port"]))
                if config['debug']:
                    logging.debug("Connecting to %s:%s" % (config["server"], config["port"]))
                    logging.debug("Status Code: %s | Message: %s" % (request_announce.status_code,
                                                                     request_announce.text))
                request_announce.close()
            except Exception as announce_error:
                logging.error(announce_error)
                time.sleep(int(config['baseinterval']) / 2)

        while not probe_stop:
            # creating some objects only needed in loop
            url_task = mini_probe.create_url(config, 'tasks')
            task_data = {
                'gid': config['gid'],
                'protocol': config['protocol'],
                'key': key_sha1
            }
            procs = []
            out_queue = multiprocessing.Queue()
            task = False
            while not task:
                json_payload_data = []
                try:
                    request_task = requests.get(url_task, params=task_data, verify=False)
                    json_response = request_task.json()
                    request_task.close()
                    gc.collect()
                    task = True
                    logging.info("TASK request successfully sent to PRTG Core Server at %s:%s."
                                 % (config["server"], config["port"]))
                    if config['debug']:
                        logging.debug(url_task)
                except Exception as announce_error:
                    logging.error(announce_error)
                    time.sleep(int(config['baseinterval']) / 2)
            gc.collect()
            if str(json_response) != '[]':
                if config['subprocs']:
                    json_response_chunks = [json_response[i:i + int(config['subprocs'])]
                                            for i in range(0, len(json_response), int(config['subprocs']))]
                else:
                    json_response_chunks = [json_response[i:i + 10]
                                            for i in range(0, len(json_response), 10)]
                for element in json_response_chunks:
                    for part in element:
                        if config['debug']:
                            logging.debug(part)
                        for sensor in sensor_list:
                            if part['kind'] == sensor.get_kind():
                                p = multiprocessing.Process(target=sensor.get_data, args=(part, out_queue),
                                                            name=part['kind'])
                                procs.append(p)
                                p.start()
                            else:
                                pass
                        gc.collect()
                    try:
                        while len(json_payload_data) < len(element):
                            out = out_queue.get()
                            json_payload_data.append(out)
                    except Exception as e:
                        logging.error(e)
                        print e
                        pass
                    #print len(json_response_chunks)
                    #print len(json_payload_data)
                        #p.join()
                        #p.terminate()
                        #del p
                    #del out_queue
                    #procs = []
                    url_data = mini_probe.create_url(config, 'data')
                    try:
                        request_data = requests.post(url_data, data=json.dumps(json_payload_data), verify=False)
                        logging.info("DATA request successfully sent to PRTG Core Server at %s:%s."
                                     % (config["server"], config["port"]))
                        if config['debug']:
                            logging.debug(json_payload_data)
                        request_data.close()
                        json_payload_data = []
                    except Exception as announce_error:
                        logging.error(announce_error)
                    if len(json_response) > 10:
                        time.sleep((int(config['baseinterval']) * (9 / len(json_response))))
                    else:
                        time.sleep(int(config['baseinterval']) / 2)

            else:
                logging.info("Nothing to do. Waiting for %s seconds." % (int(config['baseinterval']) / 3))
                time.sleep(int(config['baseinterval']) / 3)

            # Delete some stuff used in the loop and run the garbage collector
            for p in procs:
                if not p.is_alive():
                    p.join()
                    p.terminate()
                    del p
                #p.join()
                #p.terminate()
                #del p
            del json_response
            del json_payload_data
            gc.collect()

            if config['cleanmem']:
                # checking if the clean memory option has been chosen during install then call the method to flush mem
                from utils import Utils
                Utils.clean_mem()
        sys.exit()

if __name__ == "__main__":
    mini_probe = MiniProbe()
    main()
