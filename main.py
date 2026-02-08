import argparse
import logging
import sys
from src.splitter import split_sql


def main():
  logging.basicConfig(level=logging.DEBUG)
  try:
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", help="Path to the sql file.", required=True, type=str)
    parser.add_argument("-n", help="Number of chunk to split sql file.", required=True, type=int)
    parser.add_argument("-s", help="SQL new line sepparator, default ';'.", required=False, type=str, default=";")
    parser.add_argument("-c", help="Single line comment character, default '--'.", required=False, type=str, default="--")
    parser.add_argument("-m", help="Multi line comment character, default '/*'.", required=False, type=str, default="/*")
    parser.add_argument("-z", help="Compress output by ignoring emptylines and comments", required=False, action='store_true')
    args = parser.parse_args()
    
    split_sql(args.f, args.n, args.s, args.c, args.m, args.z)

  except Exception as ex:
    logging.error(ex, exc_info=True)
    sys.exit(1)


if __name__ == '__main__':
  main()
