import utils
import argparse as ap


def parse_argument():
    pars = ap.ArgumentParser()
    pars.add_argument(
        "-F", action = "store_true",
        help = "Use fast search"
    )

    pars.add_argument(
        "-A", action = "store_true",
        help = "Use accurate search"
    )
    return pars.parse_args()

if __name__ == "__main__":
    args = parse_argument()

    if args.F:
        mode = "F"
    elif args.A:
        mode = "A"
    else:
        raise SystemExit("Please specify -A or -F for fast or accurate search")

    r = utils.RunApp(mode)