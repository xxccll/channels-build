#! /usr/bin/python
# coding=utf-8
import sys
import os
import json
import zipfile
import time
import shutil

__author__ = 'lianglong'

# 解决print报错
reload(sys)
sys.setdefaultencoding('utf-8')


class Generator(object):

    # 当前工作目录,指的是当前py文件所在的目录
    pwd = 0
    # 输出目录out
    out = 0
    # 源apk文件,未写入渠道号的文件
    src = 0
    # 渠道配置对象
    obj = 0

    def __init__(self, s, f):
        self.pwd = pwd()
        self.out = self.pwd + os.sep + "out"
        self.src = s
        self.obj = self.parse(f)

    def parse(self, f):
        if not os.path.exists(f):
            return 0
        obj = 0
        try:
            content = open(f).read()
            obj = json.loads(content)
        finally:
            return obj

    def start(self):
        if os.path.exists(self.out):
            shutil.rmtree(self.out)
        os.mkdir(self.out)
        if not os.path.exists(self.src):
            print("apk源文件不存在")
            return
        if self.obj is 0:
            print("渠道配置文件不存在,或者配置信息不是JSON对象")
            return
        if "channels" not in self.obj:
            print("未发现渠道定义列表 \'channels\' ")
            return
        if not isinstance(self.obj["channels"], list):
            print("渠道定义列表 \'channels\' 不是一个JSON数组")
            return
        client = self.obj["client"] if "client" in self.obj else "App"
        write_to = self.obj["writeTo"] if "writeTo" in self.obj else "CHANNEL_VALUE"
        channels = self.obj["channels"]
        self.generate(client, write_to, channels)

    def generate(self, client, write_to, channels):
        time_stamp = time.strftime("%Y%m%d%H%M", time.localtime(int(time.time())))

        for channel in channels:
            if "name" not in channel:
                continue
            name = channel['name']
            alias = channel["alias"] if "alias" in channel else name
            version = ("-v" + channel["version"]) if "version" in channel else ""

            print("开始打渠道 '%s' 包" % alias)
            target = "%s-%s-%s.apk" % (client + version, time_stamp, name)
            unalign = '%s.unalign' % target

            try:
                print("生成未对齐 %s 文件" % unalign)
                shutil.copy(self.src, unalign)
                channel_file = "META-INF" + os.sep + write_to
                zipped = zipfile.ZipFile(unalign, 'a', zipfile.ZIP_DEFLATED)
                zipped.writestr(channel_file, name)
                print("将渠道号 %s 写入 %s 的 %s 文件" % (name, unalign, channel_file))
            finally:
                zipped.close()

            print("生成4字节对齐apk文件 %s" %  target)
            self.align(unalign, target)
            print("删除文件%s" % unalign)
            os.remove(unalign)
            print("移动渠道包%s至输出目录" % target)
            shutil.move(target, self.out + os.sep + target)
            print("渠道 '%s' 打包完成" % alias)
            print("...")

    def align(self, unalign, target):
        command = self.pwd + os.sep + 'lib' + os.sep + "zipalign " + "4 " + unalign + ' ' + target
        os.popen(command)


def pwd():
    # 获取脚本路径
    path = sys.path[0]
    # 判断为脚本文件还是py2exe编译后的文件，如果是脚本文件，则返回的是脚本的目录，如果是py2exe编译后的文件，则返回的是编译后的文件路径
    if os.path.isdir(path):
        return path
    elif os.path.isfile(path):
        return os.path.dirname(path)


length = len(sys.argv)
if length == 1:
    print("参数有误,请检查")
    exit(1)

src = sys.argv[1]
if len(sys.argv) >= 3 and sys.argv[2].strip():
    config = sys.argv[2]
else:
    config = pwd() + os.sep + "config.js"
generator = Generator(src, config)
generator.start()
