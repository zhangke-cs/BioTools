#!/usr/bin/env python3

'''
    UDP SOCKET SERVER (Host Verify and ARGV Record)
'''

__all__ = ['udp_server', 'info_handle']

import socket
import pickle
import logging
import pymysql as pm

from typing import List
from socketserver import UDPServer, BaseRequestHandler

'''
    信息格式，使用loads(recv_bytes)读取信息
        1. 每条信息肯定存在type关键字段用以判断处理方式。
        2. 每条信息肯定存在version关键字段用以验证客户端版本。
'''

# LOGGING MODULE NAME
# EX: a.b
logger = logging.getLogger('logging name')

class udp_server(UDPServer):
    '''
        IPGS VERIFY AND RECORD UDP SERVER
    '''
    def __init__(self, address, handle_class, database_ip:str, database_port:int, database_name:str, logger:logging.Logger) -> None:
        '''
            Parameters for Handle Class
            Access via self.server property
        '''
        #0 build logger
        self.database_ip = database_ip
        self.database_port = database_port
        self.database_name = database_name
        self.logger = logger
        self.rows = self.rows()
        #1 init server
        UDPServer.__init__(self, address, handle_class)
        self.logger.info("Server init.")
        self.logger.info("Program_stat table have %d rows in %s@%s." % (self.rows, self.database_ip, self.database_name))
    
    def conn(self) -> pm.connections.Connection:
        '''
            Database Connection
        '''
        db_passwd = ""
        database_conf = {"host": self.database_ip, "port": self.database_port, "user": 'ipgs', "password": db_passwd, "charset": "utf8", "cursorclass": pm.cursors.Cursor}
        return pm.connect(**database_conf, db = self.database_name)

    def rows(self) -> int:
        pm_conn = self.conn()
        pm_cursor = pm_conn.cursor()
        pm_cursor.execute('SELECT count(*) FROM program_stat')
        rows_num = pm_cursor.fetchone()
        pm_cursor.close()
        pm_conn.close()
        return rows_num[0]

class info_handle(BaseRequestHandler):
    '''
        IPGS VERIFY AND RECORD HANDLE CLASS FOR UDP SERVER
    '''
    version = 1.0
    allow_machine_id = set(['SYSTEM MACHINE ID'])
    allow_hosts = set(['SYSTEM IP ADDRESS'])
    no_record = set(['action', 'machine_id'])

    def handle(self) -> None:
        #(b'aaaassssdddd\n', <socket.socket fd=3, family=AddressFamily.AF_INET, type=SocketKind.SOCK_DGRAM, proto=0, laddr=('127.0.0.1', 9999)>)
        #0 get request
        bytes_content, sock = self.request
        #1 deserialize
        content = pickle.loads(bytes_content)
        #2 check version
        if content['version'] != self.version:
            self.server.logger.error("Version error, Now, server version is %d, client version is %d" % (self.version, content['version']))
            self.server.logger.error("Content is:")
            self.server.logger.error("%s" % str(content))
            raise ValueError("Version of the server and the client is inconsistent!")
        #3 process request
        if isinstance(content, dict):
            if 'action' in content:
                if content['action'] == 'record':
                    self.record(content)
                elif content['action'] == 'verify':
                    self.verify(content, sock)
                else:
                    self.server.logger.error("Unknown Action: '%s', content is:" % content['action'])
                    self.server.logger.error("%s" % str(content))
                    raise ValueError("Unknown Action: '%s', please check log file." % content['action'])
            else:
                self.server.logger.error("Content has no 'action' key! No process.")
                KeyError("Content has no 'action' key! No process.")
        else:
            self.server.logger.error("Recv no suppect information, type: %s, content is %s" % (type(content), str(content)))
            raise TypeError("Recv no suppect information, type: %s, content is %s" % (type(content), str(content)))

    def verify(self, content:dict, sock:socket.socket) -> None:
        #0 check host
        if len(self.allow_hosts.intersection(content['host_ip'])) == 0:
            self.server.logger.info("Verify Failed, host, content is %s" % str(content))
            sock.sendto(pickle.dumps(False), self.client_address)
            return None
        #1 check machine_id
        if content['machine_id'] not in self.allow_machine_id:
            self.server.logger.info("Verify Failed, machine_id, content is %s" % str(content))
            sock.sendto(pickle.dumps(False), self.client_address)
            return None
        sock.sendto(pickle.dumps(True), self.client_address)

    def record(self, content:dict) -> None:
        '''
            UPDATE or INSERT DATA INTO DATABASE
        '''
        #0 filter somethings from content
        content = dict(filter(lambda x:x[0] not in self.no_record, content.items()))
        #1 build conn
        pm_conn = self.server.conn()
        pm_cursor = pm_conn.cursor()
        #2 check quote
        content['argv'] = content['argv'].replace('\'', '\\\'').replace('\"', '\\\"')
        #3 process host_ip
        if len(content['host_ip']) == 1:
            content['host_ip'] = content['host_ip'][0]
        else:
            #use sorted keep order
            content['host_ip'] = ';'.join(sorted(content['host_ip']))
        #4 insert or update data
        if 'etime' in content:
            set_strings = 'edate=\'%s\',etime=\'%s\'' % (content['edate'], content['etime'])
            where_strings = " AND ".join([ i + '=' + '\'' + content[i] + '\'' for i in ['sdate', 'stime', 'host_ip', 'pname', 'user']])
            try:
                pm_cursor.execute("UPDATE program_stat SET %s WHERE %s" % (set_strings, where_strings))
                pm_conn.commit()
            except Exception as error:
                self.server.logger.error("Record failed, Failed to execute the following MySQL statement:")
                self.server.logger.error("%s" % set_strings)
                raise(error)
        else:
            set_strings = 'id=%d' % self.server.rows + ',' + ','.join([ i + '=' + '\'' + str(content[i]) + '\'' for i in content])
            try:
                #VALUES MOTHOD: 0.334s, SET MOTHOD: 0.203s
                pm_cursor.execute("INSERT INTO program_stat SET %s" % set_strings)
                pm_conn.commit()
            except Exception as error:
                self.server.logger.error("Record failed, Failed to execute the following MySQL statement:")
                self.server.logger.error("%s" % set_strings)
                raise(error)
            self.server.rows += 1
        #5 close conn
        pm_cursor.close()
        pm_conn.close()

    def argv_parser(self) -> List[str]:
        '''
            ARGV解析器，按照pname分类解析得到更为仔细的信息，未实现
        '''
        ...
