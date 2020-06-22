import sys, socket, json, getopt

if (sys.version_info < (3, 0)):
    print("Python 2 is not supported!")
    print("Update your system to Python 3!")
    sys.exit(1)


user = ""
fileName = ""
reportType = "spam"
spamSocket = "/var/run/bpanel/bpanel-spam-worker.sock"

def printHelp():
    print('Usage: python3 client.py --spam --user <username> --file <filepath>')
    print('\nArguments:')
    print('-u --user <username>            : Mailbox user / email address')
    print('-f --file <filepath>            : Path to the mail in the filesystem')
    print('-s --socket <filepath>          : Path to the socket in the filesystem')
    print('-S --spam                       : Report as spam (default if no --spam or --ham is defined)')
    print('-H --ham                        : Report as ham')
    print('-h --help                       : Print this help text')

def parseInputArgs():
    global user
    global fileName
    global reportType
    global spamSocket
    
    try:
        opts, args = getopt.getopt(sys.argv[1:],"s:u:f:SHh",["user=","file=","socket=","spam","ham","help"])
    except getopt.GetoptError:
        printHelp()
        sys.exit(2)

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            printHelp()
            sys.exit(0)
        elif opt in ("-u", "--user"):
            user = str(arg)
        elif opt in ("-f", "--file"):
            fileName = str(arg)
        elif opt in ("-s", "--socket"):
            if str(arg) != "":
                spamSocket = str(arg)
        elif opt in ("-S", "--spam"):
            reportType = "spam"
        elif opt in ("-H", "--ham"):
            reportType = "ham"
            
    if user == "" or fileName == "":
        printHelp()
        sys.exit(2)

def sendToSocket():
    try:
        message = '{"type": "%s", "user": "%s", "file": "%s"}' % (reportType, user, fileName)
        SpamSocket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

        SpamSocket.connect(spamSocket)
        SpamSocket.send(message.encode())
        SpamSocket.close()
    except ConnectionRefusedError:
        print("Got failure 'connection refused' while sending data to the bPanel SpamServer")
    except:
        print("Got failure while sending data to the bPanel SpamServer")

if __name__ == '__main__':
    parseInputArgs()
    sendToSocket()
