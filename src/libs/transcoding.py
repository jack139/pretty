#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json, redis, os
import app_helper
from config import setting

db = setting.db_web

# redis 连接
rdb = redis.Redis(host='127.0.0.1', port=6379, password='Xqs9$ta3j3s5Ey6_CiP', db=0)

# 推送到队列，进行转码，返回当前队列中排队数量
def psuh_to_transcoding(obj_id, filename):
    filepath='%s/%s' % (setting.media_store_path, filename)
    filetype = os.path.splitext(filename)[1][1:].lower()
    if filetype not in ['mp4','avi']: # 只转mp4和avi
        return False
    new_key = {
        "id"           : int(obj_id),
        "filepath"     : filepath,
        "resolution_x" : 640,
        "resolution_y" : 480,
        "format"       : filetype,
    }
    return rdb.rpush('transcoding_in', json.dumps(new_key))


# 检查已转码队列，保存更新转码文件, 返回本次处理的数量
def check_transcoded_files():
    n = 0
    while True:
        one_key = rdb.lpop('transcoding_out')
        if one_key is None:
            break

        one_key2 = json.loads(one_key)
        filename = u'/'.join(one_key2['filepath'].split('/')[-2:])

        exist_path='%s/%s' % (setting.transcode_store_path, filename)
        print exist_path
        if not os.path.isfile(exist_path): # 文件不存在，说明转换出错
            print '转码出错', one_key2['id'], filename
            filename = 'FAIL'
        else:
            print '转码完成', one_key2['id'], filename
        db.obj_store.update_one({'obj_id':str(one_key2['id'])},{'$set':{
            'transcoded_filepath' : one_key2['filepath'],
            'transcoded_filename' : filename,
        }})

        n += 1

    return n

