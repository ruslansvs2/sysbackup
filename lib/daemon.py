#!/usr/bin/python
# SySBackup deamon libs
# Version = "0.4.10"

import sys
import time
import datetime
import os
import re
sys.path.append(".")
import SB
import socket
import pickle


def log(text, file):
    logf = open(file, "a")
    logf.write(text)
    logf.close()


def check():
    tmp = SB.tmp
    LogDir = SB.LogDir
    DirBackup = SB.DirBackup
    SB.MongoCon()
    result = list(SB.collCluster.find({"Node": SB.Node }))
    if result == [] or result[0]["Node"] == "":
        text = "Add node to MongoDB\n"
        log(text, SB.Log)
        data = [{"Node": SB.Node}]
        SB.collCluster.insert(data, True)
    del result
    if not os.path.exists(tmp):
        os.makedirs(tmp)
    if not os.path.exists(LogDir):
        os.makedirs(LogDir)
    if not os.path.exists(DirBackup):
        os.makedirs(DirBackup)
    if os.path.isfile(SB.Pidfile):
        text = "\n{pd} already exists, exiting \n".format(pd=SB.Pidfile)
        log(text, SB.Log)
        print text
        return sys.exit(1)
    else:
        file(SB.Pidfile, 'w').write(SB.pid)


def create_queue():
    ServersQ = {}
    SB.MongoCon()
    Mq = SB.coll.find({"Status": {"$ne": "Disabled"}, "NodeName": SB.Node}).sort("Priv",  1)
    servers = list(Mq)
    return servers


def API():
    SERVER_ADDRESS = SB.IP
    SERVER_PORT = int(SB.Port)
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((SERVER_ADDRESS, SERVER_PORT))
    s.listen(255)
    print("Listening on address %s." %
          str((SERVER_ADDRESS, SERVER_PORT)))
    while True:
        c, addr = s.accept()
        print("\nConnection received from %s" % str(addr))
        try:
            while True:
                SB.MongoCon()
                data = c.recv(2048)
                if not data:
                    print("End of file from client. Resetting")
                    break
                data = data.decode()
                data = data.split("|")
                # print data
                print("Received '%s' from client " % data[0], str(addr))
                if data[0] == "Get":
                    DataMongo = list(SB.coll.find({"ServerIP": addr[0]}))
                    for R in DataMongo:
                        DataResult = R[data[1]]
                        if type(DataResult) == int:
                            DataResult = str(DataResult)
                        if DataResult == "":
                            DataResult = "Empty"
                elif data[0] == "Add":
                    DateUp = {data[1]: data[2]}
                    SB.coll.update({"ServerIP": addr[0]}, {
                                   "$set": DateUp}, upsert=False)
                    DataResult = "End"
                elif data[0] == "GetAll":
                    DataResult = list(SB.coll.find({"ServerIP": addr[0]}))
                else:
                    DataResult = "Error api: "
                DataResult = pickle.dumps(DataResult).encode()
                c.send(DataResult)
            c.close()
        except:
            pass


def create_tmp_file(Name, DirsEx):
    DirsEx = DirsEx.replace(' ', '')
    DirsEx = DirsEx.replace(',', '\n') + "\n"
    FileNameEx = SB.tmp + "/" + Name + "_ex.txt"
    FileEx = open(FileNameEx, "w")
    FileEx.write(DirsEx)
    FileEx.close()


def date_check(checkdate):
    checkdate = int(checkdate)
    date0 = datetime.datetime.now() - datetime.timedelta(hours=checkdate)
    date = date0.isoformat()
    return date


class daemon_supper(object):
    def __getitem__(self,key):
        return key


def mysqldump(server):
        cmd = "sbctl host " + \
                  server + " \"/usr/sbin/sbcl mysqldump\""
        os.system(cmd)
        time.sleep(3)


class backup_function:
    def __init__(self, S):
        self.Server = S
        SB.MongoCon()
        self.CodeRsync = None
        server_list = list(SB.coll.find({"Name": self.Server}))
        getkey=daemon_supper()
        for R in server_list:
            self.data=getkey.__getitem__(R)

        self.ISODateStart = datetime.datetime.now().isoformat()
        self.chdate = date_check(self.data["Frequency"])
        if self.data["Chmy"] == "YES":
            self.data["DirsExclude"] = self.data["DirsExclude"] + "," + self.data["DirsInc"]
        create_tmp_file(self.data["Name"], self.data["DirsExclude"])
        self.DirB = SB.DirBackup + "/" + self.data["Name"]
        self.DirBL = SB.DirBackup + "/" + self.data["Name"] + "/" + self.ISODateStart
        self.ExFile = SB.tmp + "/" + self.data["Name"] + "_ex.txt"
        self.Link = self.DirB + "/" + "Latest"

    def skip_backup(self):
        if self.data["DateEnd"] > self.chdate and \
                        self.data["Status"] == "Done":
            return 1
        elif  self.data["DateEnd"] > self.chdate and \
                        self.data["Status"] == "rsync error":
            return 1
        elif self.data["Status"] == "running":
            tbackuprun = self.data["Name"] + " Backup already running"
            log(tbackuprun, SB.Log)
            return 1
        elif self.data["MysqlReady"] == "NO" and self.data["Chmy"] == "YES":
            text = "\n" + self.data["Name"] + ": Mysqldump is not ready"
            log(text, SB.Log)
            return 1

    def start_log(self):
        text = """\n########### Start Backup ######
        Now TIME: {time}
        Server name: {name}
        User: {user}
        Server IP: {ip}
        Server port: {port}
        Options of rsync: {rsyncOpt}
        Dirs : {dirs}
        Dirs exclude: {dirE}
        DateStart : {dateS}\n"""
        text = text.format(time=datetime.datetime.now(),
                    name=self.data["Name"], user=self.data["User"], ip=self.data["ServerIP"],
                        port=self.data["ServerPort"], rsyncOpt=self.data["RsyncOpt"], dirs=self.data["Dirs"],
                           dirE=self.data["DirsExclude"], dateS=self.data["DateStart"])
        log(text, SB.Log)

    def update_status_start(self):
        self.ISODateStart = datetime.datetime.now().isoformat()
        Data = {"DateStart": self.ISODateStart,
                  "Status": "running", "DateEnd": ""}
        SB.coll.update({'_id': self.data["_id"]}, {"$set": Data}, upsert=False)

    def update_status_end(self, status):
        self.ISODateEnd = datetime.datetime.now().isoformat()
        Data = {"DateEnd": self.ISODateEnd, "Status": status}
        SB.coll.update({'_id': self.data["_id"]}, {"$set": Data}, upsert=False)

    def create_path(self):
        if not os.path.exists(self.DirB):
            os.makedirs(self.DirB)
        if not os.path.exists(self.DirBL):
            os.makedirs(self.DirBL)
    # old
    def create_rsync_dirs(self):
        dirs=[]
        for RD in self.data["Dirs"].split(","):
            if RD != "/":
                RD = re.sub(r'\/$', '', RD)
            dirs.append(RD)
        return dirs
    ##
    # new
    def rm_slash(self, dir):
        if dir !="/":
            return re.sub(r'\/$', '', dir)


    def create_rsync_dirs2(self):
        yield (self.rm_slash(dirs) for dirs in self.data["Dirs"].split(","))
    ##
    1
    def error_log(self, server_name, local_text):
        text = server_name + datetime.datetime.now().isoformat() +" "+ local_text +"\n"
        log(text, SB.LogError)
        self.CodeRsync = "1"

    def rsync_dirs(self, dirs):
        for dir in dirs:
            cmd=("/usr/bin/rsync  {rsopt} --relative --log-file={logdir}/{serv}.log --progress" \
                       " -e \"/usr/bin/ssh -p {port}\"  --delete  --timeout=600 --ignore-errors --exclude-from={exf}" \
                       " --link-dest={dir}/Latest {user}@{ip}:{rd}  {dirbl} ".format(rsopt=self.data["RsyncOpt"],
                                                                                     port=self.data["ServerPort"],
                                                                                     exf=self.ExFile,
                                                                                     dir=self.DirB,
                                                                                     user=self.data["User"],
                                                                                     ip=self.data["ServerIP"],
                                                                                     rd=dir,
                                                                                     dirbl=self.DirBL,
                                                                                     logdir=SB.LogDir,
                                                                                     serv=self.data["Name"]))
            code = os.system(cmd)
            if code > 0:
                self.error_log(self.data["Name"], "rsync error!")

    def rsync_mysql(self):
        cmd = "/usr/bin/rsync  {rsopt} --relative --log-file={logdir}/{serv}.log --progress " \
                            "-e \"/usr/bin/ssh -p {port}\" --timeout=600 --ignore-errors {user}@{ip}:{rd} " \
                            " {dirbl} ".format(rsopt=self.data["RsyncOpt"],
                                               port=self.data["ServerPort"],
                                               exf=self.ExFile,
                                               dir=self.DirB,
                                               user=self.data["User"],
                                               ip=self.data["ServerIP"],
                                               rd=self.data["DirsInc"],
                                               dirbl=self.DirBL,
                                               logdir=SB.LogDir,
                                               serv=self.data["Name"])
        code = os.system(cmd)
        if code > 0:
            self.error_log(self.data["Name"], "rsync error, mysql directory!")

    def remove_link(self):
        try:
            os.remove(self.Link)
            time.sleep(3)
        except:
            pass

    def create_status(self):
        if self.CodeRsync is not None:
            Status = "rsync error"
        else:
            Status = "Done"
        return Status

    def end_text(self, text_clean):
        text = """\n############ End Backup  #######
        Now TIME: {time}
        Server name: {name}
        {text_clean}
        DateEnd : {date}"""
        text = text.format(time=datetime.datetime.now(),
                           name=self.data["Name"],
                           text_clean=text_clean,
                           date=self.data["DateEnd"])
        log(text, SB.Log)

    def clean_local_store(self):
        Drs = set()
        rDir = os.listdir(self.DirB)
        CleanD = int(self.data["CleanDate"]) * 24
        DCh = date_check(CleanD)
        for rd in rDir:
            Drs.add(rd)
        Drs.discard("Latest")
        resultDir = filter(lambda x: DCh > x, Drs)
        all_path=[]
        if resultDir != [] and self.CodeRsync is None:
            for D in resultDir:
                path = self.DirB + "/" + D
                # print path
                cmdrm = "/bin/rm -rf {p}".format(p=path)
                os.system(cmdrm)
                all_path.append(path+" ")

        else:
            if self.CodeRsync is None:
                return SB.t_skip_clean +" have not old files"
            else:
                return SB.t_skip_clean +" Error, probably rsync error"
        return "Deleted directory/ies :"+str(all_path)


class backup:
    def __init__(self, S, check=0):
        self.Server = S
        self.check=check
        self.bf=backup_function(self.Server)

    def run(self):
        if self.bf.skip_backup() == 1 \
                and self.check == 0:
            return
        self.bf.start_log()
        self.bf.update_status_start()
        self.bf.create_path()


        self.bf.rsync_dirs(self.bf.create_rsync_dirs())
        #self.bf.rsync_dirs()
        if self.bf.data["Chmy"] == "YES":
            if self.check == 1:
                mysqldump(self.Server)
            self.bf.rsync_mysql()

        self.bf.remove_link()
        os.symlink(self.bf.DirBL, self.bf.Link)
        self.bf.update_status_end(self.bf.create_status())
        self.bf.end_text(self.bf.clean_local_store())


