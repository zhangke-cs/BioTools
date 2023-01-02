#!/usr/bin/env python3

__all__ = ['udp_client']

'''
    1. 发送验证信息
    2. 记录运行信息
        2.1. 记录开始和结束时间，开始时间先发送给服务器，程序结束时增加结束时间再发送给服务器。
'''

import os
import sys
import time
import pickle
import socket
import psutil
import logging
import subprocess as sp

'''
    统一信息格式，使用dumps(dict)发送
        1. 每条信息必须要存在action关键字段用以说明请求类型。
        2. 每条信息必须要存在version关键字段用以表明客户端版本。
'''

class udp_client:
    __slot__ = ['server_ip', 'server_port', 'encoding', 'logger', 'sock', 'all_informations', 'version', 'timeout_second']
    version = 1.0

    def __init__(self, server_ip:str, server_port:int, logger_name:str = '', encoding:str = 'utf8', timeout_second:int = 10) -> None:
        self.server_ip = server_ip
        self.server_port = server_port
        self.encoding = encoding
        self.timeout_second = timeout_second
        if logger_name == '':
            from ..colors_logging.colors_logging import colors_logging
            self.logger = colors_logging().create_logger(name = 'client', level = 'INFO')
        else:
            self.logger = logging.getLogger(logger_name + '.client')
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        '''
            父进程名、脚本名
        '''
        self.all_informations = {}
        self.all_informations['version'] = self.version
        self.all_informations['user'] = self.get_user()
        self.all_informations['host_name'] = os.uname().nodename
        self.all_informations['host_ip'] = self.get_ip()
        self.all_informations['machine_id'] = self.get_machine_id()
        self.all_informations['argv'] = " ".join(sys.argv)
        self.all_informations['pname'] = os.path.basename(sys.argv[0])
        self.all_informations['pwd'] = os.getcwd()
        self.all_informations['sdate'], self.all_informations['stime'] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()).split(" ")

    def record(self, opportunity:str = 'begin') -> None:
        '''
            收集运行信息并发送给服务器
        '''
        #0 parameters check
        if opportunity not in ['begin', 'end']:
            self.logger.error("Parameters opportunity is must be one of ['begin', 'end']!")
            raise ValueError("Parameters opportunity is must be one of ['begin', 'end']!")
        #1 final obtain info
        if opportunity == 'end':
            #update edate and etime to IPGS_RECORD database
            self.all_informations['edate'], self.all_informations['etime'] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()).split(" ")
        #2 submit info
        ## use record_dict not self.all_informations
        record_dict = {'action': 'record'}
        record_dict.update(self.all_informations)
        self.sock.sendto(pickle.dumps(record_dict), (self.server_ip, self.server_port))

    def verify(self) -> None:
        '''
            Function for Host Verify
        '''
        bytes_str = pickle.dumps({'action': 'verify', 'host_ip': self.all_informations['host_ip'],
            'machine_id': self.all_informations['machine_id'], 'version': self.version})
        self.sock.sendto(bytes_str, (self.server_ip, self.server_port))
        self.sock.settimeout(self.timeout_second)
        try:
            server_return = self.sock.recv(1024)
        except socket.timeout:
            self.logger.error("Verify, the server: %s did not respond within %d seconds!" % (self.server_ip, self.timeout_second))
            raise TimeoutError("Verify, the server: %s did not respond within %d seconds!" % (self.server_ip, self.timeout_second))
        except Exception as exp_obj:
            self.logger.error("Verify, unknown recv error:")
            self.logger.error("%s" % repr(exp_obj))
            raise(exp_obj)
        if pickle.loads(server_return) == True:
            self.logger.info("Verify, pass.")
        else:
            self.logger.error("Verify, fail.")
            raise SystemError("Host verify is fail, exit.")

    def get_ip(self) -> list:
        '''
            Sub Function for Obtain Host IP Address
        '''
        if_dict:dict = psutil.net_if_addrs()
        ip_list = []
        for every_network in if_dict:
            if every_network in ('lo', 'loop'):
                continue
            else:
                for every_snic in if_dict[every_network]:
                    if every_snic.family.name == 'AF_INET':
                        ip_list.append(every_snic.address)
        if len(ip_list) == 0:
            self.logger.warning("IP address acquisition failed!")
        return ip_list

    def get_user(self) -> str:
        '''
            Sub Function for Obtain User Name
        '''
        #0 from os.environ
        for every_word in ('USER', 'LOGNAME', 'LNAME', 'USERNAME'):
            if every_word in os.environ and len(os.environ[every_word]) > 0:
                return os.environ[every_word]
        #1 from subprocess
        sp_process = sp.run(['id', '-u', '-n'], stdout = sp.PIPE, stderr = sp.PIPE, timeout = 10)
        if sp_process.returncode != 0:
            raise sp.CalledProcessError(returncode = sp_process.returncode, cmd = 'id -u -n',
                output = sp_process.stdout.decode(self.encoding), stderr = sp_process.stderr.decode(self.encoding))
        else:
            sp_result = sp_process.stdout.decode(self.encoding).strip("\n")
            if len(sp_result) > 0:
                return sp_result
            else:
                self.logger.error("Command 'id -un' run complete, but, subprocess does not capture the output!")
                raise ValueError("Command 'id -un' run complete, but, subprocess does not capture the output!")

    def get_machine_id(self) -> str:
        '''
            Sub Function for Obtain Machine ID
        '''
        machine_id = ''
        for every_file in ('/etc/machine-id', '/var/lib/dbus/machine-id'):
            if os.path.exists(every_file):
                with open(every_file, mode = 'r') as ihandle:
                    machine_id = ihandle.readline().strip()
            else:
                continue
        if machine_id == '':
            raise SystemExit("Failed to obtain machine ID. Please, contact developer!")
        return machine_id