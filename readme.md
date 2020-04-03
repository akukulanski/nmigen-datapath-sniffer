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

General requirements:

* Python3 (>=3.6)
* Python3 pip

To generate the Verilog code:

* Yosys 0.9+

To run the tests:

* Icarus Verilog v10.1 (problems with v10.2+)
* GTKWave (optional, to visualize the waveforms)


### Start

(optional step) Do everything in a virtual environment:

```bash
$ python3 -m venv venv
$ source venv/bin/activate
```

Install as a Python package:

```bash
$ pip install .
```

Run tests:

```bash
$ python3 -m pytest -sv nmigen_datapath_sniffer
```

Generate verilog:
```bash
$ python3 -m nmigen_datapath_sniffer.cli -w 70 -d 4 -n my_datapath_sniffer sniffer.v
```

The generated Verilog has the multiple submodules in the same `.v` file. The top module
will be the one specified with `-n` (`-name`) in the cli parameters. In this example,

```bash
$ cat sniffer.v | grep --color -n "module my_datapath_sniffer"
```
