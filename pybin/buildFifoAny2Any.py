#! /usr/bin/python

import os,sys,string

HELPSTRING = '''
invocation:     buildFifo.py  <Writes> <Reads>  < -prefix PREFIX >
this script builds RTL of a multi_sync_fifo with optional number of concurrent writes.
and Depth being number of fifo entries.
<Writes> is the number of concurrent writes
<Reads> is the number of concurrent reads

'''


def main():
    try:
        Writes = int(sys.argv[1])
        Reads = int(sys.argv[2])
    except:
        print HELPSTRING
        return

    Prefix = ''
    if '-prefix' in sys.argv:
        Ind = sys.argv.index('-prefix')
        Prefix = sys.argv[Ind+1]


    buildFifo(Writes,Reads,Prefix)

def buildFifo(Writes,Reads,Prefix=''):
    Fname = '%smultififo_w%d_r%d.v'%(Prefix,Writes,Reads)
    Fout = open(Fname,'w')
    Str = STRING0
    Str = string.replace(Str,'WRITES',str(Writes))
    Str = string.replace(Str,'READS',str(Reads))
    Str = string.replace(Str,'multififo','%smultififo'%Prefix)
    Wx = bitsFor(Writes)-1
    if Wx==0: WWID = ''
    else: WWID = '[%d:0]'%Wx
    Rx = bitsFor(Reads)-1
    if Rx==0: RWID = ''
    else: RWID = '[%d:0]'%Rx

    Str = string.replace(Str,'WWID',WWID)
    Str = string.replace(Str,'RWID',RWID)
    TXT=''
    Wrts = []
    TEXTWRITE2 = '        if (oktowrite && (writes >= 1))  fifos[wptr] <= din[WIDTH-1:0];\n'
    for II in range(2,Writes+1):
        TEXTWRITE2 += '        if (oktowrite && (writes >= %d)) fifos[wptr%d] <= din[%d*WIDTH-1:%d*WIDTH];\n'%(II,II-1,II,II-1)
    Str = string.replace(Str,'TEXTWRITE0',TXT)

    TEXTWRITE3 = ''
    for II in range(1,Writes):
        TEXTWRITE3 += 'wire [WIDPTR:0] wptr%d = ((wptr+%d)>=DEPTH) ? ((wptr+%d)-DEPTH) : (wptr+%d);\n'%(II,II,II,II)
    TEXTWRITE3 += 'wire [WIDPTR:0] rptr0 = rptr;\n'
    for II in range(1,Reads):
        TEXTWRITE3 += 'wire [WIDPTR:0] rptr%d = ((rptr+%d)>=DEPTH) ? ((rptr+%d)-DEPTH) : (rptr+%d);\n'%(II,II,II,II)

    for II in range(1,Reads+1):
        TEXTWRITE3 += 'assign dout[WIDTH*%d-1:WIDTH*%d] = (count>=%d) ? fifos[rptr%d] : 0;\n'%(II,II-1,II,II-1)

    Str = string.replace(Str,'TEXTWRITE2',TEXTWRITE2)
    Str = string.replace(Str,'TEXTWRITE3',TEXTWRITE3)

    Fout.write(Str)
    Str =  INSTSTRING
    Str = string.replace(Str,'WRITES',str(Writes))
    Str = string.replace(Str,'READS',str(Reads))
    Fout.write(Str)
    Fout.write(');\n*/\n')
    Fout.close()
    


def bitsFor(Num):
    Int = int(Num)
    Bits = len(bin(Int))-2
    return Bits

SIMPLECOUNT = 'assign   count = (wptr >= rptr) ? (wptr - rptr) :  (((2 * DEPTH) - rptr) + wptr);'

INSTSTRING = '''
/*
multififo_wWRITES_rREADS #(32) fifo (.clk(clk),.rst_n(rst_n),.softreset(softreset)
    .reads(reads),.dout(dout)
    .writes(writes),.din(din)
    ,.full(full)
    ,.empty(empty)
    ,.count(count[COUNT:0])
    ,.overflow(overflow)
    ,.taken(taken)
'''

STRING0 = '''
module multififo_wWRITES_rREADS #(parameter WIDTH=32,parameter DEPTH=8) (input clk,input rst_n,input softreset
    ,input  WWID writes
    ,input  RWID reads
    ,input  [WIDTH*WRITES-1:0]  din
    ,output [WIDTH*READS-1:0]  dout
    ,output empty, output full, output taken
    ,output reg [15:0] count
    ,output overflow
);

reg [DEPTH-1:0] [WIDTH-1:0] fifos;
localparam WIDPTR = $clog2(DEPTH);
reg [WIDPTR:0] wptr,rptr;
wire oktowrite = (writes+count)<=DEPTH;
wire oktoread = (reads<=count);
assign taken = oktowrite;
assign overflow = !oktowrite && (writes>0);
assign   empty = count == 0;
assign   full = count == DEPTH;
TEXTWRITE3
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        fifos <= 0;
    end else if (oktowrite) begin
TEXTWRITE2
    end
end
wire [WIDPTR:0] nextwptr =  ((wptr+writes)>=DEPTH) ? ((wptr+writes)-DEPTH) : (wptr+writes);
wire [WIDPTR:0] nextrptr =  ((rptr+reads)>=DEPTH) ? ((rptr+reads)-DEPTH) : (rptr+reads);
always @(posedge clk or negedge rst_n) begin
    if(!rst_n) begin
        wptr <= 0; rptr <= 0; count<=0;
    end else if(softreset) begin
        wptr <= 0; rptr <= 0; count<=0;
    end else begin
        if(oktowrite) begin
            wptr <= nextwptr;
        end 
        if(oktoread) begin
            rptr <= nextrptr;
        end 
        count <= (oktowrite && oktoread) ? (count + writes -reads) : 
                 (oktowrite) ? (count+ writes) : 
                 (oktoread) ? (count - reads) : 
                 count;
    end 
end
endmodule
'''

main()

