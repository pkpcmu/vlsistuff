

import os,sys,string,random
import veri

def intx(Text):
    if ('z' in Text)or('x' in Text):
        return -1
    return int(Text,2)

cycles=0
def negedge():
    global cycles
    cycles += 1
    veri.force('tb.cycles',str(cycles))
    if (cycles>1000):
        veri.finish()
    rst_n = veri.peek('tb.rst_n')
    if (rst_n!='1'):
        return

def cucu():
    veri.force('tb.paddr','0')
    veri.force('tb.psel','0')
    veri.force('tb.psize','0')
    veri.force('tb.pwdata','0')
    veri.force('tb.pwrite','0')
    enables = intx(veri.peek('tb.enables'))
    gain0 = intx(veri.peek('tb.gain0'))
    gain1 = intx(veri.peek('tb.gain1'))
    jump0 = intx(veri.peek('tb.jump0'))
    jump1 = intx(veri.peek('tb.jump1'))
    jump2 = intx(veri.peek('tb.jump2'))
    prdata = intx(veri.peek('tb.prdata'))
    start0 = intx(veri.peek('tb.start0'))
    start1 = intx(veri.peek('tb.start1'))
    start2 = intx(veri.peek('tb.start2'))
