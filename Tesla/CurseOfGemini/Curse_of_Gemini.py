#!/usr/bin/python3
# -*- coding: utf-8 -*-
__title__ = 'Curse of Gemini'
__author__ = 'rendier'

import curses
# ~ import threading
# ~ import queue
from curses import start_color

#import limits
#import curl
import os
import uuid
import json # For simple storage of the ID
from dataclasses import dataclass, field
from typing import List, Dict, Optional
import datetime

DEBUG = True
DEVICE_ID_FILE = "device_id.json"

@dataclass
class GeminiEnvVar():
    DEBUG_ON = 0
    user_name: str = os.environ['USER']

    # --- API Configuration (from Environment) ---
    gemini_api_key: str = field(init=False, repr=False)  # Marked as init=False because it's loaded from env
    # repr=False to avoid printing sensitive key

    # --- Gemini Model Parameters ---
    model_name: str = "gemini-1.5-flash"  # Default model
    temperature: float = 0.9
    top_p: float = 0.95
    top_k: int = 40
    max_output_tokens: int = 2048
    system_instruction: str = ""  # Optional, sets initial AI persona/context

    # --- Client-Specific Settings ---
    device_id: str = field(init=False)  # Loaded/generated on first run
    chat_history_limit: int = 200  # How many messages to keep in memory for scrollback
    database_path: str = "./chat_memory.db"  # Path to your SQLite database
    log_file_path: str = "app_log.log"  # For application logging
    gemini_name: str = "Gemini"  # Display name for the AI in chat
    # Potentially for UI:
    message_wrap_width: int = 78  # Example default for terminal width

    def __post_init__(self):
        # Load API key from environment variable
        #api_key = os.getenv("GEMINI_API_KEY")
        #if not api_key:
        #    raise ValueError("GEMINI_API_KEY environment variable is not set.")

        self.gemini_api_key = "AIzaSyB6yfXQ5BuiAfg8KAt1A0RrrG2sx9GUqcQ" # api_key

        # Load or create device ID
        self.device_id = self._get_or_create_device_id()

    def _get_or_create_device_id(self) -> str:
        """
        Retrieves a unique device ID from a local file, or generates a new one
        and saves it if it doesn't exist.
        """
        device_id = None
        if os.path.exists(DEVICE_ID_FILE):
            try:
                with open(DEVICE_ID_FILE, 'r') as f:
                    data = json.load(f)
                    device_id = data.get("device_id")
            except (json.JSONDecodeError, KeyError):
                # File exists but is malformed, or ID not found. Regenerate.
                print(f"Warning: {DEVICE_ID_FILE} exists but is invalid or missing ID. Generating new ID.")

        if device_id is None:
            device_id = str(uuid.uuid4())  # Generate a UUID
            with open(DEVICE_ID_FILE, 'w') as f:
                json.dump({"device_id": device_id}, f)
            # print(f"New device ID generated and saved: {device_id}") # Optional debug print
        # else:
        # print(f"Existing device ID loaded: {device_id}") # Optional debug print

        return device_id

@dataclass
class WordContextData:
    """
    A dataclass to represent a comprehensive understanding of a single word,
    including its linguistic, semantic, and contextual nuances.
    This aims to model a human-like depth of word knowledge.
    """

    # --- Core Linguistic Identity ---
    text: str = field(metadata={"comment": "The word itself (e.g., 'bank')."})
    lemma: str = field(metadata={"comment": "The base form of the word (e.g., 'run' for 'running', 'ran')."})
    part_of_speech: List[str] = field(default_factory=list, metadata={"comment": "Grammatical categories (e.g., ['noun', 'verb', 'adjective'])."})
    phonetic_transcription: Optional[str] = field(default=None, metadata={"comment": "IPA phonetic transcription (e.g., '/bæŋk/'). Useful for homophones."})

    # --- Definitions and Core Semantics ---
    definitions: List[str] = field(default_factory=list, metadata={"comment": "Standard dictionary definitions for each sense of the word."})
    connotations: List[str] = field(default_factory=list, metadata={"comment": "Emotional, cultural, or subjective associations (e.g., 'freedom' -> positive, 'slimy' -> negative)."})
    denotations: List[str] = field(default_factory=list, metadata={"comment": "Explicit, literal meanings (often overlaps with definitions but can be more specific)."})
    sentiment_scores: Dict[str, float] = field(default_factory=dict, metadata={"comment": "Numerical scores for associated sentiments (e.g., {'positive': 0.8, 'negative': 0.1, 'neutral': 0.1})."})

    # --- Lexical Relationships ---
    synonyms: List[str] = field(default_factory=list, metadata={"comment": "Words with similar meanings."})
    antonyms: List[str] = field(default_factory=list, metadata={"comment": "Words with opposite meanings."})
    hypernyms: List[str] = field(default_factory=list, metadata={"comment": "Broader categories (e.g., 'animal' for 'dog', 'furniture' for 'chair')."})
    hyponyms: List[str] = field(default_factory=list, metadata={"comment": "More specific instances (e.g., 'poodle' for 'dog', 'stool' for 'chair')."})
    meronyms: List[str] = field(default_factory=list, metadata={"comment": "Parts of the word's concept (e.g., 'wheel' for 'car', 'page' for 'book')."})
    holonyms: List[str] = field(default_factory=list, metadata={"comment": "The whole the word is a part of (e.g., 'forest' for 'tree', 'sentence' for 'word')."})
    related_words: List[str] = field(default_factory=list, metadata={"comment": "Other loosely associated or semantically related words."})

    # --- Contexts and Usage ---
    immediate_contexts: List[str] = field(default_factory=list, metadata={"comment": "Common preceding/succeeding words or short phrases where the word appears (e.g., 'river bank', 'bank account')."})
    larger_contexts: List[str] = field(default_factory=list, metadata={"comment": "Typical sentence structures, topics, or domains where the word is frequently used."})
    usage_examples: List[str] = field(default_factory=list, metadata={"comment": "Full example sentences demonstrating different meanings or uses."})
    collocations: List[str] = field(default_factory=list, metadata={"comment": "Words that frequently co-occur with this word (e.g., 'heavy rain', 'make a decision')."})
    idiomatic_expressions: List[str] = field(default_factory=list, metadata={"comment": "Common idioms or fixed phrases containing the word (e.g., 'break a leg' for 'leg')."})

    # --- Nuance and Ambiguity ---
    tones: List[str] = field(default_factory=list, metadata={"comment": "Associated emotional/attitudinal tones (e.g., ['formal', 'informal', 'sarcastic', 'joyful', 'neutral'])."})
    homonyms: List[str] = field(default_factory=list, metadata={"comment": "Words spelled the same but with different meanings and origins (e.g., 'bat' (animal) vs. 'bat' (baseball))."})
    homophones: List[str] = field(default_factory=list, metadata={"comment": "Words pronounced the same but with different spellings/meanings (e.g., 'to', 'too', 'two')."})
    polysemy_senses: List[str] = field(default_factory=list, metadata={"comment": "Distinct meanings of the *same* word (e.g., 'bank' as a financial institution vs. 'bank' as a river edge). Each entry could be a short description or a unique ID linking to a specific definition."})

    # --- Temporal and Geographical Usage ---
    historical_colloquialisms: Dict[str, List[str]] = field(default_factory=dict, metadata={"comment": "Mapping of historical periods (e.g., '1920s', 'Victorian Era') to colloquial meanings/usages."})
    current_colloquialisms: Dict[str, List[str]] = field(default_factory=dict, metadata={"comment": "Mapping of current regions/social groups (e.g., 'US South', 'Gen Z Slang') to colloquial meanings."})
    regional_variations: Dict[str, List[str]] = field(default_factory=dict, metadata={"comment": "Mapping of geographical regions to specific meanings, pronunciations, or preferred synonyms."})
    temporal_shifts: Dict[str, List[str]] = field(default_factory=dict, metadata={"comment": "How the word's meaning or usage has changed over different time periods (e.g., 'gay' from 'joyful' to 'homosexual')."})

    # --- Pragmatic and Social Context ---
    register: List[str] = field(default_factory=list, metadata={"comment": "Appropriate social or professional contexts (e.g., ['formal', 'casual', 'academic', 'technical', 'slang'])."})
    domain_specific_meanings: Dict[str, List[str]] = field(default_factory=dict, metadata={"comment": "Meanings specific to certain fields or domains (e.g., 'bug' in entomology vs. software engineering)."})

    # --- Metadata for your Data Collection ---
    last_updated: datetime.datetime = field(default_factory=datetime.datetime.now, metadata={"comment": "Timestamp when this word's data was last updated."})
    source_corpus_ids: List[str] = field(default_factory=list, metadata={"comment": "IDs or references to the texts/corpora from which this information was derived."})
    confidence_score: Optional[float] = field(default=None, metadata={"comment": "Confidence level in the accuracy/completeness of this word's data (0.0 to 1.0)."})

    # --- Variables for 'Teaching' Gemini ---
    # These would be derived from the above data, or explicitly added by your system
    # to highlight key aspects you want the AI to learn.
    grounding_references: List[str] = field(default_factory=list, metadata={"comment": "Links or references to real-world entities, concepts, or sensory experiences this word aims to ground (e.g., 'red' -> reference to color spectrum data; 'jump' -> reference to kinematic concepts). This is crucial for 'grounded comprehension'."})
    associated_mental_models: List[str] = field(default_factory=list, metadata={"comment": "Descriptions or identifiers of abstract mental models this word activates (e.g., 'journey' -> 'sequence of events', 'progress', 'effort')."})
    common_misunderstandings: List[str] = field(default_factory=list, metadata={"comment": "Common ways this word is misused or misinterpreted, and why."})

# Chat Window

class GeminiChat():


    def __init__(self, **kwargs):
        self.min_x = 0
        self.min_y = 0
        self.max_x = 0
        self.max_y = 0
        self.gemini_chat_window = None
        self.gemini_input_window = None
        self.gemini_border_window = None

        self.Gemini = self.start_curse()
        self.curse_windows()
        while True:
            self.stdscr.getch()

    def text_wrapping(self, text: str, width: int, ):
        lines = ""
        current_line = 0
        start = 0

        while start < len(text):
            end = text.find(" ", start)
            if end == "":
                current_line += text[start:]
                start = len(text)
            else:

                word = text[start, (end - start)]
                if len(current_line) + len(word) + 1 > width:
                    if current_line == "":
                        lines += current_line

                    current_line = word

                else:
                    if current_line != "":
                        current_line += " "

                    current_line += word

                start = end + 1

            if len(current_line) > width:
                lines += current_line[0:width]
                current_line = current_line[width]


        if current_line != "":
            lines += current_line

        return lines



        return

    def start_curse(self):
        self.stdscr = curses.initscr()
        curses.cbreak()
        curses.noecho()
        self.stdscr.keypad(True)
        self.max_y, self.max_x = self.stdscr.getmaxyx()
        if DEBUG == True:
            print ("Max Y =: ", self.max_y, "Max X =: ", self.max_x)
        curses.curs_set(1)
        curses.set_escdelay(3)
        # if curses.has_colors():
        #     curses.start_color()
        #     curses.init_pair(1, COLOR_RED, COLOR_BLACK)
        #     curses.init_pair(2, COLOR_CYAN, COLOR_BLACK)
        #     curses.init_pair(3, COLOR_GREEN, COLOR_BLACK)
        if DEBUG == True:
            print(self.stdscr)
        return self.stdscr

    def curse_windows(self):

        self.chat_h = self.max_y - 5
        self.chat_w = self.max_x - 2

        # Create Border Window
        self.gemini_border_window = self.stdscr.newwin(self.max_y, self.max_x, 0, 0)        # Chat Window (Main Display)
        self.gemini_border_window.box()
        self.gemini_border_window.refresh()

        # Create Chat Window
        self.gemini_chat_window = self.stdscr.newwin(self.chat_h, self.chat_w)
        self.gemini_chat_window.box()
        self.gemini_chat_window.scrollok(True)
        self.gemini_chat_window.refresh()

        # Create Input Window
        self.input_h = 3
        self.input_w = self.max_x - 2
        self.gemini_input_window = curses.newwin(self.input_h + 2, self.input_w + 2, 0, 0)
        #self.gemini_input_window = self.stdscr.derwin(self.input_h + 2, self.input_w + 2)
        self.gemini_input_window.box()
        self.gemini_input_window.refresh()

        return

    def end_curse(self):

        curses.nocbreak()
        self.stdscr.keypad(False)
        curses.echo()
        curses.endwin()

        return

# Example usage in your main script:
if __name__ == "__main__":
    GemEnVar = GeminiEnvVar()
    #WordConData = WordContextData()
    Gemini = GeminiChat()
    print(f"This session's device UUID: {GemEnVar.device_id}")
    if DEBUG == True:
        print("DEBUG\n\nGemEnVar:\n\n", GemEnVar)

    # Now, when you store chat logs or memories in your database,
    # you can include `my_device_uuid` with each entry.
    # Example (conceptual):
    # db_connection.execute("INSERT INTO chat_log (device_id, message, timestamp) VALUES (?, ?, ?)",
    #                      (my_device_uuid, "Hello Gemini", current_timestamp))
