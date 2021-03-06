#! /usr/bin/python
HelpString = '''
invocation:

genver.py  <infile> [<outfile>] [... more params passed to the infile]

this script can be used for any source language, better give outfile name
if it is not verilog.


this script generates verilog code from annotated pythoned 
verilog code.
cut out the example section and run the script on it.

all lines that start with # are special lines and python
executes them.   python section ends with bare #.

for longer pure python code, use "###" line to start the section 
and "###" to end the sectio,

#< is used in de-indent  pure verilog.


#defcode CUCU  AAA BBB
wire AAA = !BBB;
#enddef

#code CUCU www aaa&bbb




enjoy,
Ilia

Example:

module tx17out (input [7:0] chipid
#for I in range(17):
#    J = I+1
  ,input [15:0] pcktinJ 
  ,output reg  availI 
  ,output reg  [15:0] chI 
#    
);

#for I in range(17):
reg [15:0] holdI;
always begin
     availI = 1;
     chI = 0;
     wait(|pcktinI);
     holdI = pcktinI;
     availI = 0;
     #(top.pool.length[holdI]);
     chI = holdI;
     #1;
end
#    

#for I in range(17):
wire [15:0] cucuI = 0
#    for J in range(17):
    || aaaJ_I
#<
  ;
#

endmodule

# this is the end of the example!!!!
'''

import os,sys,string


BigHead='# -*- encoding: UTF8 -*-\nimport os,sys,string\n'


def main():
    if len(sys.argv)==1:
        print HelpString
        return
    Fname = sys.argv[1]
    if len(sys.argv)>2:
        FnameOut = sys.argv[2]
    else:
        w1 = string.split(Fname,'/')
        w2 = string.split(w1[-1],'.')
        Top=w2[0]
        FnameOut = '%s.v'%Top
    run(Fname,FnameOut,sys.argv[3:])

def run(Fname,FnameOut,Args):
    File = open(Fname)
    lines = File.readlines()
    File.close()
    runFromLines(lines,FnameOut,Args)

def runFromLines(lines,FnameOut,Args):
    global Code0,Strings
    Code0=[]
    Strings={}
    Big = [BigHead]
    lines=extract_codelins(lines)
    lines = expand_codelins(lines)
    prepare1(lines)
    Big.append('Strings={}')
    for X in Strings:
        Big.append("Strings['%s']='''"%X)
        XX = Strings[X]
        XX = rework_backs(XX)
        Big.append(XX)
        Big.append("'''")
    Big.append(Routines)
    for X in Code0:
        Big.append(X)
    Fout = open('execme.py','w')
    for LL in Big:
        if LL[-1]!='\n': LL += '\n'
        Fout.write(LL)
    Fout.close()
    More = string.join(Args,' ')
    Work = 'python execme.py %s > %s'%(Args,FnameOut)
    os.system(Work)
#    os.system('/bin/rm  execme.py')

def rework_backs(Str):
    Str1 = string.replace(Str,'\\n','\\\\n')
    return Str1
Bags={}
def extract_codelins(lines):
    state='idle'
    Bag = []
    res = []
    for line in lines:
        if (state=='idle'):
            if '#defcode' in line:
                wrds = string.split(line)
                state='work'
                Name=wrds[1]
                Bag=[wrds]
                Bags[Name]=Bag
            else:
                res.append(line)
        elif (state=='work'):
            if '#enddef' in line:
                state='idle'
                Bag=[]
            else:
                Bag.append(line)
    return res


Routines = '''
def clog2(In):
    return len(bin(In))-2

Vars={}
import string
def formati(Var,Val):
    if len(Val)==0:
        return '<>1<>'
    if len(Var)==0:
        return '<>2<>'
    if Val[0] in '0123456789':
        if (len(Var)>1)and(Var[1] in '0123456789'):
            if Var[0]=='X':
                V1 = '%x'%int(Val)
            elif (Var[0]=='B'):
                V1 = bin(int(Val))
                V1 = V1[2:]
            elif (Var[0]=='D'):
                V1 = str(int(Val))
            else:
                return Val
            Wid = int(Var[1])
            while len(V1)<Wid:
                V1 = '0'+V1
            return V1                
    return Val


def evalStuff(Str):
    wrds = string.split(Str,'<>')
    if len(wrds)<3: return Str
    Varsi = {}
    for Var in Vars:
        Val = Vars[Var]
        try:
            Varsi[Var]=int(Val)
        except:
            pass
    for II in range(1,len(wrds),2):
        try:
            New = eval(wrds[II],{},Varsi)
            wrds[II] = str(New)
        except:
            try:
                exec("NxiX = %s"%wrds[II])
                wrds[II] = str(NxiX)
            except:
                print '// failed eval of "%s"'%(wrds[II])
    Str2 = string.join(wrds,'')
    return Str2


def print_Strings(Str):
    X = Strings[Str][:]
    X = evalStuff(X)



    if X[0]=='\\n':
        X = X[1:]
#    X = string.replace(X,'\\n\\n','\\n')
#    X = string.replace(X,'\\n\\n','\\n')
#    X = string.replace(X,'\\n\\n','\\n')
    res=[]
    for Var in Vars:
        res.append((len(Var),Var,Vars[Var]))
    res.sort()
    res.reverse()
    for _,Var,Val in res:
        X = string.replace(X,Var,formati(Var,Val))
    print X,
        


'''

def expand_codelins(lines):
    res = []
    for line in lines:
        if '#code' in line:
            more = get_code(line)
            res.extend(more)
        else:
            res.append(line)
            
    return res


def get_code(Str):
    wrds = string.split(Str)
    Name = wrds[1]
    if Name not in Bags:
        print 'name %s not in bags %s'%(Name,Bags.keys())
        return []
    Mlines = Bags[Name]
    Header =Mlines[0]
    Mlines.pop(0)
    Vars = get_code_vars(Header)
    update_code_vars(Vars,wrds)
    res=[]
    print '// >mlines>>>>',Mlines
    print '// >vars>>>>',Vars
    for line in Mlines:
        for Var in Vars:
            line = string.replace(line,Var,Vars[Var])
        res.append(line)
    return res

def get_code_vars(Header):
    Vars={}
    for Var in Header:
        if '=' in Var:
            ww =string.split(Var,'=')
            Vars[ww[0]]=ww[1]
        else:
            Vars[Var]=''
    return Vars

def update_code_vars(Vars,wrds):
    for wrd in wrds:
        if ('=' in wrd):
            ww =string.split(wrd,'=')
            Vars[ww[0]]=ww[1]
    return Vars





def prepare1(lines):
    global Indent,Lnum
    state='idle'
    Str = ''
    Indent=''
    Lnum=0
    for line in lines:
        Lnum += 1
        if (state=='idle'):
            if (len(line)>3)and(line[0:3]=='###'):
                state='longcode'
                if (Str!=''):
                    Sname = strname()
                    Strings[Sname]=Str
                    Str=''
                    Code0.append("print_Strings('%s')\n"%Sname)
            elif (len(line)>0)and(line[0]=='#'):
                if (Str!=''):
                    Sname = strname()
                    Strings[Sname]=Str
                    Str=''
                    Code0.append("print_Strings('%s')\n"%Sname)
                Code0.append(line[1:])
                Indent = calc_indent(line[1:])
                seek_vars(line[1:])
                state='code'
            else:
                Str = Str + line
        elif (state=='longcode'):
            if (len(line)>3)and(line[0:3]=='###'):
                state='idle'
            else:
                Code0.append(line)
                Indent = calc_indent(line)
                seek_vars(line)
        elif (state=='code'):
            wrds = string.split(line)
            if (len(line)>0)and(line[0]=='#')and(Str!=''):
                Sname = strname()
                Strings[Sname]=Str
                Str=''
                Code0.append("%sprint_Strings('%s')\n"%(Indent,Sname))
                
            if (len(line)>0)and(len(wrds)>0)and(wrds[0]=='#')and(len(wrds)==1):
                state='idle'
#                Code0.append('Vars={}')    
                Indent=''
            elif (len(line)>2)and(line[:2]=='#<'):
                Indent = Indent[4:]
                state='code'
            elif (len(line)>0)and(line[0]=='#'):
                Code0.append(line[1:])
                Indent = calc_indent(line[1:])
                seek_vars(line[1:])
            else:
                state='string'
                Str = Str + line
        elif (state=='string'):
            wrds = string.split(line)
            if (len(line)>0)and(line[0]=='#')and(Str!=''):
                Sname = strname()
                Strings[Sname]=Str
                Str=''
                Code0.append("%sprint_Strings('%s')\n"%(Indent,Sname))
                state='code'
                
            if (len(line)>2)and(line[:2]=='#<'):
                Indent = Indent[4:]
                state='code'
            elif (len(line)>0)and(line[0]=='#')and(len(wrds)==1)and(len(wrds[0])==1):
                state='idle'
#                Code0.append('Vars={}')    
                Indent=''
            elif (len(line)>0)and(line[0]=='#'):
                Code0.append(line[1:])
                Indent = calc_indent(line[1:])
                seek_vars(line[1:])
                state='code'
            else:
                state='string'
                Str = Str + line





    if (Str!=''):
        Sname = strname()
        Strings[Sname]=Str
        Str=''
        Code0.append("print_Strings('%s')\n"%Sname)
        

def seek_vars(line):
    wrds = string.split(line)
    if len(wrds)<3:
        pass
    elif wrds[0]=='for':
        Wrd = wrds[1]
        if ',' in Wrd:
            Wrds = string.split(Wrd,',')
            for Var in Wrds:
                Code0.append('%sVars["%s"]=str(%s)\n'%(Indent,Var,Var))    
        else:
            Code0.append('%sVars["%s"]=str(%s)\n'%(Indent,wrds[1],wrds[1]))    
    elif wrds[1]=='=':
        if ',' not in wrds[0]:
            Code0.append('%sVars["%s"]=str(%s)\n'%(Indent,wrds[0],wrds[0]))    
        else:        
            ww = string.split(wrds[0],',')
            for ww0 in ww:
                Code0.append('%sVars["%s"]=str(%s)\n'%(Indent,ww0,ww0))    

def calc_indent(line):
    wrds = string.split(line)    
    if len(wrds)==0:
        print 'lnum=%d in file, fatal ident, aborting. '%(Lnum)
        sys.exit()
        
    ind = line.index(wrds[0])
    if wrds[0] in ['for','if','else:','elif']:
        ind += 4
    return ' '*ind
      
                
StrNum = 0
def strname():
    global StrNum
    N = 'str%d'%StrNum
    StrNum += 1
    return N
    


if (__name__ == '__main__'): main()
