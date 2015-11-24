#!/usr/bin/env python
__author__ = 'chris'
import argparse
import sys

BASE_PAIR_COMPLEMENTS = {'a': 't', 't': 'a', 'c': 'g', 'g': 'c', 'A': 'T', 'T': 'A', 'C': 'G', 'G': 'C', 'n': 'n', 'N': 'N'}

CODON_TABLE = {'AAA': 'K', 'AAC': 'N', 'AAG': 'K', 'AAT': 'N', 'ACA': 'T', 'ACC': 'T', 'ACG': 'T', 'ACT': 'T',
               'AGA': 'R', 'AGC': 'S', 'AGG': 'R', 'AGT': 'S', 'ATA': 'I', 'ATC': 'I', 'ATG': 'M', 'ATT': 'I',
               'CAA': 'Q', 'CAC': 'H', 'CAG': 'Q', 'CAT': 'H', 'CCA': 'P', 'CCC': 'P', 'CCG': 'P', 'CCT': 'P',
               'CGA': 'R', 'CGC': 'R', 'CGG': 'R', 'CGT': 'R', 'CTA': 'L', 'CTC': 'L', 'CTG': 'L', 'CTT': 'L',
               'GAA': 'E', 'GAC': 'D', 'GAG': 'E', 'GAT': 'D', 'GCA': 'A', 'GCC': 'A', 'GCG': 'A', 'GCT': 'A',
               'GGA': 'G', 'GGC': 'G', 'GGG': 'G', 'GGT': 'G', 'GTA': 'V', 'GTC': 'V', 'GTG': 'V', 'GTT': 'V',
               'TAA': '*', 'TAC': 'Y', 'TAG': '*', 'TAT': 'Y', 'TCA': 'S', 'TCC': 'S', 'TCG': 'S', 'TCT': 'S',
               'TGA': '*', 'TGC': 'C', 'TGG': 'W', 'TGT': 'C', 'TTA': 'L', 'TTC': 'F', 'TTG': 'L', 'TTT': 'F',
               'NNN': 'X'}

for i in 'ACTG':
    for j in 'ACTG':
        CODON_TABLE['%s%sN' % (i, j)] = 'X'
        CODON_TABLE['%sN%s' % (i, j)] = 'X'
        CODON_TABLE['N%s%s' % (i, j)] = 'X'
    CODON_TABLE['%sNN' % i] = 'X'
    CODON_TABLE['N%sN' % i] = 'X'
    CODON_TABLE['NN%s' % i] = 'X'

parser = argparse.ArgumentParser(description="This will translate a given DNA sequence to protein.")
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument('--sequence', help='The sequence to translate.', type=str)
group.add_argument('--fasta', help='The fasta file to translate.', type=argparse.FileType('rb'))
simple_group = parser.add_argument_group('Parameter Group')
simple_group.add_argument('--frame', help='The frame to translate in.', type=str, choices=['+1', '+2', '+3', '-1', '-2', '-3'], default='+1')
simple_group.add_argument('--out', help='The file to save translations to.', type=argparse.FileType('wb'))


def main():
    args = parser.parse_args()
    seq = args.sequence
    fasta = args.fasta

    def translate(seq=None, frame=None):
        if frame.startswith('-'):
            seq = ''.join([BASE_PAIR_COMPLEMENTS.get(i, 'N') for i in seq])
        frame = int(frame[1])-1
        return ''.join([CODON_TABLE.get(seq[i:i+3], 'X') for i in xrange(frame, len(seq), 3) if i+3<=len(seq)])

    frame = args.frame
    with args.out as fasta_out:
        if fasta:
            with args.fasta as fasta_in:
                header = ''
                seq = ''
                for row in fasta_in:
                    if row[0] == '>':
                        if seq:
                            fasta_out.write('{}\n{}\n'.format(header, translate(seq, frame)))
                        header = row
                        seq = ''
                    else:
                        seq += row.strip()
                if seq:
                    fasta_out.write('{}\n{}\n'.format(header, translate(seq, frame)))
        else:
            fasta_out.write('{}\n{}\n'.format('>1', translate(seq.upper(), frame)))

if __name__ == "__main__":
    sys.exit(main())
