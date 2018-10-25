from Scripts import searchers
from nltk.stem.snowball import RussianStemmer
from requests import get
from bs4 import BeautifulSoup
import re
import multiprocessing as mp

def ffilter(f, ar):
    return list(filter(f, ar))


def fmap(f, ar):
    return list(map(f, ar))

class Targeter:
    many_targeting = False
    @staticmethod
    def word_root_match(word1, word2, stemmer):
        return stemmer.stem(word1) == stemmer.stem(word2)
    def match_word(self, word):
        return {
            'link' : None,
            'definition' : None
        }
    @classmethod
    def targets_many(cls):
        return cls.many_targeting

class TermListTargeter(Targeter):
    many_targeting = False
    @staticmethod
    def to_term_searcher(terms_links, stemmer):
        future_links_searcher = {}
        for t in terms_links:
            future_links_searcher[stemmer.stem(t.word)] = t
        return future_links_searcher

    def match_word(self, word):
        match = self.term_searcher.get(self.stemmer.stem(word))
        if match is None:
            return None
        else:
            definition = match.definition
            if self.get_definition is not None and definition is None:
                definition = self.get_definition(match.link)
            print(definition)
            return {
                'link' : match.link,
                'definition' : definition
            }

    def __init__(self, terms_links, definition_getter = None):
        self.stemmer = RussianStemmer()
        self.term_searcher = TermListTargeter.to_term_searcher(terms_links, self.stemmer)
        self.get_definition = definition_getter

class WikiTargeter(Targeter):
    many_targeting = True
    @staticmethod
    def only_letters(word):
        return ''.join(ffilter(lambda c : ord(c) >= ord('а') and ord(c) <= ord('я'), word.lower()))
    def match_word(self, word, lim = 5):
        # print('Searching for ' + word)
        PARAMS = {
            'format' : 'json',
            'utf8' : '',
            'action':'opensearch',
            'search' : word,
            'limit' : lim
        }
        resp = get(self.wiki, PARAMS).json()
        print(resp)
        try:
            for i in range(lim):
                if resp[2][i].endswith(':') or len(resp[2][i].split()) <= 1:
                    continue
                res_word = WikiTargeter.only_letters(resp[1][i].split()[0])
                print(word, res_word)
                if self.stemmer.stem(res_word).lower() == self.stemmer.stem(word).lower():
                    return {
                        'definition' : resp[2][i],
                        'link' : resp[3][i]
                    }
            return None
        except:
            return None
    @staticmethod
    def put_match_to_queue(word, queue, lim = 5):
        queue.put((word, self.match_word(word, lim)))
    def match_words(self, words, lim = 5):
        q = mp.Pool()
        results = q.map(self.match_word, words)
        return {words[i] : results[i] for i in range(len(words)) if results[i] is not None}
    def __init__(self, api='https://ru.wikipedia.org/w/api.php'):
        self.wiki = api
        self.stemmer = RussianStemmer()
class WiktionaryTargeter(Targeter):
    many_targeting = True
    def __init__(self, api='https://ru.wiktionary.org/w/api.php', words_per_request = 50):
        self.wiktionary = api
        self.words_per_request = words_per_request
    def get_links(self, words):
        PARAMS = {
            'action' : 'query',
            'titles' : ('|'.join(words)).lower(),
            'prop' : 'info',
            'inprop' : 'url',
            'format' : 'json'
        }
        resp = get(self.wiktionary, PARAMS).json()['query']['pages']
        word_dict = {}
        for k, v in resp.items():
            if int(k) >= 0:
                word_dict[v['title']] = v.get('fullurl')
        return [word_dict.get(w) for w in words]
    def match_words(self, words):
        words = list(set(map(lambda x : x.lower(), filter(lambda x : re.match(r'^[а-яА-Я](([а-яА-Я]|\-)+[а-яА-Я])?$', x), words))))
        print(words)
        links = []
        for i in range(0, len(words), self.words_per_request):
            links += self.get_links(words[i : i + self.words_per_request])
        if links is None:
            return links
        else:
            return {words[i] : {'link' : links[i], 'definition' : None} for i in range(len(words)) if links[i] is not None}