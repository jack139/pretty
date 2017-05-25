#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, json, shutil

import web
from config import setting
import helper

db = setting.db_web

# 上传图片

url = ('/plat/image2')


# 写临时文件
def write_tmp(filename, chunk_num, data): # 写入临时文件目录
    to_path='%s/tmp_%s' % (setting.image_store_path, filename)
    if not os.path.exists(to_path):
        os.makedirs(to_path)
        os.chmod(to_path, 0777)
    h=open('%s/%s.%03d' % (to_path, filename, chunk_num), 'wb')
    h.write(data)
    h.close()

# 合并tmp目录下文件
def write_to_file(filename, filename2):
    tmp_path='%s/tmp_%s' % (setting.image_store_path, filename)
    to_path='%s/%s' % (setting.image_store_path, filename2[:2])
    if not os.path.exists(to_path):
        os.makedirs(to_path)
        os.chmod(to_path, 0777)

    file_list = os.listdir(tmp_path)
    file_list = sorted(file_list)

    total_size = 0
    h=open('%s/%s' % (to_path, filename2), 'wb')
    for i in file_list:
        h2=open('%s/%s' % (tmp_path, i), 'r')
        c = h2.read()
        total_size += len(c)
        h.write(c)
        h2.close()
    h.close()
    shutil.rmtree(tmp_path)
    return total_size

# 计算临时文件数量
def count_tmp(filename):
    tmp_path='%s/tmp_%s' % (setting.image_store_path, filename)
    file_list = os.listdir(tmp_path)
    return len(file_list)

class handler: # 
    def POST(self):
        if helper.logged(helper.PRIV_USER|helper.PRIV_MCH):
            user_data=web.input()

            #print user_data

            resumableChunkNumber = int(user_data.get('resumableChunkNumber'))
            resumableTotalChunks = int(user_data.get('resumableTotalChunks'))
            resumableChunkSize = int(user_data.get('resumableChunkSize'))
            resumableCurrentChunkSize = int(user_data.get('resumableCurrentChunkSize'))
            resumableTotalSize = int(user_data.get('resumableTotalSize'))
            resumableFilename = user_data.get('resumableFilename').encode('utf-8')
            resumableIdentifier = user_data.get('resumableIdentifier').encode('utf-8')
            resumableType = user_data.get('resumableType').encode('utf-8')
            new_image_name = user_data.get('new_image_name').encode('utf-8')
            file_data = user_data.get('file')

            print resumableFilename
            print resumableTotalChunks, resumableChunkNumber
            #print resumableTotalSize, resumableChunkSize, resumableCurrentChunkSize, \
            #    resumableCurrentChunkSize==len(file_data)
            print new_image_name

            write_tmp(resumableIdentifier, resumableChunkNumber, file_data)

            # 如果是最后一个文件，则合并临时文件
            if count_tmp(resumableIdentifier)==resumableTotalChunks:
                image_name = new_image_name + os.path.splitext(resumableFilename)[1]
                db.base_image.insert_one({
                    'image' : image_name,
                    'file'  : resumableFilename,
                    'size'  : resumableTotalSize,
                    'refer' : 0,
                    'type'  : resumableType,
                })
                r = write_to_file(resumableIdentifier, image_name)
                if resumableTotalSize==r:
                    print 'Completed'
                else:
                    print 'Error: image_name=', image_name, 'file_size=', r

            return 'success'
        else:
            web.ctx.status = '415 can not upload'
            return 'can not upload'
