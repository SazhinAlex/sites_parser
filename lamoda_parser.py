from lamoda import LamodaParser
from argparse import ArgumentParser


arg_parser = ArgumentParser()


if __name__ == "__main__":
    arg_parser.add_argument("-md", "--mdelay", type=float, default=1.0, help="Main routine delay")
    args = arg_parser.parse_args()
    lamoda_parser = LamodaParser(mdelay=args.mdelay)
    lamoda_parser.start()
    