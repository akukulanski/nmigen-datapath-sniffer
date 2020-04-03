from nmigen_cocotb import run
from nmigen_datapath_sniffer.datapath_sniffer import DatapathSniffer
import pytest
import random
from math import ceil

try:
    import cocotb
    from cocotb.triggers import RisingEdge
    from cocotb.clock import Clock
    from cocotb.regression import TestFactory as TF
    from cores_nmigen.test.interfaces import *
except:
    pass

AXI_CLK_PERIOD = 25
DATA_CLK_PERIOD = 10

FIFO_DEPTH = 4
CORE_ID = 0x12345678

_COUNT_RST = (1 << 0)
_COUNT_EN = (1 << 1)
_FIFO_EN = (1 << 2)

random.seed()

def subfinder(mylist, pat): 
    return True if [pat for i in range(len(mylist)) if mylist[i:i+len(pat)] == pat] else False


@cocotb.coroutine
def init_test(dut):
    dut.core_id <= CORE_ID
    dut.input_data <= 0
    dut.input_we <= 0
    dut.data_rst <= 1
    dut.axi_rst <= 1
    cocotb.fork(Clock(dut.axi_clk, AXI_CLK_PERIOD, 'ns').start())
    cocotb.fork(Clock(dut.data_clk, DATA_CLK_PERIOD, 'ns').start())
    yield RisingEdge(dut.data_clk)
    yield RisingEdge(dut.data_clk)
    yield RisingEdge(dut.axi_clk)
    yield RisingEdge(dut.axi_clk)
    dut.axi_rst <= 0
    dut.data_rst <= 0
    yield RisingEdge(dut.axi_clk)
    yield RisingEdge(dut.data_clk)
    yield RisingEdge(dut.axi_clk)
    yield RisingEdge(dut.data_clk)


@cocotb.coroutine
def random_driver(dut, n):
    while n > 0:
        valid = random.randint(0, 1)
        dut.input_data <= random.randint(0, 2**len(dut.input_data)-1)
        dut.input_we <= valid
        if valid:
            n = n - 1
        yield RisingEdge(dut.data_clk)
    dut.input_we <= 0
    return


@cocotb.coroutine
def input_monitor(dut, buff):
    while True:
        yield RisingEdge(dut.data_clk)
        if dut.input_we.value.integer == 1:
            buff.append(dut.input_data.value.integer)


@cocotb.coroutine
def check_data(dut, **kwargs):
    axi_lite = AxiLiteDriver(dut, 's_axi_', dut.axi_clk)

    axi_lite.init_zero()
    yield init_test(dut)

    rd = yield axi_lite.read_reg(0x0)
    assert rd == CORE_ID, f'0x{rd:08x} != 0x{CORE_ID:08x}'
    print('ACA ANDAMOOOOOOOOOOOOOOo')
    yield axi_lite.write_reg(0x4, _COUNT_RST) # all reset and disabled
    
    width = len(dut.input_data)

    buff = []
    cocotb.fork(input_monitor(dut, buff))
    cocotb.fork(random_driver(dut, 1000))
    
    rd = yield axi_lite.read_reg(0x8)
    count = rd & 0xffff
    assert count == 0

    for _ in range(random.randint(0, 10)):
        yield axi_lite.write_reg(0x4, _FIFO_EN | _COUNT_EN) # enable everything
    for _ in range(random.randint(0, 50)):
        yield RisingEdge(dut.data_clk)
    yield axi_lite.write_reg(0x4, 0) # disable fifo and counter
    
    rd = yield axi_lite.read_reg(0x8)
    count, data_avail = rd & 0xffff, (rd >> 31) & 0x1
    
    if count > 0:
        assert data_avail == 1, f'{data_avail} != 1'
    
    data_packets = int(ceil(len(dut.input_data) / len(dut.s_axi__RDATA)))

    n = 0
    sniffed_data = []
    while data_avail:
        
        tmp_value = 0
        for i in range(data_packets):
            rd = yield axi_lite.read_reg(0xc + i * 0x4)
            tmp_value |= ((rd & (2**32 - 1)) << (32 * i))
        sniffed_data.append(tmp_value)
        
        rd = yield axi_lite.read_reg(0x8)
        data_avail = (rd >> 31) & 0x1
        assert n < FIFO_DEPTH, f'Read {n+1} values when fifo depth is {FIFO_DEPTH}'
        n += 1

    assert count >= len(sniffed_data), f'{count} < {len(sniffed_data)}'
    assert subfinder(buff, sniffed_data), f'{sniffed_data} not in {buff}'
    

tf_check_data = TF(check_data)
tf_check_data.add_option('', [0] * 3) # dummy variable to force repetition of test (pytest could be used but it would regenerate the core each time)
tf_check_data.generate_tests()

@pytest.mark.parametrize("width", [8, 32, 40, 64])
def test_datapath_sniffer(width):
    core = DatapathSniffer(width=width, depth=FIFO_DEPTH, domain_data='data', domain_axi='axi')
    ports = core.get_ports()
    run(core, 'nmigen_datapath_sniffer.tests.test_datapath_sniffer', ports=ports, vcd_file=f'./output.vcd')