#! /usr/bin/env python

import os,sys,string

NewName = os.path.expanduser('~')
sys.path.append('%s/verification_libs'%NewName)


import logs


import xml_regfile2_create
import regfile_axi4lite

def main():
    Fname = sys.argv[1]
    run(Fname)

def run(Fname):
    File = open(Fname)
    readFile(File)
    assignAddresses()
    Params = Db['chip'].Params['names']
    Module = Params[0] 
    Db['module']=Module
    if 'axi4lite' in Params:
        Postfix = '_ram'
    elif 'apb' in Params:
        Postfix = '_ram'
    else:
        Postfix = ''

    Db['fout'] = dumpRam(Postfix)
    Db['lines'] = LINES
    if 'axi4lite' in Params:
        dumpAxi4lite(Db)
    elif 'apb' in Params:
        dumpApb(Db)
    elif 'ram' in Params:
        Db['fout'].close()
    else:
        logs.log_error('need to specify output format:  apb ram axi4lite')
    dumpDefines()
    runXml()
#    report()
#    report2(LINES)
    return Db['module']

def report2(LINES):
    for Key in LINES:
        LL = LINES[Key]
        for Li in LL:
            logs.log_info('%s: %s'%(Key,Li))

Db = {'items':[]}
def readFile(File):
    while True:
        line = File.readline()
        if line=='': return
        wrds = string.split(line)
        if len(wrds)==0:
            pass
        elif (wrds[0]=='end'):
            generate()
        elif (wrds[0]=='chip'):
            Db['chip'] = itemClass(wrds)
        else:
            Item = itemClass(wrds)
            Db['items'].append(Item)

SYNONYMS = {'wid':'width'}

class itemClass:
    def __init__(self,Wrds):
        self.Kind = Wrds[0]
        self.Params = getParams(Wrds[1:])
        self.Synonyms()
        self.Addr = -1
        self.RAMS = ''
        self.RAMS_WIRES = ''
    def dump(self):
        print('%s : (%d 0x%x) %s'%(self.Kind,self.Addr,self.Addr,self.Params))
    def Synonyms(self):
        for Key in SYNONYMS:
            if Key in self.Params:
                Val = SYNONYMS[Key]
                if Val not in self.Params:
                    self.Params[Val] = self.Params[Key]

def expandBits(Name,Wid,Bits):
    if Wid==Bits: return Name
    if Wid<Bits:
        Line = '{%d\'b0,%s}'%(Bits-Wid,Name)
        return Line
    return 'ERROR%s'%Name

def getParams(wrds):
    Res = {}
    Nn = []
    for wrd in wrds:
        if '=' in wrd:
            ww = string.split(wrd,'=')
            try:
                AA = eval(ww[1])
            except:
                AA = ww[1]
            Res[ww[0]] = AA
        else:
            Nn.append(wrd)
    Res['names']=Nn
    return Res 


def generate():
    gatherFields()
    
def gatherFields():
    Active = False
    Acc = []
    Db['fields'] = {}
    Db['regs'] = []
    for Reg in Db['items']:
        if Reg.Kind=='reg':
            Active = Reg.Params['names'][0]
            Db['regs'].append(Reg)
        elif Reg.Kind=='field':
            Acc.append(Reg)
            if Active:
                if Active not in Db['fields']:
                    Db['fields'][Active] = [Reg]
                else:
                    Db['fields'][Active].append(Reg)
            else:
                logs.log_error('no reg for field %s'%(Reg.Params))
        else:
            Db['regs'].append(Reg)
            Active=False

def report():
    logs.mustKey(Db,'chip')
    logs.mustKey(Db,'regs')
    print(Db['chip'].Kind,Db['chip'].Params)
    for Reg in Db['regs']:
        Reg.dump()

def getPrm(Obj,Name,Default):
    if Name in Obj.Params: return Obj.Params[Name]
    return Default

def assignAddresses():
    Chip = Db['chip']
    Addr = getPrm(Chip,'base',0)
    Addr,HADDR = 0,0
    for Reg in Db['regs']:
        Reg.Addr = Addr
        if Reg.Kind in ['reg','array','ram']:
            Name= getPrm(Reg,'names',['err'])[0]
            LINES[5].append('%s = 0x%x'%(Name,Addr))
        Addr += advanceAddr(Reg)
        Reg.HADDR = Addr
    Chip.Addr = Addr
    Chip.HADDR = Addr


def computeWid(Obj):
    Wid = Obj.Params['width']
    AA = Wid/32
    Rest = Wid-(AA*32)
    if Rest>0: AA += 1
    return AA


def advanceAddr(Obj):
    if Obj.Kind=='reg':
        logs.mustKey(Obj.Params,'width')
        AA = computeWid(Obj)
        return AA*4
    elif Obj.Kind in ('array','ram'):
        Wid = Obj.Params['width']
        Dep = Obj.Params['depth']
        Num = computeWid(Obj)
        Tot = Dep*Num*4
        return Tot
    elif Obj.Kind=='gap':
        if 'align' in Obj.Params:
            Align = Obj.Params['align']
            X = int(Obj.Addr/Align)
            Diff = Obj.Addr -(X*Align)
            if Diff==0: return 0
            return (X+1)*Align - Obj.Addr
        elif 'abs' in Obj.Params:
            return Obj.Params['abs']
        else:
            logs.log_error('advanceAddr GAP got %s'%str(Obj.Params))
    else:
        logs.log_error('advanceAddr got %s'%(Obj.Kind))
        return 4

HEADER = '''module MODULE (
    input clk,input rst_n,input pwrite, input pread
    ,input [31:0] pwdata, output [31:0] prdata
    ,input [3:0] pstrb
    ,input [15:0] paddr ,output reg [31:0] last_wdata
'''

STRING0 = '''
);
wire [15:0] mpaddr = (pread||pwrite) ? ((paddr - 16'hBASE) & 16'hMASK) : 0;
wire [31:0] prdata_wire =
'''

STRING1 = '''

reg [31:0] prdata_reg;
always @(posedge clk) prdata_reg <=  prdata_wire;
assign prdata =   RAMS
   prdata_reg;

// wire [31:0] mask = (psize==1) ? 32'hff : (psize==2) ? 32'hffff :  32'hffffffff;
// wire [31:0] wdata = (psize==1) ? {4{pwdata[7:0]}} : (psize==2) ? {2{pwdata[15:0]}} :  pwdata;
wire [31:0] mask = { {8{pstrb[3]}},{8{pstrb[2]}},{8{pstrb[1]}},{8{pstrb[0]}} };
wire [31:0] wdata = pwdata;
always @(posedge clk) if (pwrite) last_wdata <= wdata & mask;
always @(posedge clk ASYNCRST) begin
    if (!rst_n) begin '''

LINES = {0:[],1:[],2:[],3:[],4:[],5:[],6:[]}
def dumpRam(Postfix=''):
    Module = Db['chip'].Params['names'][0] 
    Str = string.replace(HEADER,'MODULE',Module+Postfix)
    File = open('%s.v'%Module,'w')
    File.write(Str)
    Db['module']=Module
    bodyDump0(Db,File)
    bodyDump1(Db,File)
    return File
    


def bodyDump0(Db,File):
    for Reg in Db['regs']:
        if Reg.Kind=='reg':
            treatReg(Reg)
        elif Reg.Kind=='array':
            treatArray(Reg)
        elif Reg.Kind=='ram':
            treatRam(Reg)
        elif Reg.Kind=='gap': 
            pass
        else:
            logs.log_error('wrong kind %s'%(Reg.Kind,Reg.Params.Names))
    
    for Line in LINES[0]:
        File.write('%s\n'%Line)

def bodyDump1(Db,File):
    Base = getPrm(Db['chip'],'base',0)
    X = logs.neededBits(Db['chip'].Addr-Base)
    Mask = ((1<<X)-1) & 0xfffc
    Str = string.replace(STRING0,'MASK',hex(Mask)[2:])
    Str = string.replace(Str,'BASE',hex(Base)[2:])
    File.write('%s\n'%Str)

    for Line in LINES[1]:
        File.write('%s\n'%Line)
    File.write("    32'hx;\n")
    Str = Db['chip'].RAMS_WIRES + '\n' + string.replace(STRING1,'RAMS',Db['chip'].RAMS)
    RST = getPrm(Db['chip'],'reset','async')
    if RST=='async':
        Str = string.replace(Str,'ASYNCRST','or negedge rst_n')
    else:
        Str = string.replace(Str,'ASYNCRST','')
    File.write('%s\n'%Str)
    for Line in LINES[2]:
        File.write('%s\n'%Line)

    File.write('    end else if (pwrite)  begin\n')
    for Line in LINES[3]:
        File.write('%s\n'%Line)

    File.write('    end\n')
    File.write('end\n')

    for Line in LINES[4]:
        File.write('%s\n'%Line)

    File.write('endmodule\n')

ROPULSE = '''
wire REG_rd_sel = pread && (mpaddr=='hADDR);
reg REG_rd_pulse_reg; always @(posedge clk)  REG_rd_pulse_reg <= REG_rd_sel;
assign REG_pulse = REG_rd_pulse_reg;
'''
RWPULSE = '''
wire REG_wr_sel = pwrite && (mpaddr=='hADDR);
reg REG_wr_pulse_reg; always @(posedge clk)  REG_wr_pulse_reg <= REG_wr_sel;
assign REG_pulse = REG_wr_pulse_reg;
'''

RAM_ROPULSE_RANGE = '''
assign REG_rd_pulse = pread && (mpaddr>='hLADDR) && (mpaddr < 'hHADDR);
reg REG_rd_pulse_dly; always @(posedge clk)  REG_rd_pulse_dly <= REG_rd_pulse;
assign REG_rd_data_valid = REG_rd_pulse_dly;
'''

ROPULSE_RANGE = '''
wire REG_rd_sel = pread &&  (mpaddr>='hLADDR) && (mpaddr < 'hHADDR);
reg REG_rd_pulse_reg; always @(posedge clk)  REG_rd_pulse_reg <= REG_rd_sel;
assign REG_rd_pulse = REG_rd_pulse_reg;
'''

RWPULSE_RANGE = '''
wire REG_wr_sel = pwrite && (mpaddr>='hLADDR) && (mpaddr < 'hHADDR);
reg REG_wr_pulse_reg; always @(posedge clk)  REG_wr_pulse_reg <= REG_wr_sel;
assign REG_wr_pulse = REG_wr_pulse_reg;
'''



def treatReg(Reg):
    Access= getPrm(Reg,'access','rw')
    Wid= getPrm(Reg,'width',32)
    Reset= getPrm(Reg,'reset',0)
    Name= getPrm(Reg,'names',['err'])[0]
    if 'ro' in Access:
        Line = '    ,input [%d:0] %s'%(Wid-1,Name)
        LINES[0].append(Line)
        if 'pulse' in Access:
            lastAddr = Reg.Addr
            Wid2 = Wid
            while Wid2>32:
                lastAddr += 4
                Wid2 -= 32
            Line = '    ,output %s_pulse'%(Name)
            LINES[0].append(Line)
            Str = string.replace(ROPULSE,'REG',Name)
            Str = string.replace(Str,'ADDR',hex(lastAddr)[2:])
            LINES[4].append(Str)

        if (Wid<32):
            Line = '    (mpaddr == \'h%x) ? %s :'%(Reg.Addr,expandBits(Name,Wid,32))
            LINES[1].append(Line)
        else:
            Wid1 = Wid
            Ad = Reg.Addr
            Hi,Lo = 31,0
            while Wid1>0:
                Line = '    (mpaddr == \'h%x) ? %s[%d:%d] :'%(Ad,expandBits(Name,min(Wid1,32),32),Hi,Lo)
                Wid1 -= 32
                Ad += 4
                Lo += 32
                Hi = min(Wid-1,Hi+32)
                LINES[1].append(Line)

            
    elif 'rw' in Access:
        Line = '    ,output reg [%d:0] %s'%(Wid-1,Name)
        LINES[0].append(Line)
        lastAddr = Reg.Addr
        Wid2 = Wid
        while Wid2>32:
            lastAddr += 4
            Wid2 -= 32
        if 'pulse' in Access:
            Line = '    ,output %s_pulse'%(Name)
            LINES[0].append(Line)
            Str = string.replace(RWPULSE,'REG',Name)
            Str = string.replace(Str,'ADDR',hex(lastAddr)[2:])
            LINES[4].append(Str)
        if Wid<=32:
            Line = '    (mpaddr == \'h%x) ? %s :'%(Reg.Addr,expandBits(Name,Wid,32))
            LINES[1].append(Line)
            Line = '        if (mpaddr == \'h%x) %s <= (%s & ~mask) | (wdata & mask);'%(Reg.Addr,Name,Name)
            LINES[3].append(Line)
        else:
            Wid1 = Wid
            Ad = Reg.Addr
            Hi,Lo = 31,0
            while Wid1>0:
                Line = '    (mpaddr == \'h%x) ? %s[%d:%d] :'%(Ad,expandBits(Name,min(Wid1,32),32),Hi,Lo)
                LINES[1].append(Line)
                Line = '        if (mpaddr == \'h%x) %s[%d:%d] <= (%s[%d:%d] & ~mask) | (wdata & mask);'%(Ad,Name,Hi,Lo,Name,Hi,Lo)
                LINES[3].append(Line)
                Ad += 4
                Lo += 32
                Wid1 -= 32
                Hi = min(Wid-1,Hi+32)


        Line = '        %s <= %d\'h%x;'%(Name,Wid,Reset)
        LINES[2].append(Line)

    elif 'external' in Access:
        Line = '    ,input [%d:0] %s'%(Wid-1,Name)
        LINES[0].append(Line)
        Line = '    ,output %s_rd_pulse'%(Name)
        LINES[0].append(Line)
        Line = '    ,output %s_wr_pulse'%(Name)
        LINES[0].append(Line)
        Str = string.replace(ROPULSE,'assign REG','assign %s_rd'%Name)
        Str = string.replace(Str,'REG',Name)
        Str = string.replace(Str,'ADDR',hex(Reg.Addr)[2:])
        LINES[4].append(Str)
        Str = string.replace(RWPULSE,'assign REG','assign %s_rd'%Name)
        Str = string.replace(Str,'REG',Name)
        Str = string.replace(Str,'ADDR',hex(Reg.Addr)[2:])
        LINES[4].append(Str)

def treatArray(Reg):
    Access = getPrm(Reg,'access','rw')
    Wid = getPrm(Reg,'width',32)
    Dep = getPrm(Reg,'depth',32)
    Name= getPrm(Reg,'names',['err'])[0]
    if 'external' in Access:
        Line = '    ,input [%d:0] [%d:0] %s'%(Dep-1,Wid-1,Name)
        LINES[0].append(Line)
        Line = '    ,output %s_rd_pulse'%(Name)
        LINES[0].append(Line)
        Line = '    ,output %s_wr_pulse'%(Name)
        LINES[0].append(Line)
        Line = '    ,output [%d:0] %s_addr'%(logs.neededBits(Dep)-1,Name)
        LINES[0].append(Line)

        Str = string.replace(ROPULSE_RANGE,'REG',Name)
        Str = string.replace(Str,'LADDR',hex(Reg.Addr)[2:])
        Str = string.replace(Str,'HADDR',hex(Reg.HADDR)[2:])
        LINES[4].append(Str)
        Str = string.replace(RWPULSE_RANGE,'REG',Name)
        Str = string.replace(Str,'LADDR',hex(Reg.Addr)[2:])
        Str = string.replace(Str,'HADDR',hex(Reg.HADDR)[2:])
        LINES[4].append(Str)

    elif ('wr' in Access)or('rw' in Access):
        Line = '    ,output reg [%d:0] [%d:0] %s'%(Dep-1,Wid-1,Name)
        LINES[0].append(Line)
        Ad = Reg.Addr
        for Ind in range(Dep):
            Line = '    (mpaddr == \'h%x) ? %s :'%(Ad,expandBits(Name+'[%d]'%Ind,Wid,32))
            Ad += 4
            LINES[1].append(Line)


        Line = '        %s <= %d\'h%x;'%(Name,Wid,Reset)
        LINES[2].append(Line)

    elif ('ro' in Access):
        Line = '    ,input [%d:0] [%d:0] %s'%(Dep-1,Wid-1,Name)
        LINES[0].append(Line)
        Ad = Reg.Addr
        for Ind in range(Dep):
            Line = '    (mpaddr == \'h%x) ? %s :'%(Ad,expandBits(Name+'[%d]'%Ind,Wid,32))
            Ad += 4
            LINES[1].append(Line)
    return

def treatRam(Reg):
    Access = getPrm(Reg,'access','rw')
    Wid = getPrm(Reg,'width',32)
    Dep = getPrm(Reg,'depth',32)
    Name= getPrm(Reg,'names',['err'])[0]
    Line = '    ,input [%d:0] %s_rdata'%(Wid-1,Name)
    LINES[0].append(Line)
    Line = '    ,output [%d:0] %s_addr'%(logs.neededBits(Dep-1),Name)
    LINES[0].append(Line)
    Line = '    ,output %s_rd_pulse'%(Name)
    LINES[0].append(Line)
    Line = '    ,output %s_wr_pulse'%(Name)
    LINES[0].append(Line)

    Line = 'assign %s_addr = (mpaddr - \'h%x)>>2;'%(Name,Reg.Addr)
    LINES[4].append(Line)
    Str = string.replace(RAM_ROPULSE_RANGE,'REG',Name)
    Str = string.replace(Str,'LADDR',hex(Reg.Addr)[2:])
    Str = string.replace(Str,'HADDR',hex(Reg.HADDR)[2:])
    LINES[4].append(Str)
    Str = string.replace(RWPULSE_RANGE,'REG',Name)
    Str = string.replace(Str,'LADDR',hex(Reg.Addr)[2:])
    Str = string.replace(Str,'HADDR',hex(Reg.HADDR)[2:])
    LINES[4].append(Str)

    Line = '%s_rd_data_valid ? %s_rdata :'%(Name,Name)
    Db['chip'].RAMS += Line
    Db['chip'].RAMS_WIRES += 'wire %s_rd_data_valid;'%Name


def dumpDefines():
    Module = Db['chip'].Params['names'][0] 
    File = open('%s_defs.py'%Module,'w')
    for Line in LINES[5]:
        File.write('%s\n'%(Line))
    File.close()
    

def runXml():
    Module = Db['chip'].Params['names'][0]
    xml_regfile2_create.createXml(Module,Db)

APBHead = '''
module MODULE (input clk, input rst_n,
    input psel, input pwrite, input [3:0] pstrb, input [15:0] paddr, input [31:0] pwdata, output [31:0] prdata
    ,output pready, output pslverr
'''
APBInst = '''
MODULE rgf (.clk(clk),.rst_n(rst_n),.pwrite(i_pwrite),.pread(i_pread),.paddr(paddr)
    ,.pwdata(pwdata),.prdata(prdata)
    ,.pstrb(pstrb)
'''

APB2RAM = '''
wire i_pread = psel && !pwrite;
wire i_pwrite = psel && pwrite && penable;
assign pslverr = 0;
'''



def dumpApb(Db):
    Str = string.replace(APBHead,'MODULE',Db['module'])
    Db['fout'].write(Str)
    for Li in Db['lines'][0]:
        Li = string.replace(Li,' reg ',' ')
        Db['fout'].write(Li+'\n')
    Db['fout'].write(');\n')
    Db['fout'].write(APB2RAM)
    Str = string.replace(APBInst,'MODULE',Db['module']+'_ram')
    Db['fout'].write(Str)
    for Li in Db['lines'][0]:
        wrds = string.split(Li)
        Db['fout'].write('    ,.%s(%s)\n'%(wrds[-1],wrds[-1]))
    Db['fout'].write(');\n')
    Db['fout'].write('endmodule\n')


def dumpAxi4lite(Db):
    Str = string.replace(regfile_axi4lite.AXIHEADER,'MODULE',Db['module'])
    Db['fout'].write(Str)
    for Li in Db['lines'][0]:
        Li = string.replace(Li,' reg ',' ')
        Db['fout'].write(Li+'\n')
    Db['fout'].write(');\n')
    Db['fout'].write(regfile_axi4lite.AXISTRING2)
    Str = string.replace(APBInst,'MODULE',Db['module']+'_ram')
    Db['fout'].write(Str)
    for Li in Db['lines'][0]:
        wrds = string.split(Li)
        Db['fout'].write('    ,.%s(%s)\n'%(wrds[-1],wrds[-1]))
    Db['fout'].write(');\n')
    Db['fout'].write('endmodule\n')


if __name__ == '__main__': main()


