from sys import argv
from .scan2pdf import main as scan2pdf

def main():
    scan2pdf(argv[1:])
