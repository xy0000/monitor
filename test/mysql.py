#!/usr/bin/env python
#coding=utf8
# created by  xuchunyang@cmbc.com.cn  on 2016-11-25
# modify by  xuchunyang@cmbc.com.cn  on  2016-11-28 for  adding  long query time sql monitor fuction.
import sys
import os
import inspect
import MySQLdb
import MySQLdb.cursors
import argparse
import json, re, struct, time,datetime, socket, argparse,logging,os
import random

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S',
                    filename='/tmp/test.log',
                    filemode='w')


class Metric(object):
    def __init__(self, host, key, value, clock=None):
        self.host = host
        self.key = key
        self.value = value
        self.clock = clock

    def __repr__(self):
        result = None
        if self.clock is None:
            result = 'Metric(%r, %r, %r)' % (self.host, self.key, self.value)
        else:
            result = 'Metric(%r, %r, %r, %r)' % (self.host, self.key, self.value, self.clock)
        return result


class GetMysqlStatus():
    def __init__(self):
        self.result = ''
        self.each_result = ''
        self.SlaveStatus = ''
        self.VariableInfo = ''
        self.InnodbInfo = ''
        self.ProcesslistInfo = ''
        self.InnodbTrxInfo = ''
        self.MaxQueryTime = 0
        self.Innolastlockinfofile = '/tmp/.Innolastlockinfofile'
        self.deadlockinfo = {}
        self.deadlockchecktime = 600
        self.deadlockitem = 'Deadlock'
        self.deadlockMessage = 'DeadLock has come  out'
        self.deadlockOkmessage = 'OK'
        self.LongTrxCheckTime = 10
        self.LongTrxCheckItem = 'longtrxinfocheck'
    def check(self, port,mypasswd):
        try:
            self.db = MySQLdb.connect(user=mysqluser, passwd=mypasswd,
                                      host="127.0.0.1", port=port,
                                      cursorclass=MySQLdb.cursors.DictCursor)
        except Exception, e:
            a = []
            a.append(Metric(args.mysql_hostname, 'MySQL.Online', 0))
            send_to_zabbix(a, zabbix_host, zabbix_port)
            raise Exception, 'Cannot interface with MySQL server, %s' % e

    def extract(self):
        try:
            c = self.db.cursor()
            c.execute("""show global status """)
            self.result = c.fetchall()
#            return self.result
            c.execute("""show slave status ; """)
            self.SlaveStatus = c.fetchall()
            c.execute("""show global variables like 'max%connections%' ; """)
            self.VariableInfo = c.fetchall()
            #c.execute("""show engine innodb status ;  """)
            #self.InnodbInfo = c.fetchall()
            c.execute("""show processlist  """)
            self.ProcesslistInfo = c.fetchall()
            if_checktime_reach=0
            if_checktime_reach=Check_item_looptime_reach(gl_item_checked_lasttime_status,self.LongTrxCheckItem,self.LongTrxCheckTime)
            if if_checktime_reach == 1:
               c.execute("""select * from information_schema.INNODB_TRX; """)
               self.InnodbTrxInfo = c.fetchall()
            c.close()
            self.db.close()
            a = []
            for i in self.result:
              a.append(Metric(args.mysql_hostname, ('MySQL.%s' % i['Variable_name']), '%s' % i['Value']))
            for j in self.SlaveStatus:
              #for  slavekey in j.keys():
              for  slavekey in slaveitem:
                a.append(Metric(args.mysql_hostname, ('MySQL.%s' % slavekey), '%s' % j[slavekey]))

            for v in self.VariableInfo:
              a.append(Metric(args.mysql_hostname, ('MySQL.%s' % v['Variable_name']), '%s' % v['Value']))

            #for v in self.InnodbInfo:
            #  #a.append(Metric(args.mysql_hostname, ('MySQL.%s' % v['Variable_name']), '%s' % v['Value']))
            #   line_no = 0
            #   sart_count_line = 0
            #   for  rows in  str(v).split(r'\n'):
            #       if  rows == 'LATEST DETECTED DEADLOCK':
            #           print 'dl lock %s ' % rows
            #           sart_count_line =  1
            #           line_no = 0
            #       if sart_count_line == 1:
            #           line_no = line_no + 1
            #       if line_no == 3:
            #           print rows
            #           break
            #       print rows
            #   print ' xcy check loop '
            ExceptCmd = ['Binlog Dump GTID','Sleep',r'Connect']
            MaxQueryTimeCmd = {}
            for p in self.ProcesslistInfo:
               LongQueryTimeSQLLogstr = json.dumps(p) + '\n'
               writeLog(LongQueryTimeSQLLog,'a',LongQueryTimeSQLLogstr,86400)
               queryTime = int(p['Time'])
               queryCmd = p['Command']
               if  queryCmd not in ExceptCmd:
                   if queryTime > self.MaxQueryTime :
                        self.MaxQueryTime = queryTime
                        MaxQueryTimeCmd = p
            ## get the max query Time to  zabbix
            a.append(Metric(args.mysql_hostname, 'MySQL.CurrentMaxQueryTime', self.MaxQueryTime))

            ##  get  the   trx info  to zabbix
            if if_checktime_reach == 1:
                oldest_start_time=datetime.datetime.now()
                init_start_time=oldest_start_time
                print 'oldest_start_time:%s ' % oldest_start_time
                max_trx_rows_modified=0
                max_trx_rows_locked=0
                max_trx_lock_memory_bytes=0
                trx_active_time=0
                longest_trx_time=0
                for trx in self.InnodbTrxInfo:
                    print 'trx:%s' % trx
                    trxstr = json.dumps(str(trx)) + '\n'
                    writeLog(global_trx_logfile,'a',trxstr)
                    trx_start_time=trx['trx_started']
                    trx_active_time=(init_start_time - trx_start_time).seconds
                    trx['trx_active_time']=trx_active_time
                    print 'again'
                    print 'trx:%s' % trx
                    trxstr = json.dumps(str(trx)) + '\n'
                    writeLog(global_trx_logfile,'a',trxstr)
                    if longest_trx_time < trx_active_time:
                        longest_trx_time=trx_active_time

                    print 'trx_start_time: %s'  % trx_start_time
                    trx_rows_modified=int(trx['trx_rows_modified'])
                    if max_trx_rows_modified < trx_rows_modified :
                       max_trx_rows_modified=trx_rows_modified

                    trx_rows_locked=int(trx['trx_rows_locked'])
                    if max_trx_rows_locked < trx_rows_locked :
                       max_trx_rows_locked=trx_rows_locked

                    trx_lock_memory_bytes=int(trx['trx_lock_memory_bytes'])

                    if max_trx_lock_memory_bytes < trx_lock_memory_bytes :
                       max_trx_lock_memory_bytes=trx_lock_memory_bytes


                a.append(Metric(args.mysql_hostname, 'MySQL.longest_trx_time', longest_trx_time))
                a.append(Metric(args.mysql_hostname, 'MySQL.max_trx_rows_locked', max_trx_rows_locked))
                a.append(Metric(args.mysql_hostname, 'MySQL.max_trx_lock_memory_bytes', max_trx_lock_memory_bytes))
                a.append(Metric(args.mysql_hostname, 'MySQL.max_trx_rows_modified', max_trx_rows_modified))


            a.append(Metric(args.mysql_hostname, 'MySQL.Online', 1))
            send_to_zabbix(a, zabbix_host, zabbix_port)




        except Exception, e:
            print e


    def getResponseTime(self):
        try:
            c = self.db.cursor()
            starttime = int(time.time())
            c.execute(getRespTimeSQL)



            a.append(Metric(args.mysql_hostname, 'MySQL.Online', 1))
            send_to_zabbix(a, zabbix_host, zabbix_port)




        except Exception, e:
            print e


    def getResponseTime(self):
        try:
            c = self.db.cursor()
            starttime = int(time.time())
            c.execute(getRespTimeSQL)
            c.close()
            self.db.close()
            endtime = int(time.time())
            difftime = endtime - starttime
            a = []
            a.append(Metric(args.mysql_hostname, 'MySQL.Resptime', '%s' % difftime))
            send_to_zabbix(a, zabbix_host, zabbix_port)
        except Exception, e:
            print e

    def getDeadlockInfo(self):

        lastdeadlktime = ''
        lastchecktime = 0

        if os.path.exists(self.Innolastlockinfofile):
           deadlockstatusFile = open(self.Innolastlockinfofile,'r')
           for row in  deadlockstatusFile.readlines():
               self.deadlockinfo = json.loads(row)
           deadlockstatusFile.close
           lastchecktime = self.deadlockinfo['lastchecktime']
           lastdeadlktime = self.deadlockinfo['lastdeadlktime']

        difftime = int(time.time()) - lastchecktime

        if difftime > self.deadlockchecktime:

           current_deadlock_time = self.checkdeadlock()
           self.deadlockinfo['lastchecktime'] = int(time.time())
           self.deadlockinfo['lastdeadlktime'] = current_deadlock_time

           currentDBLOCKinfostr = json.dumps(self.deadlockinfo)
           errlogstatusFile = open(self.Innolastlockinfofile,'w')
           errlogstatusFile.write(currentDBLOCKinfostr)
           errlogstatusFile.close()

           if  current_deadlock_time != lastdeadlktime and current_deadlock_time != '' :
                a = []
                a.append(Metric(args.mysql_hostname, 'MySQL.%s' % self.deadlockitem, '%s' % self.deadlockMessage))
                send_to_zabbix(a, zabbix_host, zabbix_port)
           else:
                a = []
                a.append(Metric(args.mysql_hostname, 'MySQL.%s' % self.deadlockitem, '%s' % self.deadlockOkmessage))
                send_to_zabbix(a, zabbix_host, zabbix_port)



    def checkdeadlock(self):

        thistimedeadlocktime = ''

        try:
            c = self.db.cursor()
            c.execute("""show engine innodb status ;  """)
            self.InnodbInfo = c.fetchall()
            c.close()
            self.db.close()
            for v in self.InnodbInfo:
              #a.append(Metric(args.mysql_hostname, ('MySQL.%s' % v['Variable_name']), '%s' % v['Value']))
               line_no = 0
               sart_count_line = 0
               for  rows in  str(v).split(r'\n'):
                   if  rows == 'LATEST DETECTED DEADLOCK':
                       print 'dl lock %s ' % rows
                       sart_count_line =  1
                       line_no = 0
                   if sart_count_line == 1:
                       line_no = line_no + 1
                   if line_no == 3:
                       thistimedeadlocktime = rows
                       break

            return thistimedeadlocktime

        except Exception, e:
            print e




    def getVal(self, key):
        for i in self.result:
            if i['Variable_name'] == key:
                self.each_result = i['Value']
        return self.each_result

    def TPS(self):
        TPS = int(self.getVal('Com_commit')) + int(self.getVal('Com_rollback'))
        return TPS

    def QPS(self):
        return int(self.getVal('Com_insert')) + int(self.getVal('Com_delete')) + int(self.getVal('Com_select')) + int(self.getVal('Com_update'))

    def Key_read_hit_ratio(self):
        try:
            Key_read_hit_ratio = (1 - float(self.getVal('Key_reads'))  / float(self.getVal('Key_read_requests'))) * 100
        except ZeroDivisionError, e:
            print "integer division or modulo by zero", e
        return Key_read_hit_ratio

    def Key_usage_ratio(self):
        try:
            Key_usage_ratio = float(self.getVal('Key_blocks_used')) / (float(self.getVal('Key_blocks_used')) + float(self.getVal('Key_blocks_unused')))
        except ZeroDivisionError, e:
            print "integer division or modulo by zero", e
        return Key_usage_ratio

    def Key_write_hit_ratio(self):
        try:
            Key_write_hit_ratio = (1 - float(self.getVal('Key_writes')) / float(self.getVal('Key_write_requests'))) * 100
        except ZeroDivisionError, e:
            print "integer division or modulo by zero", e
        return Key_write_hit_ratio

    def Innodb_buffer_read_hit_ratio(self):
        try:
            Innodb_buffer_read_hit_ratio = (1 - float(self.getVal('Innodb_buffer_pool_reads')) / float(self.getVal('Innodb_buffer_pool_read_requests'))) * 100
        except ZeroDivisionError, e:
            print "integer division or modulo by zero", e
        return Innodb_buffer_read_hit_ratio

    def Innodb_buffer_usage(self):
        try:
            Innodb_buffer_usage = (1 - float(self.getVal('Innodb_buffer_pool_pages_free')) / float(self.getVal('Innodb_buffer_pool_pages_total'))) * 100
        except ZeroDivisionError, e:
            print "integer division or modulo by zero", e
        return Innodb_buffer_usage

    def Innodb_buffer_pool_dirty_ratio(self):
        try:
            Innodb_buffer_pool_dirty_ratio = (float(self.getVal('Innodb_buffer_pool_pages_dirty')) / float(self.getVal('Innodb_buffer_pool_pages_total'))) * 100
        except ZeroDivisionError, e:
            print "integer division or modulo by zero", e
        return Innodb_buffer_pool_dirty_ratio

class ErrorOut():
    def error_print(self):
        """输出错误信息"""
        print
        print 'Usage: ' + sys.argv[0] + ' ' + ' MySQL_Status_Key '
        print
        sys.exit(1)



class ErrorLogCheck(object):

    def __init__(self, errlogfile,logfilestatusfile,newlogfile,excepruledic,errkeys,zbx_item,isHA=0,hamonitorstatusfile=r'/mysql/master_failover/log/monitor_status_message',hamonitortime=500):
        self.logfilename = errlogfile
        self.logfilestatusfile = logfilestatusfile
        self.newlogfile = newlogfile
        self.excepruledic = excepruledic
        self.errkeys = errkeys
        self.diffsize = 0
        self.oldsizeinfo = {}
        self.max_bytes = 50000
        self.zbx_item = zbx_item
        self.currentsize = 0
        self.isHA = isHA
        self.hamonitorstatusfie = hamonitorstatusfile
        self.hamonitortime = hamonitortime

    def parseNewlog(self):


        if self.isHA == 1:
           if os.path.exists(self.hamonitorstatusfie):
                cutime = os.path.getmtime(self.hamonitorstatusfie)
                nowtime = time.time()
                difftime = nowtime - cutime
                if  difftime > self.hamonitortime:
                   ha_monitor_program_ruing = 0
                else:
                   ha_monitor_program_ruing = 1
           else:
               ha_monitor_program_ruing = 0

           if ha_monitor_program_ruing == 0:
             a = []
             a.append(Metric(args.mysql_hostname, 'MySQL.%s' % self.zbx_item, 'Mysql HA Monitor program is not runing'))
             send_to_zabbix(a, zabbix_host, zabbix_port)
             return  0

        elif self.zbx_item == r'HAErrorlog':
             a = []
             a.append(Metric(args.mysql_hostname, 'MySQL.%s' % self.zbx_item, 'CMBC MYSQL OK:mysql error log is ok'))
             send_to_zabbix(a, zabbix_host, zabbix_port)
             return  0


        self.currentsize = os.path.getsize(self.logfilename)
        self.oldsize = self.currentsize
        skip_it = 0
        find_err = 0
        if os.path.exists(self.logfilestatusfile):
           errlogstatusFile = open(self.logfilestatusfile,'r')
           for row in  errlogstatusFile.readlines():
             self.oldsizeinfo = json.loads(row)
             self.oldsize = int(self.oldsizeinfo[self.zbx_item])
           errlogstatusFile.close()
        print 'xcy test '
        print 'oldsize %d' % self.oldsize
        print 'newlogfile %s ' % self.newlogfile




        self.diffsize =  self.currentsize - self.oldsize

        print 'diffsize:%d' % self.diffsize
        if self.diffsize < 0:
           self.diffsize = self.currentsize

        if self.diffsize > self.max_bytes:
           self.diffsize = self.max_bytes

        if self.diffsize > 0:
           logFile = open(self.logfilename, 'r')
           print 'diffsize:%d' % self.diffsize
           newerrFile = open(self.newlogfile, 'a')
           logFile.seek(-self.diffsize,2)
           find_err = 0

           for errkey in self.errkeys:
                if find_err == 1:
                   break;
                skip_it = 0
                print "errkey on top :%s " % errkey
                logFile.seek(-self.diffsize,2)
                for row in logFile.readlines():
                   #newerrFile.write(row)
                   print 'row:%s' % row.strip()
                   skip_it = 0
                   for wordkeys in self.excepruledic:
                      print 'row.find.value %d ' % row.find(wordkeys)
                      print 'excepted key words: %s ' % wordkeys
                      if  row.find(wordkeys) >= 0:
                          skip_it = 1
                          print  'wordkeys:%s' % wordkeys
                          print  'break wordkeys'
                          break
                   print 'skip_it value:%s' % skip_it
                   if skip_it == 1:
                       print  'break this rows:%s' % row
                       continue
                   else:
                             print  "errkey:%s " % errkey
                             print "find error key: %d " % row.find(errkey)
                             if  row.find(errkey) >= 0:
                                   find_err = 1
                             elif errkey == 'ANYWORDS':
                                   find_err = 1
                                   print 'errkey on  low: %s ' % errkey
                             if find_err == 1:
                                   a = []
                                 #  row = row.strip('\n')
                                   print 'find error row :%s' % row
                                   a.append(Metric(args.mysql_hostname, 'MySQL.%s' % self.zbx_item, '%s' % row))
                                   send_to_zabbix(a, zabbix_host, zabbix_port)
                                   newerrFile.write(row)
                                   newerrFile.close()

                   if find_err == 1:
                      break
                if find_err == 1:
                      break

        if find_err == 0:
          a = []
          if os.path.exists(self.newlogfile) and os.path.getsize(self.newlogfile) > 0:

                  newerrFile = open(self.newlogfile, 'r')
                  filesize = os.path.getsize(self.newlogfile)
                  if filesize > 200:
                    newerrFile.seek(-200,2)
                  print 'filesize:%s' % filesize
                  print  'AREADly exist  err log '
                  for row in newerrFile.readlines():
                    last_error_line=row.strip('\n')
                  print 'last error line:%s' % last_error_line
                  a.append(Metric(args.mysql_hostname, 'MySQL.%s' % self.zbx_item, '%s' % last_error_line))
                  send_to_zabbix(a, zabbix_host, zabbix_port)
                  newerrFile.close()

          else:

             a.append(Metric(args.mysql_hostname, 'MySQL.%s' % self.zbx_item, 'CMBC MYSQL OK:mysql error log is ok'))
             send_to_zabbix(a, zabbix_host, zabbix_port)




    def updateInfo(self):
        self.oldsizeinfo[self.zbx_item] = self.currentsize
        currentsizeinfostr = json.dumps(self.oldsizeinfo)
        errlogstatusFile = open(self.logfilestatusfile,'w')
        errlogstatusFile.write(currentsizeinfostr)
        errlogstatusFile.close()




class Main():
    def main(self):
            error = ErrorOut()
            a = GetMysqlStatus()
            a.check(args.port,mysqlpwd)
            a.extract()
            a.check(args.port,mysqlpwd)
            a.getResponseTime()
            a.check(args.port,mysqlpwd)
            a.getDeadlockInfo()


def send_to_zabbix(metrics, zabbix_host='127.0.0.1', zabbix_port=10051, timeout=15):
    """Send set of metrics to Zabbix server."""
    j = json.dumps
    # Zabbix has very fragile JSON parser, and we cannot use json to dump whole packet
    metrics_data = []
    for m in metrics:
        print m
        clock1 = m.clock or time.time()
        clock = m.clock or ('%d' % time.time())
        metrics_data.append(('{"host":%s,"key":%s,"value":%s,"clock":%s}') % (j(m.host), j(m.key), j(m.value), j(clock)))
    json_data = ('{"request":"sender data","data":[%s]}') % (','.join(metrics_data))
    data_len = struct.pack('<Q', len(json_data))
    packet = 'ZBXD\1' + data_len + json_data
    try:
        zabbix = socket.socket()
        zabbix.connect((zabbix_host, zabbix_port))
        zabbix.settimeout(timeout)
        # send metrics to zabbix
        zabbix.sendall(packet)
        # get response header from zabbix
        #resp_hdr = _recv_all(zabbix, 13)
        resp_hdr = zabbix.recv(13)
        if not resp_hdr.startswith('ZBXD') or len(resp_hdr) != 5:
            logger.error('Wrong zabbix response')
            return False
        return True
    except socket.timeout, e:
        logger.error("zabbix timeout: " + str(e))
        return False
    except Exception, e:
        logger.exception('Error while sending data to Zabbix: ' + str(e))
        return False
    finally:
        zabbix.close()

def writeLog(filename, op_mode, message,logcleartime=86400):
    clear_logfile_before_time=logcleartime
    HisLogNeedDelChecktime=3600
    HisLogNeedDelCheckItem='HisLogNeedDelCheckItem'
    timestr=time.strftime('%Y%m%d_%H',time.localtime())
    timesplitfilename=filename + '_' + timestr
    if not  os.path.exists(timesplitfilename):
        try:
           os.mknod(timesplitfilename)
        except Exception, e:
           logger.exception('Can not create file: %s ' % filename  + str(e))
           sys.exit(1)
    try:
        filehandler = open(timesplitfilename,op_mode)
        writedatefrm = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime())
        message = writedatefrm + ' ' + message
        filehandler.write(message)
        filehandler.close()
    except Exception, e:
        logger.exception('Can not write to file: %s ' % filename  + str(e))
        sys.exit(1)

    '''delete history logfile '''
    try:
        if_checktime_reach=Check_item_looptime_reach(gl_item_checked_lasttime_status,HisLogNeedDelCheckItem,HisLogNeedDelChecktime)
        if if_checktime_reach == 1:
            logfilepath=os.path.dirname(timesplitfilename)
            logfilebasename=os.path.basename(filename)
            for logfile in os.listdir(logfilepath):
                if logfile.find(logfilebasename +'_') != -1:
                    history_logfile_name=logfilepath + '/' + logfile
                    hislogfilemodifytime=int(os.path.getmtime(history_logfile_name))
                    current_timestamp=int(time.time())
                    difftime=current_timestamp - hislogfilemodifytime

                    if difftime >= clear_logfile_before_time:
                        if  os.path.isfile(history_logfile_name):
                            os.remove(history_logfile_name)


    except Exception, e:
        logger.exception('Can not delete log file: %s ' % filename  + str(e))
        sys.exit(1)




def ReadFile(filename):
    try:
        filehandler = open(filename,'r')
        filebuffer = []
        for row in filehandler.readlines():
           print row
           filebuffer.append(row)
        filehandler.close()
        print 'filebuffer:%s' % str(filebuffer)
        return filebuffer
    except Exception, e:
        logger.exception('Can not read from file: %s ' % filename  + str(e))
        sys.exit(1)

def WriteFile(filename, op_mode, message):
    print 'filename:%s' % filename
    if not  os.path.exists(filename):
        try:
           os.mknod(filename)
        except Exception, e:
           logger.exception('Can not create file: %s ' % filename  + str(e))
           sys.exit(1)
    try:
        filehandler = open(filename,op_mode)
        filehandler.write(message)
        filehandler.close()
    except Exception, e:
        logger.exception('Can not write to file: %s ' % filename  + str(e))
        sys.exit(1)



def CheckScriptRunNormally(check_zbx_item,script_normal_end):
    a = []
    a.append(Metric(args.mysql_hostname, 'MySQL.%s' % check_zbx_item, '%s' % script_normal_end))
    send_to_zabbix(a, zabbix_host, zabbix_port)


def CheckProcess(pid_file):
    print pid_file
    selfpid = os.getpid()
    print selfpid
    if os.path.exists(pid_file) and os.path.getsize(pid_file) > 0:
       print ' exists file '
       pid_no = ReadFile(pid_file)
       for pid_id  in pid_no:
           process_no = pid_id

       pid_no = int(process_no)

       print 'pid_no:%s' % pid_no

       wait_count = 0

       while wait_count < 50:
         try:

          rtn = os.kill(pid_no,0)
          print 'os.kill resturn %s ' % rtn
          if rtn == None:
             time.sleep(1)
             wait_count = wait_count + 1
             logger.info("the last runing is  not finished  ")
          else:
             WriteFile(pid_file,'w',str(selfpid))
             break
         except Exception, e:
             WriteFile(pid_file,'w',str(selfpid))
             logger.exception('Can not kill pid: %s ' % pid_no  + str(e))
             break

       if wait_count >= 50:
          print 'script  not  finished before last time return '
          logger.error("the last time of this scripts  runing is  not finished ,this time exit ")
          sys.exit(1)
    else:
       print 'selfpid:%d ' % selfpid
       WriteFile(pid_file,'w',str(selfpid))


def Check_item_looptime_reach(filename,check_item,loop_time,):

   check_if_run=1
   last_check_info={}
   if not  os.path.exists(filename):
       last_check_info[check_item]=int(time.time())
       last_check_infostr = json.dumps(last_check_info)
       last_check_file = open(filename,'w')
       last_check_file.write(last_check_infostr)
       last_check_file.close
       return check_if_run
   else:
           last_check_file = open(filename,'r')
           for row in  last_check_file.readlines():
               last_check_info = json.loads(row)
           last_check_file.close
           if last_check_info.has_key(check_item):
              lastchecktime = last_check_info[check_item]
           else:
              lastchecktime = 0

           difftime = int(time.time()) - lastchecktime

           if difftime > loop_time:
                last_check_info[check_item]=int(time.time())
                last_check_infostr = json.dumps(last_check_info)
                last_check_file = open(filename,'w')
                last_check_file.write(last_check_infostr)
                last_check_file.close
                check_if_run=1
                return check_if_run

           else:

                check_if_run=0
                return check_if_run





#logger = logging.getLogger('zbxsender')

if __name__ == "__main__":
     parser = argparse.ArgumentParser(description='Zabbix Mysql status script')
     parser.add_argument('-n','--hnm',dest='mysql_hostname',action='store',help='Mysql zabbix name',default=None)
     parser.add_argument('-p','--port',dest='port',action='store',help='Redis server port',default=6379,type=int)
     #parser.add_argument('-k','--key',dest='key',action='store',help='mysql status key',default=None)
     args = parser.parse_args()

     print args
     print args.port
     print args.mysql_hostname

     logger = logging.getLogger('zbxsender')
     mysqlpwd = 'T0Ox0IA72ohen'
     mysqluser = 'zabbix_ro'
     zabbix_host = '197.1.32.55'       # Zabbix Server IP
     zabbix_port = 10051             # Zabbix Server Port

     gl_item_checked_lasttime_status=r'/mysql/scripts/zabbix/log/.gl_item_checked_lasttime_status'

     slaveitem = ['Seconds_Behind_Master','Slave_IO_Running','Slave_SQL_Running','Exec_Master_Log_Pos' ]

     randvalue = random.randint(0,100)
     # if  not exits table, pls use below sql  for create it.
     # create database mysql_db_monitor ;use  mysql_db_monitor; create table zabbix_mon_tab ( id int , monitor_value int );
     # insert into zabbix_mon_tab values(1,1); commit;
     #getRespTimeSQL = 'set sql_log_bin=0; begin;update  mysql_db_monitor.zabbix_mon_tab set  monitor_value=%s where  id=1 ; commit;' % randvalue
     getRespTimeSQL = 'set sql_log_bin=0; begin;select 1 ; commit;'
     print getRespTimeSQL

     # when SQL query time  excess the time 'QueryTimeNeedlog' ,will be log into 'LongQueryTimeSQLLog' file

     QueryTimeNeedlog = 10

     LongQueryTimeSQLLog = r'/mysql/scripts/zabbix/log/monitor_cmd_output/longquerytimesql.log'
     global_trx_logfile=r'/mysql/scripts/zabbix/log/monitor_cmd_output/innodb_trx_logfile.log'

     pidfile = r'/tmp/zbx_mysql_status.pid'

     # Check  the check progarm runing of last time is finished
     CheckProcess(pidfile)

     #  main() using for check mysql status , including dead lock , response time , and query of long time running.
     run = Main()
     run.main()

     #  check mysql  error log
     errlogfile = r'/mysqldata/myinst1/log/error.log'
     logfilestatusfile = r'/mysql/scripts/zabbix/log/.logfile.status'
     newlogfile = r'/mysql/scripts/zabbix/log/new_mysql_error.log'
     excepruledic = [r'Forcing close of thread',r'Aborted connection',r'InnoDB: page_cleaner',r'Got an error reading communication packets',r'Access denied for user']
     errkeys = ['shutdown',r'Semi-sync replication switched OFF',r'[ERROR]',r'[Warning]',r'[Note]',r'ANYWORDS']
     zbx_item = 'Errorlog'

     logfilecheck = ErrorLogCheck(errlogfile,logfilestatusfile,newlogfile,excepruledic,errkeys,zbx_item)
     logfilecheck.parseNewlog()
     logfilecheck.updateInfo()



     # ending line using for checking if this  scripts itself is running normally. if the follow line is run, the script is runing normally
     CheckScriptRunNormally('Check_runing_status',0)



