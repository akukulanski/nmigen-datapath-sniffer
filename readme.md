# Datapath Sniffer

### Description

The Datapath Sniffer is basically a FIFO and a counter with an axi lite
interface where the input is controlled only with the signals `input_we`
and `input_data`, and the output is read from Axi Lite registers.

It is meant to use for debugging purposes as a sniffer that can be used
at any point of a datapath in a design.

### AXI MAP

`0x0000`: Core id

|Bits|Name|Description|
|-|-|-|
|[31:0]|`core_id`|Core id.|

`0x0004`: CSR

|Bits|Name|Description|
|-|-|-|
|[0]|`count_rst`|Reset counter. Must be manually deasserted.|
|[1]|`count_en`|Enable counter. Must be manually deasserted.|
|[2]|`fifo_en`|Enable fifo.|

`0x0008`: STATUS

|Bits|Name|Description|
|-|-|-|
|[15:0]|`count`|Counter count.|
|[30:16]|RESERVED|-|
|[31]|`avail`|Data available to read.|

`0x000C`: Data 0

|Bits|Name|Description|
|-|-|-|
|[31:0]|`data_0`|Bits 31 to 0 of the current fifo data|

`0x0010`: Data 1

|Bits|Name|Description|
|-|-|-|
|[31:0]|`data_1`|Bits 63 to 32 of the current fifo data|

`0x000C + 0x4 * x`: Data x

|Bits|Name|Description|
|-|-|-|
|[31:0]|`data_x`|Bits (32*(x+1)-1) to (32*x) of the current fifo data|

There are data registers from `data_0` to `data_N`, where `N=int(ceil(input_data_width / axi_lite_data_width) - 1)`.

How to pop:

The pop of the fifo is done automatically when the last data register (`data_N`) is read from the AXI lite interface.
After that read, to know if there are valid elements remaining to read from the fifo, the `avail` signal should be
checked (bit 31 of 0x0008).


### Requirements

nMigen, Icarus Verilog, Cocotb, ...


### Run tests

`python3 -m pytest -sv nmigen_datapath_sniffer`