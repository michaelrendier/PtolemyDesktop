import re
from typing import List, Dict, Tuple, Optional, Any

# Define some default vocabulary. In a real game, these would be loaded from data files.
# Synonyms map to canonical forms.
DEFAULT_VERBS = {
    "take": ["take", "get", "grab", "pick up"],
    "drop": ["drop", "put down"],
    "go": ["go", "walk", "run", "move", "enter"],
    "look": ["look", "examine", "inspect", "l"],
    "open": ["open", "unlock"],
    "close": ["close", "lock"],
    "inventory": ["inventory", "i"],
    "help": ["help", "?"],
    "quit": ["quit", "exit", "bye"],
    "attack": ["attack", "hit", "strike", "fight"],
    "read": ["read"],
    "push": ["push"],
    "pull": ["pull"]
}

DEFAULT_NOUNS = {
    "key": ["key", "keys"],
    "door": ["door", "gate"],
    "lamp": ["lamp", "light", "torch"],
    "sword": ["sword", "blade"],
    "shield": ["shield"],
    "troll": ["troll", "creature"],
    "mailbox": ["mailbox", "mail box"],
    "room": ["room", "area", "place"],
    "north": ["north", "n"],
    "south": ["south", "s"],
    "east": ["east", "e"],
    "west": ["west", "w"],
    "up": ["up", "u"],
    "down": ["down", "d"],
    "all": ["all", "everything"],
    "nothing": ["nothing", "none"],
}

# Filler words that should be ignored (articles, common prepositions not used as delimiters)
DEFAULT_STOP_WORDS = {
    "a", "an", "the", "of", "to", "in", "on", "at", "with", "from", "for", "by", "is", "are", "and",
    "then", "now", "here", "there", "that", "this", "it"
}

# Define how commands are structured and what prepositions are relevant for indirect objects
# (verb_canonical, direct_obj_preposition, indirect_obj_preposition)
# A more advanced parser would have more complex grammar rules.
# For simplicity, we'll assume the first valid preposition after a direct object is for the indirect.
# This structure defines valid command patterns for object/preposition recognition.
# The keys are canonical verbs, values are lists of accepted preposition structures.
# An empty list means no special preposition is expected for an indirect object.
DEFAULT_GRAMMAR_RULES = {
    "take": [None], # take object
    "drop": [None], # drop object
    "go": [None],   # go direction (direction is treated as a direct object here)
    "look": [None, "at", "in"], # look [at] object, look [in] object
    "open": [None, "with"], # open object [with key]
    "close": [None],
    "attack": [None, "with"], # attack creature [with weapon]
    "read": [None],
    "push": [None],
    "pull": [None]
}


@dataclass
class ParsedCommand:
    """
    Represents a command parsed from player input.
    - action: The canonical verb (e.g., 'take', 'look').
    - direct_object: The canonical direct object (e.g., 'key', 'mailbox'). Can be multi-word.
    - direct_object_raw: The raw text of the direct object.
    - indirect_object: The canonical indirect object. Can be multi-word.
    - indirect_object_raw: The raw text of the indirect object.
    - preposition: The preposition linking direct and indirect objects (e.g., 'with', 'at').
    """
    action: Optional[str] = None
    direct_object: Optional[str] = None
    direct_object_raw: Optional[str] = None # Store raw text for context
    indirect_object: Optional[str] = None
    indirect_object_raw: Optional[str] = None # Store raw text for context
    preposition: Optional[str] = None
    original_input: str = ""
    success: bool = False
    error_message: Optional[str] = None

class ZorkParser:
    """
    A Python 3 class to emulate the core functionality of the Zork/Infocom sentence parser.
    It tokenizes input, identifies verbs, direct objects, and indirect objects,
    and handles common filler words.
    """

    def __init__(self,
                 verbs: Dict[str, List[str]] = None,
                 nouns: Dict[str, List[str]] = None,
                 stop_words: set = None,
                 grammar_rules: Dict[str, List[Optional[str]]] = None):
        """
        Initializes the ZorkParser with its vocabulary and grammar rules.

        :param verbs: A dictionary mapping canonical verbs to lists of their synonyms.
                      e.g., {"take": ["take", "get", "grab"]}
        :param nouns: A dictionary mapping canonical nouns to lists of their synonyms/phrases.
                      e.g., {"key": ["key", "keys"], "red boat": ["red boat"]}
        :param stop_words: A set of words to ignore (e.g., "a", "the", "and").
        :param grammar_rules: A dictionary defining valid prepositions for indirect objects,
                              keyed by canonical verbs.
                              e.g., {"look": [None, "at"], "attack": [None, "with"]}
        """
        self.verbs = {v_syn.lower(): canonical_v for canonical_v, v_list in (verbs or DEFAULT_VERBS).items() for v_syn in v_list}
        self.nouns = {n_syn.lower(): canonical_n for canonical_n, n_list in (nouns or DEFAULT_NOUNS).items() for n_syn in n_list}
        self.stop_words = stop_words or DEFAULT_STOP_WORDS
        self.grammar_rules = grammar_rules or DEFAULT_GRAMMAR_RULES

        # Pre-process multi-word nouns for more efficient matching
        self._multi_word_nouns = sorted([
            syn for canonical, syn_list in (nouns or DEFAULT_NOUNS).items() for syn in syn_list if ' ' in syn
        ], key=len, reverse=True) # Sort by length descending for greedy matching

        # Prepositions used in grammar rules (for identifying them in input)
        self._known_prepositions = set(
            p for rules in self.grammar_rules.values() for p in rules if p is not None
        )


    def _tokenize(self, text: str) -> List[str]:
        """
        Splits the input text into a list of words, handling punctuation and converting to lowercase.
        """
        # Replace common punctuation with spaces, then split.
        # This is a simplified tokenization. Real-world NLP uses more sophisticated methods.
        cleaned_text = re.sub(r"[.,!?;:]", " ", text).lower()
        tokens = [word for word in cleaned_text.split() if word]
        return tokens

    def _find_verb(self, tokens: List[str]) -> Tuple[Optional[str], int]:
        """
        Attempts to find a verb at the beginning of the token list.
        Returns the canonical verb and its index (0 if found at start).
        Handles multi-word verbs if defined (though not common in Zork).
        """
        for i in range(len(tokens)):
            phrase = " ".join(tokens[:i+1])
            if phrase in self.verbs:
                return self.verbs[phrase], i + 1 # Return canonical verb and words consumed
        return None, 0

    def _find_object(self, tokens: List[str], start_idx: int) -> Tuple[Optional[str], Optional[str], int]:
        """
        Attempts to find the longest matching noun phrase (object) in the tokens
        starting from `start_idx`.
        Returns canonical object, raw object text, and number of words consumed.
        Prioritizes multi-word nouns.
        """
        remaining_tokens = tokens[start_idx:]

        # First, try to match multi-word nouns (greedy, longest first)
        for mw_noun in self._multi_word_nouns:
            mw_tokens = mw_noun.split()
            if len(mw_tokens) <= len(remaining_tokens):
                potential_match = " ".join(remaining_tokens[:len(mw_tokens)])
                if potential_match in self.nouns:
                    return self.nouns[potential_match], potential_match, len(mw_tokens)

        # Then, try single-word nouns
        for i in range(len(remaining_tokens)):
            token = remaining_tokens[i]
            if token in self.nouns:
                return self.nouns[token], token, i + 1 # return canonical, raw, words consumed
            elif token in self.stop_words:
                # Skip stop words if they appear before a potential single-word noun
                continue
            else:
                # If we encounter a non-noun, non-stop-word, we stop looking for this object
                break
        return None, None, 0

    def parse(self, command_input: str) -> ParsedCommand:
        """
        Parses a Zork-like command string into a structured ParsedCommand object.

        :param command_input: The raw string input from the player (e.g., "take the rusty key").
        :return: A ParsedCommand object indicating the parsed action, objects, and status.
        """
        parsed_cmd = ParsedCommand(original_input=command_input)
        tokens = self._tokenize(command_input)

        if not tokens:
            parsed_cmd.error_message = "No input provided."
            return parsed_cmd

        # 1. Find Verb
        canonical_verb, verb_consumed_count = self._find_verb(tokens)
        if not canonical_verb:
            parsed_cmd.error_message = f"I don't understand the verb '{tokens[0]}'."
            return parsed_cmd

        parsed_cmd.action = canonical_verb
        remaining_tokens = tokens[verb_consumed_count:]

        # Handle special commands that don't take objects (e.g., "inventory", "help", "quit")
        if canonical_verb in ["inventory", "help", "quit"]:
            # If there are any extra words after these commands, it's an error for simplicity
            if any(t not in self.stop_words for t in remaining_tokens):
                parsed_cmd.error_message = f"Too many words after '{canonical_verb}'."
                return parsed_cmd
            parsed_cmd.success = True
            return parsed_cmd

        # 2. Find Direct Object
        obj1_canonical, obj1_raw, obj1_consumed_count = self._find_object(remaining_tokens, 0)

        # Simple commands like "go north" where "north" is the object
        if canonical_verb == "go" and obj1_canonical:
            parsed_cmd.direct_object = obj1_canonical
            parsed_cmd.direct_object_raw = obj1_raw
            parsed_cmd.success = True
            return parsed_cmd

        remaining_tokens_after_obj1 = remaining_tokens[obj1_consumed_count:]

        # If we didn't find a direct object, but the verb *requires* one, it's an error
        # (Assuming verbs like 'take', 'open' always need a direct object)
        if not obj1_canonical and canonical_verb not in ["look"]: # 'look' can be standalone
            parsed_cmd.error_message = f"What do you want to '{canonical_verb}'?"
            return parsed_cmd

        parsed_cmd.direct_object = obj1_canonical
        parsed_cmd.direct_object_raw = obj1_raw

        # 3. Find Preposition and Indirect Object
        # Iterate through remaining tokens to find a preposition
        preposition_found = None
        preposition_idx = -1
        for i, token in enumerate(remaining_tokens_after_obj1):
            if token in self._known_prepositions:
                # Check if this preposition is valid for the current verb's grammar
                if token in self.grammar_rules.get(canonical_verb, []):
                    preposition_found = token
                    preposition_idx = i
                    break
            elif token not in self.stop_words:
                # If we encounter a non-stop-word that's not a known preposition,
                # then there's no preposition for an indirect object.
                break

        if preposition_found:
            parsed_cmd.preposition = preposition_found
            # Now find the indirect object after the preposition
            obj2_tokens_start_idx = preposition_idx + 1
            obj2_canonical, obj2_raw, obj2_consumed_count = \
                self._find_object(remaining_tokens_after_obj1, obj2_tokens_start_idx)

            if not obj2_canonical:
                parsed_cmd.error_message = f"What do you want to {preposition_found}?"
                parsed_cmd.success = False # Cannot fully parse
                return parsed_cmd

            parsed_cmd.indirect_object = obj2_canonical
            parsed_cmd.indirect_object_raw = obj2_raw

            # Check for any unparsed tokens after the full command
            unparsed_suffix_tokens = remaining_tokens_after_obj1[obj2_tokens_start_idx + obj2_consumed_count:]
            if any(t not in self.stop_words for t in unparsed_suffix_tokens):
                parsed_cmd.error_message = f"I don't understand '{' '.join(unparsed_suffix_tokens)}' after the command."
                parsed_cmd.success = False
                return parsed_cmd
        elif any(t not in self.stop_words for t in remaining_tokens_after_obj1):
            # If there are unparsed tokens and no valid preposition was found
            parsed_cmd.error_message = f"I don't understand '{' '.join(remaining_tokens_after_obj1)}' after the direct object."
            parsed_cmd.success = False
            return parsed_cmd

        parsed_cmd.success = True
        return parsed_cmd


# --- Example Usage ---
if __name__ == "__main__":
    parser = ZorkParser()

    test_commands = [
        "take lamp",
        "get the rusty key",
        "look",
        "look at the small mailbox",
        "go north",
        "open the door with the key",
        "attack the troll with a sword",
        "inventory",
        "help",
        "quit game", # should flag as error for extra word
        "drop all",
        "read sign",
        "push button on wall", # Example of potential extension needed for more complex prepositions
        "invalid command",
        "take", # Missing object
        "take the key with a hammer", # "with" not in grammar for take (should be handled by parser error message implicitly)
        "look around room", # "around" not in grammar for look
        "" # Empty input
    ]

    print("--- Zork Parser Test ---")
    for cmd_str in test_commands:
        print(f"\nParsing: '{cmd_str}'")
        parsed = parser.parse(cmd_str)
        if parsed.success:
            print(f"  Success! Action: '{parsed.action}'")
            if parsed.direct_object:
                print(f"  Direct Object: '{parsed.direct_object}' (Raw: '{parsed.direct_object_raw}')")
            if parsed.indirect_object:
                print(f"  Indirect Object: '{parsed.indirect_object}' (Raw: '{parsed.indirect_object_raw}')', Preposition: '{parsed.preposition}'")
        else:
            print(f"  Failed: {parsed.error_message}")

    # Demonstrate adding custom vocabulary
    print("\n--- Adding Custom Vocabulary ---")
    custom_verbs = {
        "eat": ["eat", "devour"],
        "drink": ["drink"]
    }
    custom_nouns = {
        "apple": ["apple", "red apple"],
        "water": ["water", "pure water"]
    }
    # Merge with defaults or create a new parser instance
    extended_verbs = {**DEFAULT_VERBS, **custom_verbs}
    extended_nouns = {**DEFAULT_NOUNs, **custom_nouns}
    extended_grammar = {**DEFAULT_GRAMMAR_RULES, "eat": [None], "drink": [None]}

    custom_parser = ZorkParser(verbs=extended_verbs, nouns=extended_nouns, grammar_rules=extended_grammar)
    parsed_custom = custom_parser.parse("eat the red apple")
    if parsed_custom.success:
        print(f"Parsing 'eat the red apple' -> Action: '{parsed_custom.action}', Direct Object: '{parsed_custom.direct_object}'")
    else:
        print(f"Parsing 'eat the red apple' -> Failed: {parsed_custom.error_message}")

    parsed_custom = custom_parser.parse("drink pure water")
    if parsed_custom.success:
        print(f"Parsing 'drink pure water' -> Action: '{parsed_custom.action}', Direct Object: '{parsed_custom.direct_object}'")
    else:
        print(f"Parsing 'drink pure water' -> Failed: {parsed_custom.error_message}")