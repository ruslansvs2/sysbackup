#!/usr/bin/python
# sbctl - SySBackup management program
# Copyright (c) 2017 Ruslan Variushkin,  ruslan@host4.biz
Version = "0.4.13"


import sys
import os
import re
import signal
import readline
#sys.path.append("lib/")
import SB
import variablessbctl
from variablessbctl import *


class daemon_supper(object):
    def __getitem__(self,key):
        return key


def Text_Style(data, color="YELLOW"):
    from colorama import Fore, Style
    Color = getattr(Fore, color)
    return (Color + data + Style.RESET_ALL)


def signal_handler(signal, frame):
            print Text_Style(tctrlD)
            sys.exit(0)


def List(allservers, mute=None):
    if  not allservers:
        print tHavenot
        sys.exit(0)
    global count
    count = 0
    getkey=daemon_supper()
    for R in allservers:
        count += 1
        data=getkey.__getitem__(R)
        globals().update(data)
        if mute is True:
            return
        print tStart
        print Text_Style(tServName + Name)
        print Text_Style(str(tServIP + ServerIP + "\n"))
        print tUser, User
        print tServPort, ServerPort
        print tPriy, Priv
        print tOpR + RsyncOpt
        if Status == "rsync error":
            print Text_Style(tStatus + Status, color="RED")
        elif Status == "running":
            print Text_Style(tStatus + Status)
        else:
            print tStatus + Status
        if DateStart:
            print tLastD + DateStart
        if DateEnd:
            print Text_Style(tLastDN + DateEnd)
        print tDir + Dirs
        print tDirEx + DirsExclude
        print Text_Style(tFB + str(Frequency))
        print tCleanB, CleanDate
        print tChmy, Chmy
        if Chmy == 'YES':
            print tDirBInc + DirsInc
            print tDBex + DBex
            print tMyDumpOpt + MyDumpOpt
            if MysqlLog == "Error":
                print Text_Style(tMysqlLog + MysqlLog, color="RED")
            if MysqlReady == "YES":
                print tMysqlReady + MysqlReady
            else:
                print Text_Style(tMysqlReady + MysqlReady, color="RED")
            print tDateStartMysql + DateStartMySQL
            print tDateStopMysql + DateStopMySQL + "\n"
        if Desc != "":
            print Text_Style(tDesc+Desc)
        print tNodeName + NodeName
    print tAOS, count



class Mongo:
#    def __init__(self, ):
#        self.pattern=pattern

    SB.MongoCon()
    def insert(self, **kwargs):
        Mongo.insert.__globals__.update(kwargs)
        DataServer = [{"Name": Name, "User": User,  "ServerIP": ServerIP, "ServerPort": ServerPort,
             "RsyncOpt": RsyncOpt, "Priv": Priv, "Dirs": Dirs, "DirsExclude": DirsExclude, "DateStart": "",
             "DateEnd": "", "Frequency": Frequency,  "CleanDate": CleanDate, "Chmy": Chmy, "MyDumpOpt": MyDumpOpt,
             "DirsInc": DirsInc, "DBex": DBex,  "MysqlReady": "Empty", "MysqlLog": "", "DateStartMySQL": "",
             "DateStopMySQL": "", "Status": "Never", "Desc": Desc, "NodeName": NodeName }]
        SB.coll.insert(DataServer, True)

    def List(self, pattern={}, mute=None):
        allservers = list(SB.coll.find(pattern))
        return List(allservers, mute)

    def FindParm(self, Parm, Obj, regex):
        if regex == "find-regex":
            Obj = {'$regex': Obj}
        elif regex == "find-not":
            Obj = {'$ne':  Obj}
        allservers = list(SB.coll.find({Parm: Obj}))
        return List(allservers)

    def RmNode(self, Node):
        Remove=SB.collCluster.remove({"Node" : Node}, )
        if Remove["n"] > 1:
            print Text_Style(tRmNodeResult)
        else:
           print Text_Style(tHaveNotNode)

    def ChangeStatus(self, Name, Stat):
        if Stat == "Done":
            Value = "Done"
        elif Stat == "Disabled":
            Value = "Disabled"
        elif Stat == "needbackup":
            Value = "needbackup"
        else:
            return  Text_Style(tUsestat)
        data_local = {"Status": Value}
        if Name.lower() == "all":
            SB.coll.update({}, {"$set": data_local}, upsert=False, multi=True )
        else:
            M.List({"Name": Name}, mute=True)
            SB.coll.update({'_id': _id}, {"$set": data_local}, upsert=False)
            M.List({"Name": Name})
        return tStatdone

    def Delete(self, Name):
        allservers = list(SB.coll.find({"Name": Name}))
        List(allservers)
        if count == 0:
            return
        #PrCheck(Name,ServerIP,ServerPort, RsyncOpt,Priv,Dirs, DirsExclude )
        yes = set(['yes', 'y', 'ye'])
        no = set(['no', 'n'])
        choice = InCheck(Text_Style(tDuD)).lower()
        if choice in yes:
            SB.coll.remove({'_id': _id})
            choice = InCheck(Text_Style(tDuDel + SB.DirBackup +
                                    "/" + Name + " ")).lower()
            if choice in yes:
                cmd = "rm -fr {dir}".format(dir=SB.DirBackup + "/" + Name)
                os.system(cmd)
        elif choice in no:
            print tBye
        else:
            sys.stdout.write(tPlease)

    def UpdateCl(self):
        allservers = list(SB.coll.find({}))
        for R in allservers:
            print tUpdateCl + R["Name"]
            cmd = "scp -P{port} /usr/share/sbcl/sbcl {user}@{ip}:/usr/sbin/".format(user=R["User"],
                                                                                    port=R["ServerPort"],
                                                                                    ip=R["ServerIP"])
            cmd_conf = "scp -P{port} /usr/share/sbcl/sbcl.ini {user}@{ip}:/etc/sbcl/".format(user=R["User"],
                                                                                    port=R["ServerPort"],
                                                                                    ip=R["ServerIP"])
            os.system(cmd)
            os.system(cmd_conf)


    def NodeList(self, ClusterData):
        global count
        count = 0
        print tVersion
        print tCluster
        for R in ClusterData:
            count += 1
            print tNode + Text_Style(R["Node"])
            nodelist = list(SB.coll.find({"NodeName": R["Node"]}))
            nodes = ""
            countnodes = 0
            for N in nodelist:
                countnodes += 1
                nodes = nodes + " " + N["Name"] + ","
            print tNodes + R["Node"] + " :" + nodes[:-1]
            print tNodehostCount, countnodes, "\n"
        if count > 1: print tNodeCount, count
        if count == 0: print tNodeNot

    def Nodeinfo(self, pattern={}):
        ClusterData = list(SB.collCluster.find(pattern))
        return Mongo().NodeList(ClusterData)

    def MoveNode(self, Name, Server):
        M.List({"Name": Name}, mute=True)
        data_local = {"NodeName": Server}
        SB.coll.update({'_id': _id}, {"$set": data_local}, upsert=False)
        M.List({"Name": Name})
        return tStatdone_Move_Node


def PrCheck(Name, User, ServerIP, ServerPort, RsyncOpt, Priv, Dirs, DirsExclude, Frequency, CleanDate):
    print tCheckInf + Name + "\n" + tUser, User, "\n" + tServIP, ServerIP, "\n" + tServPort,  ServerPort
    print tOpR + RsyncOpt + "\n" + tPriy,  Priv, "\n" + tDir + Dirs + "\n" + tDirEx + DirsExclude
    print tFB, Frequency, "\n" + tCleanB, CleanDate


def InCheck(data, default=None, Empty=None,  Space=None):
    Check = None
    if Space is not None:
        Result = raw_input(data) or default
        return Result
    while Check is None:
        Result = raw_input(data).replace(' ', '').replace('\t', '') or default
        if Result != "" and Result is not None or Empty == "YES":
            Check = "True"
    return Result


def InCheckIP(data, default=""):
    checkip = "True"
    while checkip:
        Result = raw_input(data) or default
        pat = re.compile("\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}")
        resultip = pat.match(Result)
        if resultip:
            checkip = None
    return Result


def Update(Name):
    CronN = None
    ChmyNReal = None
    M.List(pattern={"Name": Name})
    MyDumpOptN = MyDumpOpt
    DirsIncN = DirsInc
    DBexN = DBex
    ChmyN = Chmy
    MysqlReadyN = MysqlReady
    if count == 0:
        return
    if Chmy == "NO":
        tRmDel = None
    ServerNameN = InCheck(
        tServName + ' [Now:' + Name + ']: ',  default=Name)
    ServerIPN = InCheckIP(
        tServIP + ' [Now:' + ServerIP + ']: ', default=ServerIP)
    UserN = InCheck(
        tUser + Defroot + ' [Now:' + User + ']: ',  default=User)
    ServerPortN = InCheck(
        tServPort + Defport + ' [Now: ' + ServerPort + ' ]: ', default=ServerPort)
    RsyncOptN = InCheck(
        tOpR + Defop + ' [Now:' + RsyncOpt + ']: ', default=RsyncOpt, Space="True")
    PrivN = InCheck(
        tPriy + ' [ Now:' + str(Priv) + ' ]: ', default=Priv)
    DirsN = InCheck(tDir + ExampleDir +
                    ' [ Now:' + Dirs + ' ]: ', default=Dirs)
    DirsExcludeN = InCheck(
        tDirEx + ExampleDirEx + ' [ Now:' + DirsExclude + ']: ', default=DirsExclude,  Empty="YES")
    FrequencyN = InCheck(
        tFB + ' [ Now:' + str(Frequency) + ' ]: ', default=Frequency)
    CleanDateN = InCheck(
        tCleanB + ' [ Now:' + str(CleanDate) + ' ]: ', default=CleanDate)
    # PrCheck(ServerNameN, UserN, ServerIPN, ServerPortN, RsyncOptN,
    #        PrivN, DirsN, DirsExcludeN, FrequencyN, CleanDateN)
    yes = set(['yes', 'y', 'ye'])
    no = set(['no', 'n'])
    rm = set(['rm'])
    choice = InCheck(tMysqlUpdate).lower()
    connect = "ssh -p{Port} {User}@{IP} ".format(
        Port=ServerPortN, User=UserN, IP=ServerIPN)
    cmdcrondel = connect + " \"sed -i /sbcl/d /etc/crontab \""
    if choice in rm:
        ChmyN = "NO"
        ChmyNReal = "NO"
    elif choice in yes:
        ChmyN = "YES"
        ChmyNReal = "YES"
        choicech = InCheck(Text_Style(tCheckMy)).lower()
        if choicech in yes:
            pass
        else:
            print Text_Style(tPlconfMy)
            return
        cmdscp = "scp -P{Port} /usr/share/sbcl/sbcl {User}@{IP}:/usr/sbin/".format(Port=ServerPortN,
                                                                                   User=UserN,
                                                                                   IP=ServerIPN)
        cmddb = connect + " \"mysql -e 'show databases;'\""
        cmddf = connect + " \"df -h\""
        print tResdf
        os.system(cmddf)
        if DirsInc == "Empty":
            DirsIncExample = DirIncDef
        else:
            DirsIncExample = DirsInc
        DirsIncN = InCheck(
            tDirBInc + ExampleIncDir + ' [ Now:' + DirsInc + ' ]: ',
            default=DirsIncExample )
        print (Text_Style(tUdb))
        os.system(cmddb)
        print (Text_Style(tAOS))
        if DBex == "Empty":
            DBexExample = DBexDef
        else:
            DBexExample = DBex
        DBexN = InCheck(tDBex + ExampleExDB +
                        '[Now: ' + DBex + ']: ', default=DBexExample,  Empty="YES")
        if MyDumpOpt == "Empty":
            MyDumpOptExample = MysqlOptDef
        else:
            MyDumpOptExample = MyDumpOpt
        MyDumpOptN = InCheck(tMyDumpOpt + tDefMysqlOpt +
                             '[Now:' + MyDumpOpt + ']:', default=MyDumpOptExample, Space = "True")
        CronN = InCheck(tSbcltext + tSbclCron + tSbcltext2, default=tSbclCron, Space = "True")
        cmdcron = connect + " \"echo '" + CronN + "' >> /etc/crontab\""
    else:
        pass
    if CronN is not None:
        print CronN + tAddtoCron
    if CronN is None and ChmyN == "NO":
        MyDumpOptN = "Empty"
        DirsIncN = "Empty"
        DBexN = "Empty"
        MysqlReadyN = "Empty"
    else:
        pass
    print Text_Style(tDesc + Desc)
    DescN = InCheck(
        tDescrm,  default=Desc, Empty="YES", Space="True" )
    NodeNameN = InCheck(
        tNodeName+ ' [ Now:' + NodeName + ']: ',  default=NodeName )
    if DescN == "rm": DescN = ""
    choice = InCheck(tDataCor).lower()
    if choice in yes:
        # print _id
        data = {"Name":  ServerNameN, "User": UserN,  "ServerIP": ServerIPN, "ServerPort": ServerPortN,
                "RsyncOpt": RsyncOptN, "Dirs": DirsN, "DirsExclude": DirsExcludeN, "Priv": PrivN,
                "Frequency": FrequencyN, "CleanDate": CleanDateN, "DirsInc": DirsIncN, "DBex": DBexN,
                "MyDumpOpt": MyDumpOptN,  "Chmy": ChmyN, "MysqlReady": MysqlReadyN,
                "Desc": DescN, "NodeName": NodeNameN}

        SB.coll.update({'_id': _id}, {"$set": data}, upsert=False)
        if ChmyNReal == "YES":
            os.system(cmdscp)
            os.system(cmdcrondel)
            os.system(cmdcron)
        elif ChmyNReal == "NO":
            os.system(cmdcrondel)
            print tDelCronResult
        else:
            pass
        print Text_Style(tEndofUpdate)
    elif choice in no:
        print tBye
        return sys.exit(1)
    else:
        sys.stdout.write(tPlease)


def add():
    print Text_Style(tNote)
    #import time
    # time.sleep(3)
    yes = set(['yes', 'y', 'ye'])
    no = set(['no', 'n'])
    choicech = InCheck(tCheckRsync).lower()
    if choicech in yes:
        pass
    else:
        print Text_Style(tPlInR)
        return
    Name = InCheck(tServName)
    ServerIP = InCheckIP(tServIP)
    User = InCheck(tUser + Defroot, default=UserDef)
    ServerPort = InCheck(tServPort + Defport,  default=PortDef)
 #   ServerPort = ServerPort.replace(' ', '')
    RsyncOpt = InCheck(tOpR + Defop, default=RsyncOptDef, Space = "True")
    Priv = InCheck(tPriy + Defpri,  default=PrivDef)
    Dirs = InCheck(tDirB + ExampleDir + ": ",  default=DirsDef)
    DirsExclude = InCheck(
        tDirBx + ExampleDirEx + ": ",  default='',  Empty="YES")
    Frequency = InCheck(tFB + DefFr,  default=FrequencyDef)
    CleanDate = InCheck(tCleanB + DefClean,  default=CleanDateDef)
    # PrCheck(Name, User,  ServerIP, ServerPort,
    #        RsyncOpt, Priv, Dirs, DirsExclude, Frequency, CleanDate)
    choice = InCheck(tDataCor).lower()
    if choice in yes:
        print Text_Style(tAddsshKey)
        # time.sleep(3)
        connect = "ssh -p{Port} {User}@{IP} ".format(
            Port=ServerPort, User=User, IP=ServerIP)
        cmd = "cat " + SB.PublicKey + " | " + connect + \
            " \"mkdir -p ~/.ssh && cat >>  ~/.ssh/authorized_keys\""
        cmdscp = "scp -P{Port} /usr/share/sbcl/sbcl {User}@{IP}:/usr/sbin/".format(Port=ServerPort,
                                                                                   User=User, IP=ServerIP)
        cmdscpini = "scp -P{Port} /usr/share/sbcl/sbcl.ini {User}@{IP}:/etc/sbcl/".format(Port=ServerPort,
                                                                                   User=User, IP=ServerIP)
        cmdmkini = connect + "\"mkdir -p /etc/sbcl\""
        cmdmklog = connect + "\"mkdir -p /var/log/sbclient\""
        os.system(cmdmkini)
        os.system(cmdmklog)
        os.system(cmd)
        os.system(cmdscp)
        os.system(cmdscpini)
        choise = InCheck(tDoUBackupMysql).lower()
        if choise in yes:
            choicech = InCheck((Text_Style(tCheckMy))).lower()
            if choicech in yes:
                pass
            else:
                print Text_Style(tPlconfMy)
                return
            Chmy = "YES"
            cmd = connect + " \"df -h\""
            print tResdf
            os.system(cmd)
            DirsInc = InCheck(
                tDirBInc + DefaultNodeName, default=DirIncDef)
            cmdmk = connect + "\"mkdir -p {dir}\"".format(dir=DirsInc)
            choice = InCheck(tDoUexdb).lower()
            if choice in yes:
                cmd = connect + " \"mysql -e 'show databases;'\""
                print Text_Style(tUdb)
                os.system(cmd)
                print (Text_Style("##############"))
                DBex = InCheck(tDBex + tdefExDb,
                               default=DBexDef,  Empty="YES")
            else:
                DBex = "Empty"
            MyDumpOpt = InCheck(tMyDumpOpt + tDefMysqlOpt, default=MysqlOptDef, Space = "True")
            Cron = InCheck(tSbcltext + tSbclCron +
                           tSbcltext2, default=tSbclCron,  Space = "True" )
            cmdcron = connect + " \"echo '" + Cron + "' >> /etc/crontab\""
        else:
            Chmy = "NO"
            MyDumpOpt = "Empty"
            DirsInc = "Empty"
            DBex = "Empty"
        serv = "^" + Name + "$"
        Desc = InCheck(
            tDesc,  default="",  Empty="YES", Space="True")
        NodeName = InCheck(
            tNodeName+" [default is your hostname "+SB.Node+" ]: ", default=SB.Node)
        M.insert(Name=Name, User=User, ServerIP=ServerIP, ServerPort=ServerPort, RsyncOpt=RsyncOpt,
                Priv=Priv, Dirs=Dirs, DirsExclude=DirsExclude, Frequency=Frequency, CleanDate=CleanDate,
                    Chmy=Chmy, MyDumpOpt=MyDumpOpt, DirsInc=DirsInc, DBex=DBex,
                        Desc=Desc, NodeName=NodeName )
        if Chmy == "YES":
            os.system(cmdmk)
            print tInstClient
            os.system(cmdcron)
        M.List(pattern={"Name": {'$regex': serv}})
    elif choice in no:
        print tBye
        return
    else:
        sys.stdout.write(tPlease)


def Command(Serv, Args):
    M.List(pattern={"Name": Serv}, mute=True)
    try:
        print tCommandHost + Name
        connect = "ssh -p{Port} {User}@{IP} ".format(
            Port=ServerPort, User=User, IP=ServerIP)
        cmd = connect + "\"" + Args + "\""
        return os.system(cmd)
    except:
        return


def FindHelp():
    return """\n\tUsing """ + Text_Style("find/find-not/find-regex") + """ with keys
    \t""" + tServName + Text_Style("\tName") + """
    \t""" + tServIP + Text_Style("\tServerIP") + """
    \t""" + tUser + Text_Style("\t\tUser") + """
    \t""" + tServPort + Text_Style("\tServerPort") + """
    \t""" + tPriy + Text_Style("\t\tPriv") + """
    \t""" + tOpR + Text_Style("\tRsyncOpt") + """
    \t""" + tStatus + Text_Style("\t\tStatus") + """
    \t""" + tLastD + Text_Style("\tDateStart") + """
    \t""" + tLastDN + Text_Style("\tDateEnd") + """
    \t""" + tDirB + Text_Style("\tDirs") + """
    \t""" + tDirBx + Text_Style("\tDirsExclude") + """
    \t""" + tFB + Text_Style("\tFrequency") + """
    \t""" + tCleanB + Text_Style("\tCleanDate") + """
    \t""" + tChmy + Text_Style("\t\tChmy") + """
    \t""" + tDirBInc + Text_Style("\tDirsInc") + """
    \t""" + tDBex + Text_Style("\tDBex") + """
    \t""" + tMyDumpOpt + Text_Style("\tMyDumpOpt") + """
    \t""" + tMysqlReady + Text_Style("\tMysqlReady") + """
    \t""" + tMysqlLog   + Text_Style("\tMysqlLog") + """
    \t""" + tDateStartMysql + Text_Style("\tDateStartMysql") + """
    \t""" + tDateStopMysql + Text_Style("\tDateStopMySQL") + """
    \n
    \tExamples: 
    \tlist all servers with status rsync error: """ + Text_Style("sbctl find Status \"rsync error\"") + """
    \tlist all servers with \"""" + tChmy + """NO\": """ + Text_Style("sbctl find Chmy NO") + """
    \n"""


def help():
    return tVersion+"""
    \nHelp function: Basic Usage:
    \t""" + Text_Style("add", color="WHITE") + """ or addhost \t\t- Add host to backup
    \t""" + Text_Style("l", color="WHITE") + """ or  list     \t\t- List all hosts
    \t""" + Text_Style("lmy", color="WHITE") + """ or  list-my     \t- List the backup hosts for only my node
    \t""" + Text_Style("se", color="WHITE") + """ or search   \t\t- Search for the host name. For example: """ + Text_Style("sbctl search w1.host.com") + """
    \t""" + Text_Style("re", color="WHITE") + """ or reconf   \t\t- Reconfiguration of backup settings. For example: """ + Text_Style("sbctl reconf w1.host.com") + """
    \t""" + Text_Style("rm", color="WHITE") + """ or remove   \t\t- Remove host. For example: """ + Text_Style("sbctl remove w1.host.com") + """
    \t""" + Text_Style("ho", color="WHITE") + """ or host     \t\t- Send command to remote host. For example: """ + Text_Style("sbctl host w1.host.com \"ls -al /var/backup\"") + """
    \t""" + Text_Style("backup", color="WHITE") + """         \t\t- Start backup. For example: """ + Text_Style("sbctl backup w1.host.com") + """
    \t""" + Text_Style("update-sbcl", color="WHITE") + """    \t\t- Update client. For example: sbctl update-sbcl
    \t""" + Text_Style("status", color="WHITE") + """         \t\t- Status update. For example: """ + Text_Style("sbctl status w1.host.com Done/Disabled/needbackup") + """
    \t""" + Text_Style("status all", color="WHITE") + """     \t\t- Update status for all nodes. For example: """ + Text_Style("sbctl status all Done/Disabled/needbackup") + """
    \t   status Done         \t- Backup is done
    \t   status Disabled     \t- Turn backup off
    \t   status needbackup   \t- Need to backup
    \t""" + Text_Style("find", color="WHITE") + """           \t\t- List the hosts matching parameters. For example: """ + Text_Style("sbctl find Status \"rsync error\"") + """
    \t""" + Text_Style("find-not", color="WHITE") + """       \t\t- List the hosts invert-matching parameters. For example: """ + Text_Style("sbctl find-not Chmy YES") + """
    \t""" + Text_Style("find-regex", color="WHITE") + """     \t\t- Use regular expression to find the hosts on their parameter. For example: """ + Text_Style("sbctl find-regex Status error") + """ 
    \t""" + Text_Style("find help", color="WHITE") + """     \t\t- List all parameter keys. For example: """ + Text_Style("sbctl find help") + """ 
    \t""" + FindHelp() + """
    \t""" + Text_Style("node", color="WHITE") + """      \t\t- Print the nodes of your cluster 
    \t\t""" + Text_Style("node name", color="WHITE") + """      \t- Print information for just one node. For example: """ + Text_Style("sbctl node mynode") + """
    \t""" + Text_Style("rm-node", color="WHITE") + """      \t\t- Remove node
    \t""" + Text_Style("move-host", color="WHITE") + """      \t\t- Move host to node. For example: """ + Text_Style("sbctl move-host Host New_Server_Node_Name") + """
    \t""" + Text_Style("more-then", color="WHITE") + """      \t\t- Backup errors, find days more than. For example: """ + Text_Style("sbctl more-than 1") + """

    \thelp              \t- Help
    \n"""


def main():
    try:
        argv = sys.argv[1]
        if argv == 'addhost' or argv == 'add':
            add()
        elif argv == 'list' or argv == 'l':
            M.List()
        elif argv == 'list-my' or argv == 'lmy':
            M.List(pattern={"NodeName": SB.Node})
        elif argv == 'search' or argv == 'se':
            M.List(pattern={"Name": {'$regex': sys.argv[2]}})
        elif argv == 'reconf' or argv == 're':
            Update(sys.argv[2])
        elif argv == 'remove' or argv == 'rm':
            M.Delete(sys.argv[2])
        elif argv == 'more-than':
            from datetime import datetime, timedelta
            ISODateStart = datetime.now() - timedelta(days=int(sys.argv[2]))
            M.List(pattern={"$and":[{"DateStart":{'$lt':ISODateStart.isoformat()}}, {"Status":{'$ne':"Disabled"}}]})
        elif argv == 'host' or argv == 'ho':
            Command(sys.argv[2], sys.argv[3])
        elif argv == "backup":
            cmd = "sbd backup " + sys.argv[2]
            os.system(cmd)
        elif argv == "status":
            try:
                print M.ChangeStatus(sys.argv[2], sys.argv[3])
            except:
                pass
        elif argv == "find" or argv == "find-regex" or argv == "find-not":
            if sys.argv[2] == "help":
                print FindHelp()
            else:
                M.FindParm(sys.argv[2], sys.argv[3], regex=argv)
        elif argv == "update-sbcl":
            M.UpdateCl()
        elif argv == "node":
            try:
                M.Nodeinfo(pattern={"Node": sys.argv[2]})
            except:
                M.Nodeinfo()
        elif argv == "rm-node":
            M.RmNode(sys.argv[2])
        elif argv == "move-host":
            try:
                M.MoveNode(sys.argv[2], sys.argv[3])
            except:
                tNoteNodeOrServer
        else:
            print help()
    except IndexError:
        print help()
    except EOFError:
        print Text_Style(tBye)


if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    M=Mongo()
    main()
