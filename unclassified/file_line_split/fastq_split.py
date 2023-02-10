#!/usr/bin/env python3

'''
    NO gzip support !!!
'''

__all__ = ['FastqSlicer', 'MultiFastqSlicer']

import os
import multiprocessing as mp

from typing import List

class FastqSlicer:
    def __init__(self, file_list:List[str], chunk_size:int = 100000, split_num:int = 0, encoding:str = 'utf8') -> None:
        if not isinstance(file_list, List):
            raise TypeError("file_list is List, but now is %s" % type(file_list))
        self.encoding = encoding
        self.pointers = self.seek_file(file_list, chunk_size, split_num)

    def seek_file(self, file_list:str, chunk_size:int = 100000, split_num:int = 0) -> List:
        seek_result = []
        for every_file in file_list:
            if not os.path.exists(every_file):
                raise FileNotFoundError("%s is not found!" % (every_file))
            init_pointer = 0
            total_size = os.path.getsize(every_file)
            input_handle = open(every_file, 'rb')
            if split_num >= 1:
                #recalculate chunk_size
                chunk_size = int((total_size - init_pointer) / split_num)
            while init_pointer < total_size:
                #seek and find line ends
                input_handle.seek(chunk_size, 1)
                _ = input_handle.readline()
                now_pointer = input_handle.tell()
                if now_pointer == init_pointer:
                    continue
                else:
                    check_data:List = input_handle.readlines(3)
                    end_pointer = input_handle.tell()
                    if len(check_data) == 3:
                        if check_data[0].startswith(b'@') and check_data[2].startswith(b'+'):
                            #save result
                            seek_result.append((every_file, init_pointer, end_pointer))
                            init_pointer = end_pointer
                    elif len(check_data) == 2:
                        if check_data[0].startswith(b'+'):
                            seek_result.append((every_file, init_pointer, end_pointer))
                            init_pointer = end_pointer
                    elif len(check_data) == 1:
                        seek_result.append((every_file, init_pointer, end_pointer))
                        init_pointer = end_pointer
                    else:
                        seek_result.append((every_file, init_pointer, now_pointer))
                        init_pointer = now_pointer
                    #because the readline method is used
            '''
                The problem of the last loop exceeding the file size is not dealt with,
                because it will automatically stop if it exceeds the file size during reading
            '''
            input_handle.close()
        return seek_result

class MultiFastqSlicer:
    '''
        from file_slice import MultiFastqSlicer
        for every_block in MultiFastqSlicer([fp1, fp2], 100000).pointers:
            b = open(every_block[0], 'rb')
            b.seek(every_block[1])
            c = b.read(every_block[2] - every_block[1]) #c is data for sub process.
    '''
    def __init__(self, file_list:List[str], threads:int = 5, chunk_size:int = 100000, split_num:int = 0, encoding:str = 'utf8'):
        if not isinstance(file_list, List):
            raise TypeError("file_list is List, but now is %s" % type(file_list))
        self.encoding = encoding
        self.pointers = self.begin(file_list, threads, chunk_size, split_num)

    def begin(self, file_list:list, threads:int = 5, chunk_size:int = 100000, split_num:int = 0) -> List:
        #1 build process pool
        pool = mp.Pool(processes = threads)
        #2 multiprocess call
        pool_result = []
        for every_file in file_list:
            parameters = [every_file, chunk_size, split_num]
            pool_result.append(pool.apply_async(self.seek_file, parameters))
        #3 join process
        result, final_result = [], []
        for e in pool_result:
            e.wait()
            result = e.get()
            final_result += result
        pool.close()
        pool.join()
        return final_result

    def seek_file(self, file:str, chunk_size:int = 100000, split_num:int = 0) -> List:
        seek_result = []
        if not os.path.exists(file):
            raise FileNotFoundError("%s is not found!" % (file))
        init_pointer = 0
        total_size = os.path.getsize(file)
        input_handle = open(file, 'rb')
        if split_num >= 1:
            #recalculate chunk_size
            chunk_size = int((total_size - init_pointer) / split_num)
        while init_pointer < total_size:
            #seek and find line ends
            input_handle.seek(chunk_size, 1)
            _ = input_handle.readline()
            now_pointer = input_handle.tell()
            if now_pointer == init_pointer:
                continue
            else:
                #check fastq format!
                check_data:List = input_handle.readlines(3)
                end_pointer = input_handle.tell()
                if len(check_data) == 3:
                    if check_data[0].startswith(b'@') and check_data[2].startswith(b'+'):
                        #save result
                        seek_result.append((file, init_pointer, end_pointer))
                        init_pointer = end_pointer
                elif len(check_data) == 2:
                    if check_data[0].startswith(b'+'):
                        seek_result.append((file, init_pointer, end_pointer))
                        init_pointer = end_pointer
                elif len(check_data) == 1:
                    seek_result.append((file, init_pointer, end_pointer))
                    init_pointer = end_pointer
                else:
                    seek_result.append((file, init_pointer, now_pointer))
                    init_pointer = now_pointer
                #because the readline method is used
        '''
            The problem of the last loop exceeding the file size is not dealt with,
            because it will automatically stop if it exceeds the file size during reading
        '''
        input_handle.close()
        return seek_result
