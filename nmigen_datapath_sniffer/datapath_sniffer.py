from nmigen import *
from nmigen.lib.fifo import AsyncFIFO
from nmigen.lib.cdc import FFSynchronizer
from cores_nmigen.axi_lite import AxiLiteDevice
from cores_nmigen.interfaces import AxiLite
from math import ceil


class DatapathSniffer(Elaboratable):

    _addr_w = 8
    _data_w = 32
    _base_registers = [
        ('reg_0', 'ro', 0x00000000, [('core_id',    32,  0),
                                    ]),
        ('reg_1', 'rw', 0x00000004, [('count_rst',   1,  0),
                                     ('count_en',    1,  1),
                                     ('fifo_en',     1,  2),
                                    ]),
        ('reg_2', 'ro', 0x00000008, [('count',      16,  0),
                                     ('data_avail',  1, 31),
                                    ]),
    ]

    def __init__(self, width, depth, domain_data='sync_data', domain_axi='sync_axi'):
        self.width = width
        self.depth = depth
        self.cd_data = domain_data
        self.cd_axi = domain_axi
        self._registers = self._base_registers + self._data_registers
        self.input_we = Signal()
        self.input_data = Signal(width)
        self.core_id = Signal(self._data_w)
        self.axi_lite = AxiLite(self._addr_w, self._data_w, mode='slave', name='s_axi')

    def get_ports(self):
        ports = [self.input_we, self.input_data]
        ports += [self.axi_lite[f] for f in self.axi_lite.fields]
        ports += [self.core_id]
        return ports

    def get_reg_addr_by_name(self, name):
        for n, typ, addr, fields in self._registers:
            if n == name:
                return addr
        raise RuntimeError('Register "' + name + '" not found.')


    @property
    def _data_registers(self):
        first_addr = max([reg[2] for reg in self._base_registers]) + 0x4
        _data_registers = []
        for i in range(int(self.width / self._data_w)):
            _data_registers.append(('reg_data_'+str(i), 'ro', first_addr + i * 0x4, [('data_'+str(i), self._data_w, 0)]))
        if self.width % self._data_w != 0: # for non-multiples
            i = int(self.width / self._data_w)
            _data_registers.append(('reg_data_'+str(i), 'ro', first_addr + i * 0x4, [('data_'+str(i), self.width % self._data_w, 0)]))
        return _data_registers


    def elaborate(self, platform):
        m = Module()
        comb = m.d.comb
        sync_data = m.d[self.cd_data]
        sync_axi = m.d[self.cd_axi]

        # r_domain = ClockDomain(name='r_domain')
        # w_domain = ClockDomain(name='w_domain')
        ## m.domains += r_domain
        ## m.domains += w_domain
        # comb += r_domain.clk.eq(sync_axi.clk)
        # comb += w_domain.clk.eq(sync_data.clk)
        # comb += r_domain.rst.eq(sync_axi.rst | axi_lite_device.fifo_rst)
        # FFSynch... (axi_lite_device.fifo_rst) --> fifo_rst_sync_w
        # comb += w_domain.rst.eq(sync_data.rst | fifo_rst_sync_w)

        count = Signal(31)
        read_next_data = Signal()
        regs_cd_data = Signal(3)
        count_rst_cd_data = Signal()
        fifo_en_cd_data = Signal()
        count_en_cd_data = Signal()

        m.submodules.axi_lite_device = axi_lite_device = AxiLiteDevice(self._addr_w, self._data_w, self._registers, domain=self.cd_axi)
        m.submodules.fifo_core = fifo = AsyncFIFO(width=self.width, depth=self.depth, r_domain=self.cd_axi, w_domain=self.cd_data)
        m.submodules.synchronizer = synch = FFSynchronizer(i=Cat(*[axi_lite_device.registers.count_rst, axi_lite_device.registers.fifo_en, axi_lite_device.registers.count_en]),
                                                           o=regs_cd_data,
                                                           o_domain=self.cd_data)

        comb += axi_lite_device.axi_lite.connect(self.axi_lite)        

        comb += [
            count_rst_cd_data.eq(regs_cd_data[0]),
            fifo_en_cd_data.eq(regs_cd_data[1]),
            count_en_cd_data.eq(regs_cd_data[2]),
        ]

        last_data_reg = int(ceil(self.width / self._data_w) - 1)
        for i in range(int(self.width / self._data_w)):
            comb += getattr(axi_lite_device.registers, 'data_'+str(i)).eq(fifo.r_data[i*self._data_w:(i+1)*self._data_w])

        if self.width % self._data_w != 0: # for non-multiples
            i = last_data_reg
            comb += getattr(axi_lite_device.registers, 'data_'+str(i)).eq(fifo.r_data[i*self._data_w:i*self._data_w + (self.width % self._data_w)])
        
        # comb += axi_lite_device.registers.core_id.eq(self.core_id)
        comb += axi_lite_device.registers.core_id.eq(self.core_id)
        comb += axi_lite_device.registers.data_avail.eq(fifo.r_rdy)
        comb += axi_lite_device.registers.count.eq(count)
        
        comb += read_next_data.eq(axi_lite_device.axi_lite.ar_accepted() & (axi_lite_device.axi_lite.araddr == self.get_reg_addr_by_name('reg_data_'+str(last_data_reg))))
        comb += fifo.r_en.eq(read_next_data)

        with m.If(count_rst_cd_data):
            sync_data += count.eq(0)
        with m.Elif(count_en_cd_data & self.input_we):
            sync_data += count.eq(count + 1)

        with m.If(fifo_en_cd_data):
            comb += [
                fifo.w_en.eq(self.input_we),
                fifo.w_data.eq(self.input_data),
            ]
        with m.Else():
            comb += [
                fifo.w_en.eq(0),
                fifo.w_data.eq(0),
            ]

        return m
