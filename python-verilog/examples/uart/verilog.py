

import os,sys,string,random
sys.path.append('../vlibs')
import veri
import logs
import uartx2
logs.MAXWRONGS = 100

TEST_LENGTH = 100

PERCENT = 6.00     # will make a lot of wrongs
PERCENT = 3.0     # will pass

BAUD0 = 150
BAUD1 = BAUD0 + int(PERCENT*BAUD0/100.0) + 1
cycles=0
uartmodel = uartx2.uartx2Class('tb.uart1')
uartaluka = uartx2.uartx2Class('tb.uart0',True)
def negedge():
    global cycles
    cycles += 1
    veri.force('tb.cycles',str(cycles))
    if (cycles>1000000):    # guard 
        veri.finish()
    uartmodel.run()
    uartaluka.run()

    rst_n = veri.peek('tb.rst_n')
    if (rst_n!='1'):
        veri.force('tb.baudrate0',str(BAUD0))
        veri.force('tb.baudrate1',str(BAUD1))
        return

    drive_tx()
    monitor_rx()
    loopback()

# check that what was sent, actually arrived back.
scoreboard=[]

pauseBetweenTxs=0
def drive_tx():
    global pauseBetweenTxs
    if pauseBetweenTxs:
        pauseBetweenTxs -= 1
        veri.force('tb.write_tx0','0')
        return
    tx_empty = logs.peek('tb.tx_empty0')
    if tx_empty==1:
        fdata = random.randint(0,255)
        veri.force('tb.txdata0',str(fdata))
        veri.force('tb.write_tx0','1')
        pauseBetweenTxs=10
        scoreboard.append(fdata)
    else:
        veri.force('tb.write_tx0','0')
        pauseBetweenTxs=10

arrivedCharacters = 0
def monitor_rx():
    global arrivedCharacters
    if veri.peek('tb.rx_valid0')=='1':
        fdata = logs.peek('tb.rxdata0')
        if scoreboard==[]:
            logs.log_wrong('character arrived unexpectedly (%x)'%fdata)
        else:
            Expected = scoreboard.pop(0)
            if Expected==fdata:
                logs.log_correct('character arrived correctly (%x)'%fdata)
            else:
                logs.log_wrong('character arrived uncorrectly exp=%02x    act=%02x '%(Expected,fdata))
                

        arrivedCharacters += 1
        if arrivedCharacters>=TEST_LENGTH:
            logs.finish()
        veri.force('tb.read_rx0','1')
    else:
        veri.force('tb.read_rx0','0')



def loopback():
    if veri.peek('tb.rx_valid1')=='1':
        veri.force('tb.read_rx1','1')
        fdata = veri.peek('tb.rxdata1')
        veri.force('tb.txdata1','0b'+fdata)
        veri.force('tb.write_tx1','1')
    else:
        veri.force('tb.write_tx1','0')
        veri.force('tb.read_rx1','0')


