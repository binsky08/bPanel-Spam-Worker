import sys

if (sys.version_info < (3, 0)):
    print("Python 2 is not supported!")
    print("Update your system to Python 3!")
    sys.exit(1)

import socket, os, time, signal, json, getopt
import subprocess
from threading import Thread, Lock
from _thread import start_new_thread as listen_spam_thread
from _thread import start_new_thread as sa_worker_thread

verbose = False
thread_stop_requested = False
listen_spam_thread_running = False
sa_worker_thread_running = False
enableCache = True
cacheFolder = "/opt/bpanel/spamWorker"
spamSocket = "/var/run/bpanel/bpanel-spam-worker.sock"
listAccessLock = Lock()
workerList = []

def openFakeClientSocket():
    message = '{"type": "ignore", "user": "", "file": ""}'
    FakeClientSocket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    FakeClientSocket.connect(spamSocket)
    FakeClientSocket.send(message.encode())
    FakeClientSocket.close()

def signal_handler(sig, frame):
    """A custom signal handler to stop the service if it is called"""
    global thread_stop_requested
    global listen_spam_thread_running
    global sa_worker_thread_running
    
    if verbose:
        print("\nWait for tasks to finish ...")
    thread_stop_requested = True
    openFakeClientSocket()
    retries = 0
    while thread_stop_requested:
        if retries == 8:
            if sa_worker_thread_running:
                sa_worker_thread_running = False
            if listen_spam_thread_running:
                listen_spam_thread_running = False
        
        if sa_worker_thread_running or listen_spam_thread_running:
            time.sleep(1)
        else:
            thread_stop_requested = False
        retries += 1
    if verbose:
        print("... see you!")
    sys.exit(0)

def loadWorkerListCache():
    global workerList

    if enableCache and os.path.exists(cacheFolder + "/workerList.cache"):
        with listAccessLock:
            with open(cacheFolder + "/workerList.cache", 'r') as f:
                try:
                    rawWorkerList = f.read()
                    if rawWorkerList != "":
                        workerList = json.loads(rawWorkerList)
                except:
                    if verbose:
                        print("Failure while reading/loading cached worker list")
            with open(cacheFolder + "/workerList.cache", 'w+') as f:
                f.write('')
            
def saveWorkerListCache():
    if enableCache:
        with listAccessLock:
            if len(workerList) > 0:
                with open(cacheFolder + "/workerList.cache", 'w+') as f:
                    f.write(json.dumps(workerList))

def saWorker():
    global sa_worker_thread_running
    global listAccessLock
    global workerList
    
    sa_worker_thread_running = True
    while not thread_stop_requested:
        wlength = 0
        with listAccessLock:
            wlength = len(workerList)
        if wlength > 0:
            lastElement = None
            with listAccessLock:
                lastElement = workerList.pop(0)
                if verbose:
                    print("Last processed element: ", lastElement)
            if lastElement is not None:
                reportType = 'spam'
                if lastElement['reportType'] == 'ham':
                    reportType = 'ham'
                saLearnCommand = 'sa-learn --%s --username=%s %s' % (reportType, lastElement['user'], lastElement['fileName'])
                p = subprocess.Popen(saLearnCommand, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                
                try:
                    stdout, stderr = p.communicate(timeout=45)
                    p.poll()
                except subprocess.TimeoutExpired:
                    if verbose:
                        print('sa-learn command timed out after 45 seconds')
                    p.kill()    #not needed; just to be sure
        time.sleep(1)
        
    saveWorkerListCache()
    sa_worker_thread_running = False

def addToSAWorkerList(reportType, user, fileName):
    global listAccessLock
    global workerList
    
    with listAccessLock:
        workerList.append({
            'reportType': reportType,
            'user': user,
            'fileName': fileName
        })

def onNewClient(clientSocket, addr):
    receivedData = clientSocket.recv(1024)
    if verbose:
        print("Received: ", receivedData)
    empty = ''.encode()
    if receivedData is not None and receivedData != empty:
        try:
            data = json.loads(receivedData.decode('utf-8'))
            if 'type' in data and data['type'] != 'ignore' and 'user' in data and 'file' in data:
                addToSAWorkerList(data['type'], data['user'], data['file'])
        except:
            if verbose:
                print("Got wrong formatted message: ", receivedData)
    
def spamListener():
    global listen_spam_thread_running
    
    listen_spam_thread_running = True
    SpamSocket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        os.remove(spamSocket)
    except OSError:
        pass
    SpamSocket.bind(spamSocket)
    SpamSocket.listen(1)
    
    while not thread_stop_requested:
        try:
            socketConnection, addr = SpamSocket.accept()
            Thread(target=onNewClient, args=(socketConnection, addr),).start()
        except:
            if verbose:
                print("Failure while accepting new socket connection")
    try:
        SpamSocket.close()
    except:
        if verbose:
            print("Failure while closing socket connection")
    listen_spam_thread_running = False

def printHelp():
    print('Usage: python3 bPanelSpamWorkerServer.py')
    print('\nArguments:')
    print('-s --socket <filepath>          : Path to the socket in the filesystem')
    print('-c --cache-folder <filepath>    : Path to the cache folder in the filesystem')
    print('-n --no-cache                   : Disable persistent filesystem cache (not recommended!)')
    print('-v --verbose                    : Enable server status messages (use only for debugging!)')
    print('-h --help                       : Print this help text')

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        opts, args = getopt.getopt(sys.argv[1:],"hvnc:s:",["socket=","cache-folder=","no-cache","verbose","help"])
    except getopt.GetoptError:
        printHelp()
        sys.exit(2)
        
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            printHelp()
            sys.exit(0)
        elif opt in ("-s", "--socket"):
            if str(arg) != "":
                spamSocket = str(arg)
        elif opt in ("-c", "--cache-folder"):
            if str(arg) != "":
                cacheFolder = str(arg)
        elif opt in ("-n", "--no-cache"):
            enableCache = False
        elif opt in ("-v", "--verbose"):
            verbose = True
    
    if enableCache and not os.access(cacheFolder, os.W_OK):
        print("Cache folder not found or not writeable!")
        print("Please run: mkdir -p", cacheFolder, "&& chown www-data", cacheFolder)
        sys.exit(1)

    sockDir = os.path.dirname(spamSocket)
    if not os.path.exists(sockDir) or not os.access(sockDir, os.W_OK):
        try:
            os.makedirs(sockDir)
        except PermissionError:
            print("Got permission error while trying to create", sockDir)
        if not os.path.exists(sockDir) or not os.access(sockDir, os.W_OK):
            print("Socket folder not found or not writeable!")
            print("Please run: mkdir -p", sockDir, "&& chown www-data", sockDir)
            sys.exit(1)

    loadWorkerListCache()
    listen_spam_thread(spamListener, ())
    sa_worker_thread(saWorker, ())
    
    try:
        while True:
            signal.pause()
    except AttributeError:
        # if signal.pause() is missing, wait 1ms and loop instead
        while True:
            time.sleep(0.1)
