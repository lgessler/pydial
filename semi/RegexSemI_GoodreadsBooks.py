###############################################################################
# PyDial: Multi-domain Statistical Spoken Dialogue System Software
###############################################################################
#
# Copyright 2015 - 2018
# Cambridge University Engineering Department Dialogue Systems Group
#
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
###############################################################################

"""
RegexSemI_CamRestaurants.py - regular expression based CamRestaurants SemI decoder
===============================================================


HELPFUL: http://regexr.com

"""

'''
    Modifications History
    ===============================
    Date        Author  Description
    ===============================
    Jul 21 2016 lmr46   Refactoring, creating abstract class SemI
'''

import RegexSemI
import re, os
parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.sys.path.insert(0, parentdir)
from utils import ContextLogger
logger = ContextLogger.getLogger('')

from nltk.corpus import wordnet as wn
def find_syns(word):
    syns = wn.synsets(word.replace(" ", "_"))
    lemmas = [lemma.name()
              for synset in wn.synsets(word.replace(" ", "_"))
              for lemma in synset.lemmas()]
    return lemmas

def syn_patterns(word):
    lemmas = find_syns(word)
    formatted_lemmas = ["|(" + x.replace(" ", "\\ ") + ")" for x in lemmas]
    return "".join(formatted_lemmas)


class RegexSemI_GoodreadsBooks(RegexSemI.RegexSemI):
    """
    """

    def __init__(self, repoIn=None):
        RegexSemI.RegexSemI.__init__(self)  # better than super() here - wont need to be changed for other domains
        self.domainTag = "GoodreadsBooks"  # FIXME
        self.create_domain_dependent_regex()

    def create_domain_dependent_regex(self):
        """Can overwrite any of the regular expressions set in RegexParser.RegexParser.init_regular_expressions().
        This doesn't deal with slot,value (ie domain dependent) semantics. For those you need to handcraft
        the _decode_[inform,request,confirm] etc.
        """
        # REDEFINES OF BASIC SEMANTIC ACTS (ie those other than inform, request): (likely nothing needs to be done here)
        # eg: self.rHELLO = "anion"

        self._domain_init(dstring=self.domainTag)

        # DOMAIN DEPENDENT SEMANTICS:
        self.slot_vocab = dict.fromkeys(self.USER_REQUESTABLE, '')
        # FIXME: define slot specific language -  for requests
        # ---------------------------------------------------------------------------------------------------
        self.slot_vocab["author"] = "(author|by)"
        self.slot_vocab["review"] = "(reviews?)"
        self.slot_vocab["rating"] = "(ratings?)"
        self.slot_vocab["title"] = "(name|title)"
        # ---------------------------------------------------------------------------------------------------
        # Generate regular expressions for requests:
        self._set_request_regex()

        # FIXME:  many value have synonyms -- deal with this here:
        self._set_value_synonyms()  # At end of file - this can grow very long
        self._set_inform_regex()

    def _set_request_regex(self):
        """
        """
        self.request_regex = dict.fromkeys(self.USER_REQUESTABLE)
        for slot in self.request_regex.keys():
            # FIXME: write domain dependent expressions to detext request acts
            self.request_regex[slot] = self.rREQUEST + "\ " + self.slot_vocab[slot]
            self.request_regex[slot] += "|(?<!" + self.DONTCAREWHAT + ")(?<!want\ )" + self.IT + "\ " + self.slot_vocab[
                slot]
            self.request_regex[slot] += "|(?<!" + self.DONTCARE + ")" + self.WHAT + "\ " + self.slot_vocab[slot]

        self.request_regex["author"] += "|(authors?)|(writer)|(who\ (is\ the\ )*author)|(whats?\ the\ author)" + syn_patterns("author")
        self.request_regex["title"] += "|(title)|(name)|(what\ (is\ book\ called))" + syn_patterns("title")
        self.request_regex["review"] += "|(review/s)|(commentary)" + syn_patterns("review") + syn_patterns("opinion")
        self.request_regex["rating"] += "|(ratings?)" + syn_patterns("rating")

    def _set_inform_regex(self):
        """
        """
        self.inform_regex = dict.fromkeys(self.USER_INFORMABLE)
        for slot in self.inform_regex.keys():
            self.inform_regex[slot] = {}
            for value in self.slot_values[slot].keys():
                self.inform_regex[slot][value] = self.rINFORM + "\ " + re.escape(self.slot_values[slot][value])
                self.inform_regex[slot][value] += "|" + re.escape(self.slot_values[slot][value]) + self.WBG
                self.inform_regex[slot][value] += "|(\ |^)" + re.escape(self.slot_values[slot][value]) + "(\ (please|and))*"

            # FIXME: value independent rules:
            nomatter = r"\ doesn\'?t matter"
            dontcare = r"(any(\ (kind|type)(\ of)?)?)|((i\ )?(don\'?t|do\ not)\ care\ (what|which|about|for))(\ (kind|type)(\ of)?)"
            if slot == "author":
                slot_term = r"(the\ )*(author|writer)"
                self.inform_regex[slot]['dontcare'] = dontcare + slot_term
                self.inform_regex[slot]['dontcare'] += r"|" + slot_term + nomatter

            if slot == "rating":
                slot_term = r"(the\ )*" + slot
                self.inform_regex[slot]['dontcare'] = dontcare + slot_term
                self.inform_regex[slot]['dontcare'] += r"|" + slot_term + nomatter

    def _generic_request(self, obs, slot):
        """
        """
        if self._check(re.search(self.request_regex[slot], obs, re.I)):
            self.semanticActs.append('request(' + slot + ')')

    def _generic_inform(self, obs, slot):
        """
        """

        DETECTED_SLOT_INTENT = False
        for value in self.inform_regex[slot]:
            if self._check(re.search(self.inform_regex[slot][value], obs, re.I)):
                # FIXME:  Think easier to parse here for "dont want" and "dont care" - else we're playing "WACK A MOLE!"
                ADD_SLOTeqVALUE = True
                #                 # Deal with -- DONTWANT --:
                #                 if self._check(re.search(self.rINFORM_DONTWANT+"\ "+self.slot_values[slot][value], obs, re.I)):
                #                     self.semanticActs.append('inform('+slot+'!='+value+')')  #TODO - is this valid?
                #                     ADD_SLOTeqVALUE = False
                #                 # Deal with -- DONTCARE --:
                #                 if self._check(re.search(self.rINFORM_DONTCARE+"\ "+slot, obs, re.I)) and not DETECTED_SLOT_INTENT:
                #                     self.semanticActs.append('inform('+slot+'=dontcare)')
                #                     ADD_SLOTeqVALUE = False
                #                     DETECTED_SLOT_INTENT = True
                # Deal with -- REQUESTS --: (may not be required...)
                # TODO? - maybe just filter at end, so that inform(X) and request(X) can not both be there?
                if ADD_SLOTeqVALUE and not DETECTED_SLOT_INTENT:
                    self.semanticActs.append('inform(' + slot + '=' + value + ')')

    def _decode_request(self, obs):
        """
        """
        # if a slot needs its own code, then add it to this list and write code to deal with it differently
        DO_DIFFERENTLY = []  # FIXME
        for slot in self.USER_REQUESTABLE:
            if slot not in DO_DIFFERENTLY:
                self._generic_request(obs, slot)
        # Domain independent requests:
        self._domain_independent_requests(obs)

    def _decode_inform(self, obs):
        """
        """
        # if a slot needs its own code, then add it to this list and write code to deal with it differently
        DO_DIFFERENTLY = []  # FIXME
        for slot in self.USER_INFORMABLE:
            if slot not in DO_DIFFERENTLY:
                self._generic_inform(obs, slot)
        # Check other statements that use context
        self._contextual_inform(obs)

    def _decode_type(self, obs):
        """
        """
        # This is pretty ordinary - will just keyword spot for now since type really serves no point at all in our system
        if self._check(re.search(self.inform_type_regex, obs, re.I)):
            self.semanticActs.append('inform(type=' + self.domains_type + ')')

    def _decode_confirm(self, obs):
        """
        """
        # TODO?
        pass

    def _set_value_synonyms(self):
        """Starts like:
            self.slot_values[slot] = {value:"("+str(value)+")" for value in DOMAINS_ontology["informable"][slot]}
            # Can add regular expressions/terms to be recognised manually:
        """
        # FIXME:
        # ---------------------------------------------------------------------------------------------------
        # TYPE:
        self.inform_type_regex = r"(book|novel|(want|looking for) book|(read|some(thing)) to read)"
        ## SLOT: area
        #slot = 'area'
        ## {u'west': '(west)', u'east': '(east)', u'north': '(north)', u'south': '(south)', u'centre': '(centre)'}
        #self.slot_values[slot]['north'] = "((the)\ )*(north|kings\ hedges|arbury|chesterton)"
        #self.slot_values[slot]['east'] = "((the)\ )*(east|castle|newnham)"
        #self.slot_values[slot]['west'] = "((the)\ )*(west|abbey|romsey|cherry hinton)"
        #self.slot_values[slot]['south'] = "((the)\ )*(south|trumpington|queen ediths|coleridge)"
        #self.slot_values[slot][
        #    'centre'] = "((the)\ )*(centre|center|downtown|central|market)"  # lmr46, added rule for detecting the center
        ##         self.slot_values[slot]['dontcare'] = "any(\ )*(area|location|place|where)"
        ## SLOT: pricerange
        #slot = 'pricerange'
        ## {u'moderate': '(moderate)', u'budget': '(budget)', u'expensive': '(expensive)'}
        #self.slot_values[slot]['moderate'] = "(to\ be\ |any\ )*(moderat|moderate|moderately\ priced|mid|middle|average)"
        #self.slot_values[slot]['moderate'] += "(?!(\ )*weight)"
        #self.slot_values[slot][
        #    'cheap'] = "(to\ be\ |any\ )*(budget|cheap|bargin|bargain|inexpensive|cheapest|low\ cost)"
        #self.slot_values[slot]['expensive'] = "(to\ be\ |any\ )*(expensive|expensively|dear|costly|pricey)"
        ##         self.slot_values[slot]['dontcare'] = "any\ (price|price(\ |-)*range)"
        ## SLOT: food
        #slot = "food"
        ## rely only on ontology values for now
        #self.slot_values[slot]["asian oriental"] = "(oriental|asian)"
        #self.slot_values[slot]["gastropub"] = "(gastropub|gastro pub)"
        #self.slot_values[slot]["italian"] = "(italian|pizza|pasta)"
        #self.slot_values[slot]["north american"] = "(american|USA)"

        # ---------------------------------------------------------------------------------------------------

# END OF FILE
