from lamoda import LamodaParser
from argparse import ArgumentParser


arg_parser = ArgumentParser()


if __name__ == "__main__":
    arg_parser.add_argument("-md", "--mdelay", type=float, default=1.0, help="Main routine delay")
    arg_parser.add_argument('-b', '--begin', type=str, required=False, help='A category, that will use to begin a process')
    arg_parser.add_argument('-bd', '--begin_dir', type=str, required=False, help='A category path, that will use to begin a process')
    arg_parser.add_argument('-ps', '--proxy_server', type=str, required=False, help='A proxy server')
    args = arg_parser.parse_args()
    lamoda_parser = LamodaParser(mdelay=args.mdelay, begin=args.begin, begin_dir=args.begin_dir, proxy_server=args.proxy_server)
    lamoda_parser.start()
    