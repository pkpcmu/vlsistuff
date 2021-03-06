
USAGE = '''
import axiLiteMaster
axi = axiLiteMaster.axiLiteMaster('tb',Monitors)

axi.wait(100)
axi.makeRead(Addr0,Size=2)
axi.makeWrite(Addr1,Wdata)
axi.finish(100)

'''



import os,sys,string
import logs
import veri

class axiLiteMasterClass:
    def __init__(self,Path,Monitors):
        self.Path = Path
        Monitors.append(self)
        self.Queue=[]
        self.Queue2=[]
        self.waiting=0
        self.Translates={}
        self.Prefix = ''
        self.Defines={}
        self.Comments=[]

    def peek(self,Sig):
        if self.Prefix!='': Sig = '%s%s'%(self.Prefix,Sig)
        if Sig in self.Translates: Sig = self.Translates[Sig]
        return logs.peek('%s.%s'%(self.Path,Sig))
    def force(self,Sig,Val):
        if self.Prefix!='': Sig = '%s%s'%(self.Prefix,Sig)
        if Sig in self.Translates: Sig = self.Translates[Sig]
        veri.force('%s.%s'%(self.Path,Sig),str(Val))

    def makeRead(self,Address,Size=4,Queue=1):
        if Queue==1:
            self.Queue.append('force arvalid=1 araddr=%s'%(Address))
            self.Queue.append('force arvalid=0 araddr=0 rready=1')
            self.Comments.append('addr=%x'%Address)
        elif Queue==2:
            self.Queue2.append('force arvalid=1 araddr=%s'%(Address))
            self.Queue2.append('force arvalid=0 araddr=0 rready=1')
            self.Comments.append('addr=%x'%Address)

    def wait(self,Many):
        self.Queue.append('wait %s'%Many)
    def finish(self,Many):
        self.Queue.append('wait %s'%Many)
        self.Queue.append('finish')

    def makeWrite(self,Address,Wdata):
        self.Queue.append('force awvalid=1 awaddr=%s'%(Address))
        self.Queue.append('force awvalid=0 awaddr=0')
        self.Queue.append('force wvalid=1 wdata=%s wstrb=15 '%(Wdata))
        self.Queue.append('force wvalid=0 wdata=0 wstrb=0 bready=1')
#        logs.log_info('makeWrite addr=%x data=%x'%(Address,Wdata))

    def run(self):
        self.runResponce()
        self.runQueue2()
        if self.waiting>0:
            self.waiting -= 1
            return
        self.runQueue()

    def runResponce(self):
        if self.peek('rvalid')==1:
            self.force('rready',1)
            rdata = self.peek('rdata')
            Comm = '?'
            if self.Comments!=[]:
                Comm = self.Comments.pop(0)
            if rdata<0:
                logs.log_error('axiLiteMaster %s responce rdata=UNKNOWN'%(Comm))
            else:
                logs.log_info('axiLiteMaster %s responce rdata=%08x'%(Comm,rdata))
        else:
            self.force('rready',0)



    def runQueue2(self):
        if self.Queue2==[]: return
        Cmd = self.Queue2.pop(0)
        wrds = string.split(Cmd)
        if wrds==[]:
            pass
        elif (wrds[0]=='force'):
            for wrd in wrds[1:]:
                ww = string.split(wrd,'=')
                Var = ww[0]
                Val = self.evalit(ww[1])
                self.force(Var,Val)
        else:
            logs.log_error('runQueue2 cannot deal with "%s"'%Cmd)

    def runQueue(self):
        if self.Queue==[]: return
        Cmd = self.Queue.pop(0)
        wrds = string.split(Cmd)
        if wrds==[]:
            pass
        elif (wrds[0]=='wait'):
            self.waiting = int(wrds[1])
        elif (wrds[0]=='finish'):
            logs.log_info('veri finish from axi Master')
            veri.finish()
            sys.exit()
        elif (wrds[0]=='force'):
            for wrd in wrds[1:]:
                ww = string.split(wrd,'=')
                Var = ww[0]
                Val = self.evalit(ww[1])
                self.force(Var,Val)
        else:
            logs.log_error('runQueue cannot deal with "%s"'%Cmd)

    def evalit(self,Expr):
        try:
            Val = eval(Expr,self.Defines)
        except:
            logs.log_error('eval of "%s" failed, on %s'%(Expr,self.Defines.keys()))
            Val=0
        return Val

    def readSequence(self,Fname):
        File = open(Fname)
        while True:
            line = File.readline()
            if line=='': return
            wrds = string.split(line)
            if wrds==[]:
                pass
            elif (wrds[0][0]=='#'):
                pass
            elif (wrds[0]=='finish'):
                self.Queue.append('finish')
#                logs.log_info('queue append finish')
            elif (wrds[0]=='wait'):
                self.Queue.append(line)
            elif (wrds[0]=='include'):
                self.readSequence(wrds[1])
            elif (wrds[0]=='define'):
                Var = wrds[1]
                Val = self.evalit(wrds[2])
                self.Defines[Var]=Val
                self.Defines[string.upper(Var)]=Val
            elif (wrds[0]=='write'):
                Addr = self.evalit(wrds[1])
                Data = self.evalit(wrds[2])
                self.makeWrite(Addr,Data)
            elif (wrds[0]=='read'):
                Addr = self.evalit(wrds[1])
                self.makeRead(Addr)

                                    
