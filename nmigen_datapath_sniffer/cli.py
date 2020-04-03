import argparse
import re
from nmigen_datapath_sniffer.datapath_sniffer import DatapathSniffer
from nmigen.hdl.ir import Fragment
from nmigen.back import verilog


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--name', '-n', type=str, default='datapath_sniffer', help='Module name')
    parser.add_argument('--width', '-w', type=int, default=64, help='Input data width')
    parser.add_argument('--depth', '-d', type=int, default=8, help='Fifo depth')
    parser.add_argument('file', type=str, metavar='FILE', help='output file (verilog)')
    return parser.parse_args()


def main():
    args = get_args()

    core = DatapathSniffer(width=args.width, depth=args.depth, domain_data='data', domain_axi='axi')
    ports = core.get_ports()

    fragment = Fragment.get(core, None)
    output = verilog.convert(fragment, name=args.name, ports=ports)

    # to avoid submodules of different verilog files to have the same name.
    submodule_prefix = f'_w{args.width}_d{args.depth}'

    with open(args.file, 'w') as f:
        output = re.sub('\*\)', '*/',re.sub('\(\*','/*', output))
        output = output.replace('__', '_')
        output = re.sub(f'module (?!{args.name})', f'module {submodule_prefix}_', output)
        f.write(output)


if __name__ == '__main__':
    main()
    
