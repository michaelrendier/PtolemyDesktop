import re
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Set

@dataclass
class ParsedCommand:
    """
    Represents a command parsed from player input.
    This dataclass provides a structured way to hold the extracted components
    of the player's command, making it easy for game logic to interpret.

    Attributes:
        action (Optional[str]): The canonical verb (e.g., 'take', 'look'). None if not found.
        direct_object (Optional[str]): The canonical direct object (e.g., 'key', 'mailbox'). None if not found.
        direct_object_raw (Optional[str]): The raw text of the direct object as it appeared in input.
        indirect_object (Optional[str]): The canonical indirect object. None if not found.
        indirect_object_raw (Optional[str]): The raw text of the indirect object.
        preposition (Optional[str]): The preposition linking direct and indirect objects (e.g., 'with', 'at').
        original_input (str): The complete raw input string from the player.
        success (bool): True if the command was successfully parsed into a recognizable structure.
        error_message (Optional[str]): A message explaining why parsing failed, if applicable.
    """
    action: Optional[str] = None
    direct_object: Optional[str] = None
    direct_object_raw: Optional[str] = None
    indirect_object: Optional[str] = None
    indirect_object_raw: Optional[str] = None
    preposition: Optional[str] = None
    original_input: str = ""
    success: bool = False
    error_message: Optional[str] = None


class ZorkParser:
    """
    An improved Python 3 class to emulate the core functionality of the Zork/Infocom
    sentence parser, optimized for efficiency.

    It tokenizes input, identifies verbs, direct objects, and indirect objects,
    and handles common filler words and multi-word phrases.

    Instructions for Use:
    1. Instantiate the parser, optionally providing custom vocabulary and grammar rules.
       If no arguments are provided, it uses sensible defaults.
       `parser = ZorkParser()`
       `parser = ZorkParser(verbs=my_verbs, nouns=my_nouns, stop_words=my_stop_words, grammar_rules=my_grammar_rules)`
    2. Call the `parse()` method with the player's raw input string.
       `parsed_command = parser.parse("open the rusty door with the skeleton key")`
    3. Check `parsed_command.success` to see if parsing was successful.
    4. Access the parsed components using attributes like `parsed_command.action`,
       `parsed_command.direct_object`, etc.
    5. If `parsed_command.success` is False, `parsed_command.error_message` will
       contain a reason for the failure.
    """

    # --- Default Vocabulary and Grammar Rules ---
    # These are defined as class-level constants. They can be overridden
    # by passing custom dictionaries to the constructor.

    # Maps common verb synonyms to their canonical form.
    # E.g., "get" -> "take", "walk" -> "go".
    _DEFAULT_VERBS: Dict[str, List[str]] = {
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

    # Maps common noun synonyms/phrases to their canonical form.
    # E.g., "keys" -> "key", "mail box" -> "mailbox".
    _DEFAULT_NOUNS: Dict[str, List[str]] = {
        "key": ["key", "keys"],
        "door": ["door", "gate"],
        "lamp": ["lamp", "light", "torch"],
        "sword": ["sword", "blade"],
        "shield": ["shield"],
        "troll": ["troll", "creature"],
        "mailbox": ["mailbox", "mail box", "small mailbox"], # Example of multi-word noun
        "room": ["room", "area", "place"],
        "north": ["north", "n"],
        "south": ["south", "s"],
        "east": ["east", "e"],
        "west": ["west", "w"],
        "up": ["up", "u"],
        "down": ["down", "d"],
        "all": ["all", "everything"], # Special noun for "take all"
        "nothing": ["nothing", "none"],
        "sign": ["sign"]
    }

    # Words to ignore during parsing (articles, common conjunctions, etc.).
    # Using a set for O(1) average time complexity lookups.
    _DEFAULT_STOP_WORDS: Set[str] = {
        "a", "an", "the", "and", "then", "now", "here", "there", "that", "this", "it"
    }

    # Defines valid prepositions for indirect objects, keyed by canonical verb.
    # `None` indicates the verb can take a direct object without a preposition for an indirect object.
    # E.g., "look": [None, "at", "in"] means "look", "look at X", "look in X" are valid.
    # This helps validate the command structure.
    _DEFAULT_GRAMMAR_RULES: Dict[str, List[Optional[str]]] = {
        "take": [None],
        "drop": [None],
        "go": [None],
        "look": [None, "at", "in"],
        "open": [None, "with"], # e.g., "open door", "open door with key"
        "close": [None],
        "attack": [None, "with"], # e.g., "attack troll", "attack troll with sword"
        "read": [None],
        "push": [None],
        "pull": [None]
    }

    def __init__(self,
                 verbs: Optional[Dict[str, List[str]]] = None,
                 nouns: Optional[Dict[str, List[str]]] = None,
                 stop_words: Optional[Set[str]] = None,
                 grammar_rules: Optional[Dict[str, List[Optional[str]]]] = None):
        """
        Initializes the ZorkParser. It pre-processes vocabulary for efficient lookups.

        :param verbs: Custom verb dictionary (overrides default).
        :param nouns: Custom noun dictionary (overrides default).
        :param stop_words: Custom set of stop words (overrides default).
        :param grammar_rules: Custom grammar rules (overrides default).
        """
        # Use provided custom data or fall back to defaults
        effective_verbs = verbs if verbs is not None else self._DEFAULT_VERBS
        effective_nouns = nouns if nouns is not None else self._DEFAULT_NOUNS
        self.stop_words = stop_words if stop_words is not None else self._DEFAULT_STOP_WORDS
        self.grammar_rules = grammar_rules if grammar_rules is not None else self._DEFAULT_GRAMMAR_RULES

        # --- Optimization: Create efficient lookup maps for verbs and nouns ---
        # self._verb_map: Maps every synonym (lowercase) to its canonical verb.
        # This allows O(1) average time complexity lookup for verbs.
        self._verb_map: Dict[str, str] = {
            v_syn.lower(): canonical_v
            for canonical_v, v_list in effective_verbs.items()
            for v_syn in v_list
        }

        # self._noun_map: Maps every noun synonym/phrase (lowercase) to its canonical noun.
        # This allows O(1) average time complexity lookup for nouns.
        self._noun_map: Dict[str, str] = {
            n_syn.lower(): canonical_n
            for canonical_n, n_list in effective_nouns.items()
            for n_syn in n_list
        }

        # --- Optimization: Pre-process multi-word nouns for greedy matching ---
        # self._multi_word_phrases: List of multi-word noun synonyms, sorted by length descending.
        # This ensures that "small mailbox" is checked before "mailbox" when parsing.
        self._multi_word_phrases: List[str] = sorted(
            [syn for syn in self._noun_map if ' ' in syn],
            key=len,
            reverse=True
        )

        # --- Optimization: Create a set of all known prepositions for quick checks ---
        # self._known_prepositions: A set of all prepositions that appear in any grammar rule.
        # This allows O(1) average time complexity lookup for prepositions.
        self._known_prepositions: Set[str] = set(
            p for rules in self.grammar_rules.values() for p in rules if p is not None
        )

    def _tokenize(self, text: str) -> List[str]:
        """
        Splits the input text into a list of lowercase words.
        Removes basic punctuation. This is a simple but efficient tokenization
        suitable for text adventure inputs.

        :param text: The raw input string.
        :return: A list of lowercase word tokens.
        """
        # Use regex to replace non-alphanumeric characters (except spaces) with spaces,
        # then split by whitespace. This handles common punctuation.
        cleaned_text = re.sub(r"[^a-zA-Z0-9\s]", " ", text).lower()
        tokens = [word for word in cleaned_text.split() if word]
        return tokens

    def _find_verb(self, tokens: List[str]) -> Tuple[Optional[str], int]:
        """
        Attempts to find a verb at the beginning of the token list.
        It tries to match the longest possible verb phrase first (e.g., "pick up").

        :param tokens: The list of input tokens.
        :return: A tuple containing the canonical verb (or None) and the number of tokens consumed.
        """
        # Iterate from the longest possible verb phrase down to single words.
        # Max verb phrase length is usually small (e.g., 2 words for "pick up").
        # This avoids redundant checks and ensures multi-word verbs are prioritized.
        for i in range(min(3, len(tokens)), 0, -1): # Check phrases of length 3, 2, then 1
            phrase = " ".join(tokens[:i])
            if phrase in self._verb_map:
                return self._verb_map[phrase], i # Return canonical verb and words consumed
        return None, 0

    def _find_object(self, tokens: List[str], start_idx: int) -> Tuple[Optional[str], Optional[str], int]:
        """
        Attempts to find the longest matching noun phrase (object) in the tokens
        starting from `start_idx`. Prioritizes multi-word nouns for accurate matching.

        :param tokens: The list of input tokens.
        :param start_idx: The index in `tokens` from which to start searching.
        :return: A tuple: (canonical_object, raw_object_text, tokens_consumed_count).
                 Returns (None, None, 0) if no object is found.
        """
        remaining_tokens = tokens[start_idx:]

        # --- Optimization: Greedy matching for multi-word phrases ---
        # Iterate through pre-sorted multi-word noun phrases (longest first).
        # This ensures "small mailbox" is matched before "mailbox".
        for mw_phrase in self._multi_word_phrases:
            mw_tokens_count = len(mw_phrase.split())
            if mw_tokens_count <= len(remaining_tokens):
                # Construct the potential match from the current position in tokens.
                potential_match_raw = " ".join(remaining_tokens[:mw_tokens_count])
                if potential_match_raw in self._noun_map:
                    return self._noun_map[potential_match_raw], potential_match_raw, mw_tokens_count

        # --- Optimization: Single-word noun matching ---
        # If no multi-word phrase matched, check for single-word nouns.
        # Stop words are skipped, but other non-nouns terminate the search for this object.
        for i, token in enumerate(remaining_tokens):
            if token in self._noun_map:
                # Found a single-word noun.
                return self._noun_map[token], token, i + 1
            elif token in self.stop_words:
                # Skip stop words. Continue looking for a noun.
                continue
            else:
                # Encountered a word that is neither a noun nor a stop word.
                # This indicates the end of a potential object phrase.
                break
        return None, None, 0 # No object found

    def parse(self, command_input: str) -> ParsedCommand:
        """
        Parses a Zork-like command string into a structured ParsedCommand object.
        This method orchestrates the tokenization and object/verb identification.

        :param command_input: The raw string input from the player (e.g., "take the rusty key").
        :return: A ParsedCommand object indicating the parsed action, objects, and status.
        """
        parsed_cmd = ParsedCommand(original_input=command_input)
        tokens = self._tokenize(command_input)

        if not tokens:
            parsed_cmd.error_message = "No input provided."
            return parsed_cmd

        # 1. Find Verb: The first significant word(s) should be the verb.
        canonical_verb, verb_consumed_count = self._find_verb(tokens)
        if not canonical_verb:
            parsed_cmd.error_message = f"I don't understand the verb '{tokens[0]}'."
            return parsed_cmd

        parsed_cmd.action = canonical_verb
        # Remaining tokens after the verb.
        remaining_tokens = tokens[verb_consumed_count:]

        # Handle special commands that are typically standalone (e.g., "inventory", "help", "quit").
        # For simplicity, if extra words are present, it's an error.
        if canonical_verb in ["inventory", "help", "quit"]:
            # Check if any non-stop words remain after these simple commands.
            if any(t not in self.stop_words for t in remaining_tokens):
                parsed_cmd.error_message = f"Too many words after '{canonical_verb}'."
                return parsed_cmd
            parsed_cmd.success = True
            return parsed_cmd

        # 2. Find Direct Object: Look for the primary object of the verb.
        obj1_canonical, obj1_raw, obj1_consumed_count = self._find_object(remaining_tokens, 0)

        # Handle "go direction" where direction is the direct object.
        # This is a common pattern in text adventures.
        if canonical_verb == "go" and obj1_canonical:
            parsed_cmd.direct_object = obj1_canonical
            parsed_cmd.direct_object_raw = obj1_raw
            parsed_cmd.success = True
            return parsed_cmd

        # If a direct object was expected but not found.
        # Verbs like 'take', 'open', 'attack' usually require a direct object.
        # 'look' can be standalone or take an object.
        if not obj1_canonical and canonical_verb not in ["look"]:
            parsed_cmd.error_message = f"What do you want to '{canonical_verb}'?"
            return parsed_cmd

        parsed_cmd.direct_object = obj1_canonical
        parsed_cmd.direct_object_raw = obj1_raw

        # Tokens remaining after the direct object (potentially for a preposition or indirect object).
        remaining_tokens_after_obj1 = remaining_tokens[obj1_consumed_count:]

        # 3. Find Preposition and Indirect Object:
        # Iterate through the rest of the tokens to find a valid preposition.
        preposition_found = None
        preposition_start_idx = -1 # Index of preposition within remaining_tokens_after_obj1

        # Retrieve valid prepositions for the current verb from grammar rules.
        valid_prepositions_for_verb = self.grammar_rules.get(canonical_verb, [])

        for i, token in enumerate(remaining_tokens_after_obj1):
            if token in self._known_prepositions:
                # Check if this preposition is allowed for the current verb's grammar.
                if token in valid_prepositions_for_verb:
                    preposition_found = token
                    preposition_start_idx = i
                    break # Found a valid preposition, stop searching for it.
            elif token not in self.stop_words:
                # If we encounter a non-stop-word that's not a known preposition,
                # then there's no valid preposition for an indirect object here.
                break

        if preposition_found:
            parsed_cmd.preposition = preposition_found
            # Now, search for the indirect object immediately after the preposition.
            obj2_tokens_start_idx = preposition_start_idx + 1
            obj2_canonical, obj2_raw, obj2_consumed_count = \
                self._find_object(remaining_tokens_after_obj1, obj2_tokens_start_idx)

            if not obj2_canonical:
                parsed_cmd.error_message = f"What do you want to {preposition_found}?"
                parsed_cmd.success = False # Cannot fully parse
                return parsed_cmd

            parsed_cmd.indirect_object = obj2_canonical
            parsed_cmd.indirect_object_raw = obj2_raw

            # Check for any unparsed tokens after the full command (verb + obj1 + prep + obj2).
            # If any non-stop words remain, it indicates an unparsed part of the command.
            unparsed_suffix_tokens = \
                remaining_tokens_after_obj1[obj2_tokens_start_idx + obj2_consumed_count:]
            if any(t not in self.stop_words for t in unparsed_suffix_tokens):
                parsed_cmd.error_message = \
                    f"I don't understand '{' '.join(unparsed_suffix_tokens)}' after the command."
                parsed_cmd.success = False
                return parsed_cmd
        else:
            # If no preposition was found, check if there are any unparsed non-stop words
            # that were not part of the direct object.
            if any(t not in self.stop_words for t in remaining_tokens_after_obj1):
                parsed_cmd.error_message = \
                    f"I don't understand '{' '.join(remaining_tokens_after_obj1)}' after the direct object."
                parsed_cmd.success = False
                return parsed_cmd

        parsed_cmd.success = True # If we reached here, the command was successfully parsed.
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
        "push button",
        "pull lever",
        "invalid command",
        "take", # Missing object
        "open door with", # Missing indirect object
        "attack troll with", # Missing indirect object
        "look around room", # "around" not a recognized preposition for "look"
        "" # Empty input
    ]

    print("--- Improved Python3 Zork Parser Test ---")
    for cmd_str in test_commands:
        print(f"\nParsing: '{cmd_str}'")
        parsed = parser.parse(cmd_str)
        if parsed.success:
            print(f"  Success! Action: '{parsed.action}'")
            if parsed.direct_object:
                print(f"  Direct Object: '{parsed.direct_object}' (Raw: '{parsed.direct_object_raw}')")
            if parsed.preposition:
                print(f"  Preposition: '{parsed.preposition}'")
            if parsed.indirect_object:
                print(f"  Indirect Object: '{parsed.indirect_object}' (Raw: '{parsed.indirect_object_raw}')")
        else:
            print(f"  Failed: {parsed.error_message}")

    # Demonstrate adding custom vocabulary
    print("\n--- Adding Custom Vocabulary and Testing ---")
    custom_verbs = {
        "eat": ["eat", "devour"],
        "drink": ["drink"]
    }
    custom_nouns = {
        "apple": ["apple", "red apple", "green apple"],
        "water": ["water", "pure water", "fresh water"]
    }
    custom_grammar = {
        "eat": [None],
        "drink": [None]
    }

    # Create a new parser instance with custom (merged) vocabulary
    # In a real application, you might load these from configuration files.
    merged_verbs = {**ZorkParser._DEFAULT_VERBS, **custom_verbs}
    merged_nouns = {**ZorkParser._DEFAULT_NOUNS, **custom_nouns}
    merged_grammar = {**ZorkParser._DEFAULT_GRAMMAR_RULES, **custom_grammar}

    custom_parser = ZorkParser(verbs=merged_verbs, nouns=merged_nouns, grammar_rules=merged_grammar)

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

    parsed_custom = custom_parser.parse("look in the mailbox")
    if parsed_custom.success:
        print(f"Parsing 'look in the mailbox' -> Action: '{parsed_custom.action}', Direct Object: '{parsed_custom.direct_object}', Preposition: '{parsed_custom.preposition}'")
    else:
        print(f"Parsing 'look in the mailbox' -> Failed: {parsed_custom.error_message}")