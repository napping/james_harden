#!/usr/bin/env python
import argparse # optparse is deprecated
from itertools import islice # slicing for iterators
from nltk.stem import PorterStemmer
from nltk.corpus import wordnet
import sys

""" 
    Based on "METEOR: An Automatic Metric for MT Evaluation 
    with High Levels of Correlation with Human Judgments"
    by Alon Lavie and Abhaya Agarwal at Language Technologies Inititute, CMU
"""

class Meteor:
    def __init__(self, sentences, num_sentences, alpha, beta, gamma): 
        self.sentences = sentences
        self.num_sentences = num_sentences
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma

        self.stemmer = PorterStemmer()
        self.wordnet = wordnet

    def run_meteor(self):
        # note: the -n option does not work in the original code
        count = 0
        for h1, h2, ref in islice(self.sentences, self.num_sentences):
            score_1 = self.score(h1, ref)
            score_2 = self.score(h2, ref)


            rset = set(ref)
            # h1_match = word_matches(h1, rset)
            # h2_match = word_matches(h2, rset)
            # print(1 if h1_match > h2_match else # \begin{cases}
                    # (0 if h1_match == h2_match
                        # else -1)) # \end{cases}
            count += 1
            if count % 100 == 0:
                sys.stderr.write(str(count) + " finished. ")

    def score(self, translation, reference):
        best_alignment = self.get_best_alignment(translation, reference)
        mapped_unigrams = sum([1 for mapping in best_alignment if mapping[1] != None])
        translation_unigrams = len(translation)
        reference_unigrams = len(reference)
        P = mapped_unigrams / translation_unigrams
        R = mapped_unigrams / reference_unigrams

        a = self.alpha
        Fmean = (P * R) / ((a * P) + ((1 - a) * R))

    def get_chunks(self, alignment, translation, reference):
        current_chunk = 0
        chunks = 1
        # fugly code =/
        remaining_alignment = alignment
        for i in range(len(translation) - 1):
            this_align = [mapping[1] for mapping in remaining_alignment if mapping[0] == translation[i]]
            next_align = [mapping[1] for mapping in remaining_alignment if mapping[0] == translation[i+1]]

            if len(this_align) == 0 or None in this_align or None in next_align:
                continue

            if (reference.index(this_align[1]) + 1) != (reference.index(next_align[1])):
                chunks += 1
            

    # Generates the optimal mapping between the words of the translation and the reference;
    # every word in each string maps to at most one word in the other string.
    def get_best_alignment(self, translation, reference):
        max_alignments = self.create_word_alignments(translation, reference)

        min_crossings = 9999
        best_alignment = None
        for alignment in max_alignments:
            crossings = 0
            for i, map1 in enumerate(alignment):
                for map2 in alignment[i+1:]:
                    if None in map1 or None in map2:
                        continue
                    else:
                        start1 = translation.index(map1[0])
                        end1 = reference.index(map1[1])
                        start2 = translation.index(map2[0])
                        end2 = reference.index(map2[1])
                        if start1 < start2 and end1 > end2:
                            crossings += 1
                        elif start1 > start2 and end1 < end2:
                            crossings += 1

            if crossings < min_crossings:
                min_crossings = crossings
                best_alignment = alignment

        return best_alignment

    def create_word_alignments(self, translation, reference): 
        mappings = dict(zip(translation, [set() for _ in range(len(translation))]))
        for word in translation:
            for exact in self.exact_module(word, reference):
                mappings[word].add(exact)

            for stemmed in self.porter_module(word, reference):
                mappings[word].add(stemmed)

            for synonym in self.wordnet_module(word, reference):
                mappings[word].add(synonym)
                    
        max_alignments = []
        maximum = 0
        # Awful code, but running out of time lol
        self.curr_alignments = []
        self.generate_alignments(translation, reference, mappings, [])
        for alignment in self.curr_alignments:
            l = len(alignment)
            if l > maximum:
                maximum = l
                max_alignments = [alignment]
            elif l == maximum:
                max_alignments.append(alignment)
        
        return max_alignments

    def generate_alignments(self, translation, reference, mappings, built_up):
        if (len(translation) == 0):
            self.curr_alignments.append(built_up)
        else:
            head = translation[0]
            for ref_word in mappings[head]:
                if ref_word in reference:
                    self.generate_alignments(translation[1:], filter(lambda w: w!=ref_word, reference), mappings, [(head, ref_word)] + built_up)

            self.generate_alignments(translation[1:], reference, mappings, [(head, None)] + built_up)

    def exact_module(self, word, reference):
        if word in reference:
            yield word

    def porter_module(self, word, reference):
        if all(ord(c) < 128 for c in word):
            stemmed = str(self.stemmer.stem(word))
            for ref_word in reference:
                if all(ord(c) < 128 for c in ref_word):
                    if stemmed == str(self.stemmer.stem(ref_word)):
                        yield ref_word
            
    def wordnet_module(self, word, reference):
        if all(ord(c) < 128 for c in word):
            synsets_trans = set(wordnet.synsets(word))
            for ref_word in reference:
                if all(ord(c) < 128 for c in ref_word):
                    synsets_ref = set(wordnet.synsets(ref_word))
                    if bool(synsets_trans & synsets_ref):
                        yield ref_word
 
def sentences(data):
    with open(data) as f:
        for pair in f:
            yield [sentence.strip().split() for sentence in pair.split(' ||| ')]


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Evaluate translation hypotheses.')
    parser.add_argument('-i', '--input', default='data/hyp1-hyp2-ref',
            help='input file (default data/hyp1-hyp2-ref)')
    parser.add_argument('-n', '--num_sentences', default=None, type=int,
            help='Number of hypothesis pairs to evaluate')
    parser.add_argument('-a', '--alpha', default=0.8, type=float,
            help='Alpha')
    parser.add_argument('-b', '--beta', default=0.8, type=float,
            help='Beta')
    parser.add_argument('-g', '--gamma', default=0.3, type=float,
            help='Gamma')
    opts = parser.parse_args()

    s = sentences(opts.input)

    meteor = Meteor(s, opts.num_sentences, opts.alpha, opts.beta, opts.gamma)
    meteor.run_meteor();
