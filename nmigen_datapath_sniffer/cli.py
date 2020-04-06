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

    # to avoid submodules of different verilog files to have the same name.
    name = args.name
    submodule_posfix = f'_w{args.width}_d{args.depth}'

    fragment = Fragment.get(core, None)
    output = verilog.convert(fragment, name=name, ports=ports)
    output = re.sub('\*\)', '*/',re.sub('\(\*','/*', output))
    output = output.replace('__', '_')

    modules = re.findall(r'^module (\S*) ?\(.*\);', output, re.MULTILINE)
    for m in modules:
        pattern = m.replace('\\', '\\\\').replace('$', '\$')
        with_posfix = m.replace('\\', '\\\\') + submodule_posfix
        output = re.sub('^module ' + pattern, 'module ' + with_posfix, output, 0, re.MULTILINE)
        output = re.sub('^  ' + pattern, '  ' + with_posfix, output, 0, re.MULTILINE)


    with open(args.file, 'w') as f:
        f.write(output)


if __name__ == '__main__':
    main()
    
