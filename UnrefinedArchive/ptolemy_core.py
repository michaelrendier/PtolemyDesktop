#!/usr/bin/env python3
"""
ptolemy_core.py
===============
Ptolemy Neural Language Architecture — Core Modular Framework

Naked, language-independent neural building blocks that can be
assembled into any language understanding or production system.

Architecture overview:
─────────────────────────────────────────────────────────────
  CharacterNeuron          — understands characters in context,
                             language-independently. One neuron
                             per character in output layer.
                             Resolves ambiguity: < as math vs HTML vs music.

  LexicalDimensionNeuron   — classifies word dimensional complexity.
                             Structural (1D: 'the') vs Embodied (nD: 'petrichor').
                             Gates which downstream networks activate.

  GrammarNeuron            — language-specific grammatical rules.
                             English: complex, multi-root rule system.
                             Spanish: phonetic, minimal exception rules.
                             Latin: case-based, word-order free.
                             Loads rules from /etc/ptolemy/grammar/<lang>.json

  WordMonadNetwork         — one small network per word.
                             Built on top of frozen CharacterNeuron.
                             Stores SemanticWord (LLM_Datatype_Cl.py) as
                             its knowledge state.
                             Trained separately, checkpointed individually.

  WernickeNetwork          — Ptolemy's Ears. Language understanding.
                             Transformer encoder. Bidirectional.
                             Trained: input text → semantic representation.

  BrocaNetwork             — Ptolemy's Voice. Language production.
                             Autoregressive decoder.
                             Trained: semantic representation → output text.

  LanguageNeuron           — complete language capability as one importable unit.
                             Contains: CharacterNeuron (frozen) +
                                       WordMonadDictionary +
                                       GrammarNeuron +
                                       LexicalDimensionNeuron +
                                       WernickeNetwork +
                                       BrocaNetwork

  PtolemyFace              — a complete language model instance.
                             One or more LanguageNeurons combined.
                             english_us + latin + python_code = multilingual face.

Design principles:
──────────────────
  - All networks are NAKED: no language hardcoded at class level.
    Language is a parameter, not an assumption.
  - Train once, freeze, import: CharacterNeuron trains once for all languages.
  - Modular checkpointing: every component saves/loads independently.
  - SemanticWord (from LLM_Datatype_Cl.py) is the knowledge representation.
  - Grammar rules live in config files, not code.
  - The 'it' problem is solved structurally: Class 1 words are pointer nodes,
    not statistical associations.

Compatible with:
  Python 3.10+
  PyTorch 2.0+
  LLM_Datatype_Cl.py (SemanticWord datatype)

Author: Ptolemy project / HyperWebster architecture
License: MIT
"""

import os
import json
import time
import math
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader

# Import the SemanticWord datatype
try:
    from LLM_Datatype_Cl import (
        SemanticWord, HyperWebster, ContextualTone,
        PartOfSpeech, SemanticLayer, Etymology,
        PhonologicalProfile, SyntacticProfile
    )
    SEMANTIC_WORD_AVAILABLE = True
except ImportError:
    SEMANTIC_WORD_AVAILABLE = False
    print("WARNING: LLM_Datatype_Cl.py not found. "
          "WordMonad knowledge layer will be disabled.")


# =============================================================================
# Word Classification — the dimensional complexity taxonomy
# =============================================================================

class WordClass(Enum):
    """
    Dimensional complexity classification.

    This determines storage strategy, network depth, and whether
    a word gets a full WordMonad or a lightweight grammar node.

    CLASS_1: Structural — almost no semantic content.
             Meaning is purely relational/grammatical.
             Examples: the, a, it, in, on, and, but, I, you
             Note: 'I' may not exist in some languages (Algonquian).
             Note: articles may not exist (Mandarin, Latin).
             Storage: ~200 bytes, static grammar node, never grows.

    CLASS_2: Concrete/Common — sensory, physical, categorical.
             Stable meaning with contextual inflection.
             Examples: tree, run, red, house, eat, water
             Storage: 4.5KB base → ~50KB experienced.

    CLASS_3: Experientially rich — nostalgia, scent, emotion, poetry.
             High dimensional. Every encounter potentially novel.
             Examples: petrichor, vellichor, hiraeth, redwoods
             Storage: 4.5KB base → grows with each novel usage.

    CLASS_4: Proper contextual compounds — capitalization + context
             signals a specific cultural/experiential referent.
             Examples: The Redwoods, The Nightmare, The Way, The Universe
             These are NOT derivable from their component words.
             Storage: separate entry from lowercase version.
    """
    CLASS_1_STRUCTURAL        = 1
    CLASS_2_CONCRETE          = 2
    CLASS_3_EXPERIENTIAL      = 3
    CLASS_4_PROPER_COMPOUND   = 4


# =============================================================================
# Configuration
# =============================================================================

PTOLEMY_BASE = Path(os.environ.get('PTOLEMY_BASE', '/etc/ptolemy'))
CHECKPOINT_BASE = Path(os.environ.get('PTOLEMY_CHECKPOINTS', '~/.ptolemy')).expanduser()

# Unicode coverage: all currently assigned codepoints + room for growth
UNICODE_VOCAB_SIZE = 155000   # covers all current Unicode + headroom

# Context window for character-level disambiguation
CHAR_CONTEXT_WINDOW = 32

# Embedding dimensions — tunable per hardware budget
CHAR_EMBED_DIM    = 128
WORD_HIDDEN_DIM   = 256
SEMANTIC_DIM      = 512
GRAMMAR_HIDDEN    = 256


# =============================================================================
# Layer 0: CharacterNeuron
# =============================================================================

class CharacterNeuron(nn.Module):
    """
    Language-independent character context network.

    Trained ONCE across all languages and scripts. Then frozen.
    Imported as the first layer of every downstream network.

    Architecture:
      Embedding → CNN (bigram/trigram/quadgram filters) →
      Transformer (long-range context) → Output layer

    Output layer: one neuron per character in active script.

    The critical disambiguation this network learns:
      < in "x < y"        → mathematical less-than (TECHNICAL tone)
      < in "<div>"        → HTML open tag (TECHNICAL tone)
      < in "mp < ff"      → musical dynamics (EMBODIED tone)
      'I' as pronoun      → structural/referential (CLASS_1)
      'I' in chemical     → iodine symbol (TECHNICAL)

    This disambiguation comes from the context window, not
    from hardcoded rules. The network learns the patterns.

    Saved to: {CHECKPOINT_BASE}/char_neuron.pt
    Once trained, NEVER retrained. Only ever frozen and imported.

    Args:
        vocab_size:      Number of Unicode codepoints to cover.
        context_window:  Characters of context on each side.
        embed_dim:       Embedding dimension per character.
        n_heads:         Transformer attention heads.
        n_layers:        Transformer encoder layers.
    """

    def __init__(
        self,
        vocab_size:     int = UNICODE_VOCAB_SIZE,
        context_window: int = CHAR_CONTEXT_WINDOW,
        embed_dim:      int = CHAR_EMBED_DIM,
        n_heads:        int = 8,
        n_layers:       int = 4,
    ):
        super().__init__()
        self.vocab_size     = vocab_size
        self.context_window = context_window
        self.embed_dim      = embed_dim

        # Character embedding table — one vector per Unicode codepoint
        self.embedding = nn.Embedding(
            num_embeddings=vocab_size,
            embedding_dim=embed_dim,
            padding_idx=0
        )

        # CNN layers — local pattern detection
        # Filter sizes 2,3,4 detect bigrams, trigrams, quadgrams
        # These catch: th, ing, tion, pre-, un-, etc.
        # Also catch: </  />  <!--  ->  =>  ::  etc.
        self.conv2 = nn.Conv1d(embed_dim, 64, kernel_size=2, padding=1)
        self.conv3 = nn.Conv1d(embed_dim, 64, kernel_size=3, padding=1)
        self.conv4 = nn.Conv1d(embed_dim, 64, kernel_size=4, padding=2)
        # Combined: 192 channels
        self.conv_norm = nn.LayerNorm(192)

        # Transformer encoder — long-range context resolution
        # This is what resolves < as math vs HTML vs music:
        # it can see the broader sentence context
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=192,
            nhead=n_heads,
            dim_feedforward=512,
            dropout=0.1,
            batch_first=True,
        )
        self.transformer = nn.TransformerEncoder(
            encoder_layer,
            num_layers=n_layers,
        )

        # Output heads
        # Primary: predict next character (language modeling)
        self.char_output = nn.Linear(192, vocab_size)

        # Secondary: classify contextual role of current character
        # This IS the neuron that feeds into WordMonad networks
        # Roles: alphabetic, numeric, punctuation, operator,
        #        markup, whitespace, combining, unknown
        self.role_output = nn.Linear(192, 16)

        # Tertiary: writing system classifier
        # Latin, Greek, Cyrillic, Arabic, Hebrew, Han, Devanagari,
        # Coptic, Demotic, Egyptian Hieroglyphic, etc.
        self.script_output = nn.Linear(192, 64)

    def forward(
        self,
        char_ids: torch.Tensor,   # (batch, seq_len)
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Forward pass.

        Args:
            char_ids: Integer tensor of Unicode codepoint IDs.
                      Shape: (batch_size, sequence_length)

        Returns:
            char_logits:   (batch, seq, vocab_size) — next char prediction
            role_logits:   (batch, seq, 16)         — character role
            script_logits: (batch, seq, 64)         — writing system
        """
        # Embed characters
        x = self.embedding(char_ids)        # (B, L, embed_dim)

        # CNN: operate over sequence dimension
        x_t = x.transpose(1, 2)            # (B, embed_dim, L)
        c2 = F.relu(self.conv2(x_t))[:, :, :x.size(1)]
        c3 = F.relu(self.conv3(x_t))[:, :, :x.size(1)]
        c4 = F.relu(self.conv4(x_t))[:, :, :x.size(1)]
        # Concatenate along channel dimension
        conv_out = torch.cat([c2, c3, c4], dim=1)   # (B, 192, L)
        conv_out = conv_out.transpose(1, 2)          # (B, L, 192)
        conv_out = self.conv_norm(conv_out)

        # Transformer: resolve long-range context
        context = self.transformer(conv_out)         # (B, L, 192)

        # Output heads
        char_logits   = self.char_output(context)    # (B, L, vocab_size)
        role_logits   = self.role_output(context)    # (B, L, 16)
        script_logits = self.script_output(context)  # (B, L, 64)

        return char_logits, role_logits, script_logits

    def get_features(self, char_ids: torch.Tensor) -> torch.Tensor:
        """
        Extract character feature vectors without classification heads.
        Used when importing as frozen first layer into downstream networks.

        Args:
            char_ids: (batch, seq_len) integer tensor

        Returns:
            features: (batch, seq_len, 192) contextual character features
        """
        x = self.embedding(char_ids)
        x_t = x.transpose(1, 2)
        c2 = F.relu(self.conv2(x_t))[:, :, :x.size(1)]
        c3 = F.relu(self.conv3(x_t))[:, :, :x.size(1)]
        c4 = F.relu(self.conv4(x_t))[:, :, :x.size(1)]
        conv_out = torch.cat([c2, c3, c4], dim=1).transpose(1, 2)
        conv_out = self.conv_norm(conv_out)
        return self.transformer(conv_out)

    def save(self, path: Optional[str] = None) -> str:
        """Save checkpoint. Returns path written."""
        path = path or str(CHECKPOINT_BASE / 'char_neuron.pt')
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        torch.save({
            'model_state': self.state_dict(),
            'vocab_size':  self.vocab_size,
            'embed_dim':   self.embed_dim,
            'timestamp':   time.time(),
            'version':     1,
        }, path)
        print(f"CharacterNeuron saved → {path}")
        return path

    @classmethod
    def load(cls, path: Optional[str] = None, freeze: bool = True) -> 'CharacterNeuron':
        """
        Load from checkpoint and optionally freeze all weights.

        Args:
            path:   Checkpoint path. Defaults to CHECKPOINT_BASE/char_neuron.pt
            freeze: If True, no gradients flow through this network.
                    Always True when importing into downstream networks.

        Returns:
            Loaded CharacterNeuron instance.
        """
        path = path or str(CHECKPOINT_BASE / 'char_neuron.pt')
        ckpt = torch.load(path, map_location='cpu')
        net  = cls(
            vocab_size=ckpt.get('vocab_size', UNICODE_VOCAB_SIZE),
            embed_dim=ckpt.get('embed_dim',   CHAR_EMBED_DIM),
        )
        net.load_state_dict(ckpt['model_state'])
        if freeze:
            for param in net.parameters():
                param.requires_grad = False
            net.eval()
            print(f"CharacterNeuron loaded (frozen) ← {path}")
        else:
            print(f"CharacterNeuron loaded (trainable) ← {path}")
        return net


# =============================================================================
# Layer 1: LexicalDimensionNeuron
# =============================================================================

class LexicalDimensionNeuron(nn.Module):
    """
    Classifies words by dimensional complexity (WordClass 1-4).

    This is the gating network. Its output determines:
    - Which downstream networks activate for this word
    - What storage strategy applies
    - Whether reference resolution (structural) or
      semantic lookup (monad) is used

    Critical for the 'it' problem:
      'it' → CLASS_1 → pointer/reference resolution node
      No statistical associations stored. Cannot drift.
      Resolution is structural: find nearest compatible antecedent.

    'The Redwoods' → CLASS_4 → separate monad from 'redwoods'
      Capitalization + article = cultural/experiential referent.
      Not derivable from component words.

    Args:
        char_feature_dim: Output dimension of CharacterNeuron (192).
        hidden_dim:       Internal hidden layer size.
        language:         Language code (en_us, la, es, etc.)
                          Used to load language-specific class hints.
    """

    def __init__(
        self,
        char_feature_dim: int = 192,
        hidden_dim:       int = 128,
        language:         str = 'en_us',
    ):
        super().__init__()
        self.language = language

        # Aggregate character features into word representation
        # (pool over character sequence)
        self.word_pooler = nn.Sequential(
            nn.Linear(char_feature_dim, hidden_dim),
            nn.GELU(),
            nn.Linear(hidden_dim, hidden_dim),
        )

        # Attention pooling — weight characters by importance
        self.attention = nn.Linear(char_feature_dim, 1)

        # Classification head: 4 word classes
        self.classifier = nn.Linear(hidden_dim, 4)

        # Load language-specific structural word list
        # (Class 1 words differ by language)
        self._class1_words = self._load_class1_words(language)

    def _load_class1_words(self, language: str) -> set:
        """
        Load the structural word list for this language.

        These are words that are definitionally Class 1 —
        no neural classification needed, rule-based override.

        For English: pronouns, articles, prepositions, conjunctions
        For Mandarin: (no articles — empty article set)
        For Latin: (no articles — empty article set)
        For Algonquian: (no standalone 'I' — different pronoun system)
        """
        grammar_path = PTOLEMY_BASE / 'grammar' / language / 'class1_words.json'
        if grammar_path.exists():
            with open(grammar_path) as f:
                return set(json.load(f))
        # Fallback: English defaults
        return {
            'the', 'a', 'an', 'this', 'that', 'these', 'those',
            'i', 'you', 'he', 'she', 'it', 'we', 'they',
            'me', 'him', 'her', 'us', 'them', 'my', 'your',
            'his', 'its', 'our', 'their', 'who', 'what', 'which',
            'in', 'on', 'at', 'by', 'for', 'with', 'from', 'to',
            'of', 'about', 'as', 'into', 'through', 'during',
            'and', 'but', 'or', 'nor', 'yet', 'so', 'although',
            'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will',
            'would', 'could', 'should', 'may', 'might', 'shall',
            'not', 'no', 'nor', 'neither',
        }

    def forward(
        self,
        char_features: torch.Tensor,  # (batch, seq_len, 192)
        raw_token:     str = '',
    ) -> Tuple[torch.Tensor, WordClass]:
        """
        Classify word dimensional complexity.

        Rule-based override for known Class 1 words —
        no neural computation needed, just a set lookup.
        This is how 'it' becomes a structural pointer,
        not a statistical association.

        Args:
            char_features: Output of CharacterNeuron.get_features()
            raw_token:     The actual word string for rule-based check.

        Returns:
            logits:     (batch, 4) classification scores
            word_class: WordClass enum — the classification
        """
        # Rule-based Class 1 override — no neural cost
        # This is the fix for the 'it' drift problem
        if raw_token.lower().strip() in self._class1_words:
            dummy = torch.zeros(char_features.size(0), 4)
            dummy[:, 0] = 10.0  # strong Class 1 signal
            return dummy, WordClass.CLASS_1_STRUCTURAL

        # Class 4 check: proper compound (starts with capital The/A/An
        # followed by capitalized noun — "The Redwoods", "The Nightmare")
        tokens = raw_token.strip().split()
        if (len(tokens) >= 2
                and tokens[0] in {'The', 'A', 'An'}
                and tokens[1][0].isupper()):
            dummy = torch.zeros(char_features.size(0), 4)
            dummy[:, 3] = 10.0  # strong Class 4 signal
            return dummy, WordClass.CLASS_4_PROPER_COMPOUND

        # Neural classification for Class 2/3
        # Attention pooling over character sequence
        attn_weights = F.softmax(
            self.attention(char_features), dim=1)  # (B, L, 1)
        pooled = (char_features * attn_weights).sum(dim=1)  # (B, 192)
        hidden = self.word_pooler(pooled)                    # (B, hidden)
        logits = self.classifier(hidden)                     # (B, 4)

        predicted = logits.argmax(dim=-1)[0].item()
        word_class = list(WordClass)[predicted]
        return logits, word_class


# =============================================================================
# Layer 2: GrammarNeuron
# =============================================================================

class GrammarNeuron(nn.Module):
    """
    Language-specific grammatical rule network.

    One instance per language. Not shared between languages.
    Learns the rule system for its specific language from
    annotated corpora.

    English: complex multi-root rules (Latin, French, Anglo-Saxon,
             Greek, Norse, Arabic, and more contributing rule sets).
             Irregular verbs, phrasal verbs, article system,
             complex tense/aspect interactions.

    Spanish: phonetically regular, small exception set,
             gendered nouns, verb conjugation by ending,
             ser vs estar distinction.

    Latin:   case system (nominative, accusative, genitive,
             dative, ablative, vocative), no articles,
             word order free, verb at end convention.

    Python:  indentation-based scope, colon endings,
             snake_case convention, operator precedence.

    HTML/CSS/JS: tag nesting rules, selector specificity,
                 event model, DOM tree structure.

    Grammar rules are stored in:
      /etc/ptolemy/grammar/{language}/rules.json

    The network learns which rules apply when — the
    structural knowledge of when 'whom' vs 'who' is correct,
    when 'lay' vs 'lie' applies, when subjunctive is needed.

    Args:
        language:    Language code. Determines which rule file loads.
        hidden_dim:  Internal representation size.
        input_dim:   Input feature dimension (from char network).
    """

    def __init__(
        self,
        language:   str = 'en_us',
        hidden_dim: int = GRAMMAR_HIDDEN,
        input_dim:  int = 192,
    ):
        super().__init__()
        self.language = language
        self._rules   = self._load_grammar_rules(language)
        n_rules        = len(self._rules)

        # Bidirectional LSTM — grammar requires seeing both
        # what came before AND what comes after
        # (subject-verb agreement requires seeing the verb
        #  to check the subject, which came before it)
        self.lstm = nn.LSTM(
            input_size=input_dim,
            hidden_size=hidden_dim,
            num_layers=2,
            bidirectional=True,
            dropout=0.1,
            batch_first=True,
        )

        # Rule applicability head
        # Which grammatical rules are active in this context?
        self.rule_head = nn.Linear(hidden_dim * 2, max(n_rules, 1))

        # Parse structure head
        # What is the grammatical role of the current token?
        self.parse_head = nn.Linear(hidden_dim * 2, 32)

        # Grammatical error detection
        self.error_head = nn.Linear(hidden_dim * 2, 2)  # correct/incorrect

    def _load_grammar_rules(self, language: str) -> List[dict]:
        """Load grammar rule definitions from config file."""
        rules_path = PTOLEMY_BASE / 'grammar' / language / 'rules.json'
        if rules_path.exists():
            with open(rules_path) as f:
                return json.load(f)
        return []

    def forward(
        self,
        char_features: torch.Tensor,  # (batch, seq_len, input_dim)
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Apply grammar analysis to a sequence.

        Args:
            char_features: Character-level features from CharacterNeuron.

        Returns:
            rule_logits:  (batch, seq, n_rules) — active grammar rules
            parse_logits: (batch, seq, 32)      — grammatical roles
            error_logits: (batch, seq, 2)       — grammatical correctness
        """
        lstm_out, _ = self.lstm(char_features)  # (B, L, hidden*2)
        rule_logits  = self.rule_head(lstm_out)
        parse_logits = self.parse_head(lstm_out)
        error_logits = self.error_head(lstm_out)
        return rule_logits, parse_logits, error_logits

    def save(self, path: Optional[str] = None) -> str:
        path = path or str(
            CHECKPOINT_BASE / 'grammar' / f'{self.language}.pt')
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        torch.save({
            'model_state': self.state_dict(),
            'language':    self.language,
            'n_rules':     len(self._rules),
            'timestamp':   time.time(),
        }, path)
        print(f"GrammarNeuron[{self.language}] saved → {path}")
        return path

    @classmethod
    def load(cls, language: str,
             path: Optional[str] = None) -> 'GrammarNeuron':
        path = path or str(
            CHECKPOINT_BASE / 'grammar' / f'{language}.pt')
        ckpt = torch.load(path, map_location='cpu')
        net  = cls(language=ckpt.get('language', language))
        net.load_state_dict(ckpt['model_state'])
        print(f"GrammarNeuron[{language}] loaded ← {path}")
        return net


# =============================================================================
# Layer 3: WordMonadNetwork
# =============================================================================

class WordMonadNetwork(nn.Module):
    """
    One small specialist network per word.

    Each monad knows its word deeply — not statistically but
    experientially. Its knowledge state is a SemanticWord object
    from LLM_Datatype_Cl.py.

    The CharacterNeuron is imported frozen as the first layer.
    The monad then builds word-specific layers on top.

    Only Class 2 and Class 3 words get full monads.
    Class 1 words get GrammarPointerNodes (lightweight, below).
    Class 4 words get their own monads with separate entries.

    Training:
      Each monad trains only on examples of its own word.
      Training data: every sentence this word appears in,
      with the full SemanticWord context.
      Checkpointed individually — 180,000 small checkpoints.

    The rabies principle:
      The first training example of a word is the most
      important. It establishes the spectral foundation.
      Every subsequent example adds to or modifies the spectrum.
      This is stored in SemanticWord.resonance.personal_associations.

    Args:
        word:          The word this monad represents.
        word_class:    WordClass enum value.
        char_net:      Frozen CharacterNeuron instance.
        semantic_word: SemanticWord knowledge state (if available).
        hidden_dim:    Internal representation size.
    """

    def __init__(
        self,
        word:          str,
        word_class:    WordClass,
        char_net:      CharacterNeuron,
        semantic_word: Optional[Any] = None,
        hidden_dim:    int = WORD_HIDDEN_DIM,
    ):
        super().__init__()
        self.word       = word
        self.word_class = word_class

        # Frozen character network — never trains after import
        self.char_net = char_net
        for p in self.char_net.parameters():
            p.requires_grad = False

        # char_net output dim: 192
        char_out_dim = 192

        # Word-specific encoder
        # Bidirectional LSTM: sees full context of each usage
        self.encoder = nn.LSTM(
            input_size=char_out_dim,
            hidden_size=hidden_dim,
            num_layers=2,
            bidirectional=True,
            dropout=0.1,
            batch_first=True,
        )

        # Spectrum projection
        # Maps LSTM output to the spectral space of SemanticWord
        self.spectrum_proj = nn.Linear(hidden_dim * 2, SEMANTIC_DIM)

        # Context sensitivity head
        # How much does meaning shift in this context?
        # Class 3 words (petrichor, vellichor) are highly sensitive.
        # Class 2 words (tree, run) are moderately sensitive.
        self.context_sensitivity = nn.Linear(hidden_dim * 2, 1)

        # Novelty detector
        # Is this usage pattern new? (triggers SemanticWord update)
        self.novelty_head = nn.Linear(hidden_dim * 2, 2)

        # Knowledge state — the SemanticWord
        # This is what makes the monad 'know' its word
        # beyond just statistical patterns
        self.knowledge: Optional[Any] = semantic_word

        # Usage history — timestamped spectral snapshots
        # Class 3 words accumulate these without aggregation
        # Class 2 words aggregate after threshold
        self._usage_log: List[dict] = []
        self._aggregation_threshold = (
            10000 if word_class == WordClass.CLASS_3_EXPERIENTIAL
            else 1000
        )

    def forward(
        self,
        char_ids:       torch.Tensor,  # (batch, seq_len)
        context_before: Optional[torch.Tensor] = None,
        context_after:  Optional[torch.Tensor] = None,
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Encode this word in context.

        Args:
            char_ids:       Character IDs for this word + context window.
            context_before: Character features from preceding tokens.
            context_after:  Character features from following tokens.

        Returns:
            spectrum:     (batch, SEMANTIC_DIM) — word's spectral position
            sensitivity:  (batch, 1)            — context shift amount
            novelty:      (batch, 2)            — is this usage novel?
        """
        # Extract character features (frozen)
        with torch.no_grad():
            char_features = self.char_net.get_features(char_ids)

        # Encode with context
        lstm_out, (h_n, _) = self.encoder(char_features)

        # Pool: use final hidden states from both directions
        pooled = torch.cat([h_n[-2], h_n[-1]], dim=-1)  # (B, hidden*2)

        spectrum    = self.spectrum_proj(pooled)
        sensitivity = torch.sigmoid(self.context_sensitivity(pooled))
        novelty     = self.novelty_head(pooled)

        return spectrum, sensitivity, novelty

    def log_usage(self, context: dict) -> None:
        """
        Record a usage of this word.

        For Class 3 words: every usage logged fully.
        For Class 2 words: aggregated after threshold.

        The rabies principle: first entry is preserved permanently,
        regardless of aggregation.

        Args:
            context: Dict with keys:
                     timestamp, context_before, context_after,
                     register, meaning_active, emotional_valence,
                     novel (bool)
        """
        entry = {**context, 'timestamp': time.time()}

        # First usage: always preserved
        if not self._usage_log:
            entry['foundational'] = True

        self._usage_log.append(entry)

        # Aggregate if over threshold (Class 2 only)
        if (self.word_class == WordClass.CLASS_2_CONCRETE
                and len(self._usage_log) > self._aggregation_threshold):
            self._aggregate_usages()

    def _aggregate_usages(self) -> None:
        """
        Aggregate usage log into statistical summary.
        Preserves the foundational first entry and any
        entries marked 'novel'.
        """
        preserved = [u for u in self._usage_log
                     if u.get('foundational') or u.get('novel')]
        # Keep most recent 100 for recency bias
        recent = self._usage_log[-100:]
        self._usage_log = preserved + [
            u for u in recent if u not in preserved]

    def save(self, base_dir: Optional[str] = None) -> str:
        """Save monad checkpoint."""
        base = Path(base_dir or CHECKPOINT_BASE / 'monads')
        # Use first 2 chars as subdirectory to avoid huge flat directories
        subdir = base / self.word[:2].lower().replace(' ', '_')
        subdir.mkdir(parents=True, exist_ok=True)
        safe_name = self.word.replace(' ', '_').replace('/', '_')
        path = str(subdir / f'{safe_name}.pt')
        torch.save({
            'model_state': self.state_dict(),
            'word':        self.word,
            'word_class':  self.word_class.value,
            'usage_log':   self._usage_log[-1000:],  # last 1000 entries
            'knowledge':   (self.knowledge.to_json()
                           if self.knowledge and SEMANTIC_WORD_AVAILABLE
                           else None),
            'timestamp':   time.time(),
        }, path)
        return path

    @classmethod
    def load(
        cls,
        word:     str,
        char_net: CharacterNeuron,
        base_dir: Optional[str] = None,
    ) -> 'WordMonadNetwork':
        """Load a word monad from checkpoint."""
        base     = Path(base_dir or CHECKPOINT_BASE / 'monads')
        subdir   = base / word[:2].lower().replace(' ', '_')
        safe     = word.replace(' ', '_').replace('/', '_')
        path     = str(subdir / f'{safe}.pt')
        ckpt     = torch.load(path, map_location='cpu')
        wc       = WordClass(ckpt['word_class'])
        knowledge = None
        if ckpt.get('knowledge') and SEMANTIC_WORD_AVAILABLE:
            knowledge = SemanticWord.from_json(ckpt['knowledge'])
        net = cls(word=ckpt['word'], word_class=wc,
                  char_net=char_net, semantic_word=knowledge)
        net.load_state_dict(ckpt['model_state'])
        net._usage_log = ckpt.get('usage_log', [])
        print(f"WordMonad['{word}'] loaded ← {path}")
        return net


# =============================================================================
# Class 1 Grammar Pointer Node — NOT a neural network
# =============================================================================

@dataclass
class GrammarPointerNode:
    """
    Lightweight structural node for Class 1 words.

    This is NOT a neural network. It's a rule-based reference
    resolution node. No statistical associations. Cannot drift.

    This is the fix for the 'it' problem.

    'it' resolves to the nearest compatible antecedent in the
    working context stack. Deterministic. Structural.
    The resolution doesn't depend on training data — it depends
    on the grammatical rules for that language and the actual
    context of the current sentence.

    Storage: ~200 bytes. Static. Never updated during operation.

    Args:
        token:          The word (e.g. 'it', 'the', 'and')
        pos:            Part of speech
        resolution_type: How this word resolves:
                         'anaphora' — refers back (it, he, she)
                         'cataphora' — refers forward (the latter)
                         'article'  — determinacy marking
                         'connector' — logical connection
                         'auxiliary' — grammatical helper
        resolution_rules: Language-specific resolution logic
        language:       Language this node belongs to
    """
    token:            str
    pos:              str
    resolution_type:  str
    resolution_rules: List[str] = field(default_factory=list)
    language:         str = 'en_us'

    def resolve(self, context_stack: List[Any]) -> Optional[str]:
        """
        Resolve this pointer to its referent in context.

        For 'it': find the nearest compatible antecedent
        (non-animate singular noun) in the context stack.
        Works backwards from current position.

        For 'the': marks the following noun as definite —
        the reader/listener already knows which one.

        Args:
            context_stack: List of recently processed tokens
                          with their SemanticWord data.

        Returns:
            The resolved referent string, or None if unresolvable.
        """
        if self.resolution_type == 'anaphora':
            # Search backwards for compatible antecedent
            for entry in reversed(context_stack):
                if self._compatible(entry):
                    return entry.get('token')
        return None

    def _compatible(self, entry: dict) -> bool:
        """Check if a context entry is a compatible antecedent."""
        if self.token == 'it':
            # 'it': non-animate singular noun
            pos = entry.get('pos', '')
            animacy = entry.get('animacy', 'unknown')
            return pos == 'noun' and animacy != 'animate'
        if self.token in {'he', 'him', 'his'}:
            return (entry.get('pos') == 'noun'
                    and entry.get('gender') == 'masculine')
        if self.token in {'she', 'her', 'hers'}:
            return (entry.get('pos') == 'noun'
                    and entry.get('gender') == 'feminine')
        return False


# =============================================================================
# Layer 4: WernickeNetwork — Ptolemy's Ears
# =============================================================================

class WernickeNetwork(nn.Module):
    """
    Ptolemy's Ears — Language Understanding.

    Named for Wernicke's area in the temporal lobe.
    Damage here → receptive aphasia: fluent speech, no comprehension.

    Takes the output of word monads (spectral representations)
    and produces a semantic understanding of what was said —
    meaning, intent, emotional valence, pragmatic force.

    Architecture: Transformer encoder (bidirectional).
    Reason: Understanding benefits from seeing the full input
    simultaneously. The meaning of the first word often depends
    on the last word of the sentence.

    Can be trained separately from BrocaNetwork.
    Saved as: {CHECKPOINT_BASE}/wernicke/{language}.pt

    Args:
        language:        Language this network understands.
        semantic_dim:    Dimension of word spectral representations.
        n_heads:         Attention heads.
        n_layers:        Transformer layers.
        max_seq_len:     Maximum tokens in one input sequence.
    """

    def __init__(
        self,
        language:    str = 'en_us',
        semantic_dim: int = SEMANTIC_DIM,
        n_heads:     int = 8,
        n_layers:    int = 6,
        max_seq_len: int = 512,
    ):
        super().__init__()
        self.language    = language
        self.semantic_dim = semantic_dim

        # Positional encoding — word order matters in understanding
        self.pos_encoding = nn.Embedding(max_seq_len, semantic_dim)

        # Transformer encoder
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=semantic_dim,
            nhead=n_heads,
            dim_feedforward=semantic_dim * 4,
            dropout=0.1,
            batch_first=True,
        )
        self.transformer = nn.TransformerEncoder(
            encoder_layer,
            num_layers=n_layers,
        )

        # Output heads
        # Meaning: compact semantic representation of full input
        self.meaning_head = nn.Linear(semantic_dim, semantic_dim)

        # Intent: what is the speaker trying to accomplish?
        # question, statement, command, emotional_expression,
        # humor, sarcasm, ritual (greeting/farewell), etc.
        self.intent_head = nn.Linear(semantic_dim, 16)

        # Emotional valence of the full utterance
        self.valence_head = nn.Linear(semantic_dim, 3)  # pos/neg/neutral

        # Pragmatic force: literal, ironic, hyperbolic, euphemistic
        self.pragmatic_head = nn.Linear(semantic_dim, 8)

    def forward(
        self,
        word_spectra:  torch.Tensor,       # (batch, seq_len, semantic_dim)
        padding_mask:  Optional[torch.Tensor] = None,  # (batch, seq_len)
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Understand an input sequence.

        Args:
            word_spectra:  Spectral representations from word monads.
                          Shape: (batch, seq_len, semantic_dim)
            padding_mask:  True where tokens are padding.

        Returns:
            meaning:    (batch, semantic_dim) — semantic representation
            intent:     (batch, 16)           — intent classification
            valence:    (batch, 3)            — emotional valence
            pragmatic:  (batch, 8)            — pragmatic force
        """
        # Add positional encoding
        positions = torch.arange(
            word_spectra.size(1), device=word_spectra.device)
        x = word_spectra + self.pos_encoding(positions)

        # Transformer understanding
        encoded = self.transformer(x, src_key_padding_mask=padding_mask)

        # Pool to single representation (CLS-style: use first position)
        cls_repr = encoded[:, 0, :]

        meaning   = self.meaning_head(cls_repr)
        intent    = self.intent_head(cls_repr)
        valence   = self.valence_head(cls_repr)
        pragmatic = self.pragmatic_head(cls_repr)

        return meaning, intent, valence, pragmatic

    def save(self, path: Optional[str] = None) -> str:
        path = path or str(
            CHECKPOINT_BASE / 'wernicke' / f'{self.language}.pt')
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        torch.save({
            'model_state':  self.state_dict(),
            'language':     self.language,
            'semantic_dim': self.semantic_dim,
            'timestamp':    time.time(),
        }, path)
        print(f"WernickeNetwork[{self.language}] saved → {path}")
        return path

    @classmethod
    def load(cls, language: str,
             path: Optional[str] = None) -> 'WernickeNetwork':
        path = path or str(
            CHECKPOINT_BASE / 'wernicke' / f'{language}.pt')
        ckpt = torch.load(path, map_location='cpu')
        net  = cls(
            language=ckpt.get('language', language),
            semantic_dim=ckpt.get('semantic_dim', SEMANTIC_DIM),
        )
        net.load_state_dict(ckpt['model_state'])
        print(f"WernickeNetwork[{language}] loaded ← {path}")
        return net


# =============================================================================
# Layer 5: BrocaNetwork — Ptolemy's Voice
# =============================================================================

class BrocaNetwork(nn.Module):
    """
    Ptolemy's Voice — Language Production.

    Named for Broca's area in the frontal lobe.
    Damage here → expressive aphasia: comprehension intact,
    cannot produce language. Slow, labored speech, grammar lost.

    Takes a semantic representation (from WernickeNetwork or
    from internal reasoning state) and produces language —
    selects words, orders them grammatically, generates output.

    Architecture: Autoregressive transformer decoder.
    Reason: Production is inherently sequential.
    You commit to each word before knowing the next.
    This is how actual speech works.

    Can be trained separately from WernickeNetwork.
    The key test: does it produce grammatically correct,
    semantically appropriate output from a meaning vector?
    Not 'what word statistically follows these words' but
    'what word expresses this meaning in this language?'

    Saved as: {CHECKPOINT_BASE}/broca/{language}.pt

    Args:
        language:     Language this network produces.
        semantic_dim: Input meaning representation size.
        vocab_size:   Output vocabulary size (monad dictionary size).
        n_heads:      Attention heads.
        n_layers:     Decoder layers.
        max_output:   Maximum tokens to generate.
    """

    def __init__(
        self,
        language:    str = 'en_us',
        semantic_dim: int = SEMANTIC_DIM,
        vocab_size:  int = 180000,
        n_heads:     int = 8,
        n_layers:    int = 6,
        max_output:  int = 512,
    ):
        super().__init__()
        self.language    = language
        self.semantic_dim = semantic_dim
        self.vocab_size  = vocab_size
        self.max_output  = max_output

        # Target word embedding (for teacher forcing during training)
        self.word_embedding = nn.Embedding(vocab_size, semantic_dim)

        # Positional encoding for output sequence
        self.pos_encoding = nn.Embedding(max_output, semantic_dim)

        # Transformer decoder
        decoder_layer = nn.TransformerDecoderLayer(
            d_model=semantic_dim,
            nhead=n_heads,
            dim_feedforward=semantic_dim * 4,
            dropout=0.1,
            batch_first=True,
        )
        self.transformer = nn.TransformerDecoder(
            decoder_layer,
            num_layers=n_layers,
        )

        # Word selection head
        # Maps decoder output to monad dictionary index
        # This selects WHICH word monad to activate next
        self.word_select = nn.Linear(semantic_dim, vocab_size)

        # Grammar check gate
        # Before committing to a word, check grammar validity
        # (subject-verb agreement, article before noun, etc.)
        # Works with GrammarNeuron
        self.grammar_gate = nn.Linear(semantic_dim * 2, 1)

    def forward(
        self,
        meaning:      torch.Tensor,              # (batch, semantic_dim)
        target_ids:   Optional[torch.Tensor] = None,  # for training
    ) -> torch.Tensor:
        """
        Generate word sequence from meaning representation.

        Args:
            meaning:    Semantic representation from WernickeNetwork
                       or internal reasoning. Shape: (batch, semantic_dim)
            target_ids: Ground truth word IDs for teacher forcing
                       during training. None during inference.

        Returns:
            logits: (batch, seq_len, vocab_size) — word selection scores
        """
        # Expand meaning to sequence dimension
        memory = meaning.unsqueeze(1)  # (B, 1, semantic_dim)

        if target_ids is not None:
            # Training: teacher forcing
            tgt = self.word_embedding(target_ids)
            positions = torch.arange(
                tgt.size(1), device=tgt.device)
            tgt = tgt + self.pos_encoding(positions)
            # Causal mask: can't see future tokens during training
            tgt_mask = nn.Transformer.generate_square_subsequent_mask(
                tgt.size(1), device=tgt.device)
            decoded = self.transformer(tgt, memory, tgt_mask=tgt_mask)
            return self.word_select(decoded)

        else:
            # Inference: autoregressive generation
            # Start with empty sequence, generate token by token
            # (simplified — full beam search would go here)
            batch_size = meaning.size(0)
            generated  = torch.zeros(batch_size, 1, self.semantic_dim,
                                      device=meaning.device)
            all_logits = []
            for step in range(self.max_output):
                positions = torch.arange(
                    generated.size(1), device=meaning.device)
                tgt = generated + self.pos_encoding(positions)
                decoded = self.transformer(tgt, memory)
                logits  = self.word_select(decoded[:, -1:, :])
                all_logits.append(logits)
                # Greedy: pick highest probability word
                next_id  = logits.argmax(dim=-1)
                next_emb = self.word_embedding(next_id)
                generated = torch.cat([generated, next_emb], dim=1)
                # Stop if EOS token selected (id=1 by convention)
                if (next_id == 1).all():
                    break
            return torch.cat(all_logits, dim=1)

    def save(self, path: Optional[str] = None) -> str:
        path = path or str(
            CHECKPOINT_BASE / 'broca' / f'{self.language}.pt')
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        torch.save({
            'model_state':  self.state_dict(),
            'language':     self.language,
            'semantic_dim': self.semantic_dim,
            'vocab_size':   self.vocab_size,
            'timestamp':    time.time(),
        }, path)
        print(f"BrocaNetwork[{self.language}] saved → {path}")
        return path

    @classmethod
    def load(cls, language: str,
             path: Optional[str] = None) -> 'BrocaNetwork':
        path = path or str(
            CHECKPOINT_BASE / 'broca' / f'{language}.pt')
        ckpt = torch.load(path, map_location='cpu')
        net  = cls(
            language=ckpt.get('language', language),
            semantic_dim=ckpt.get('semantic_dim', SEMANTIC_DIM),
            vocab_size=ckpt.get('vocab_size', 180000),
        )
        net.load_state_dict(ckpt['model_state'])
        print(f"BrocaNetwork[{language}] loaded ← {path}")
        return net


# =============================================================================
# LanguageNeuron — complete importable language capability
# =============================================================================

class LanguageNeuron:
    """
    A complete language capability as one importable unit.

    Contains all layers for one language:
      CharacterNeuron    (frozen — shared across all languages)
      LexicalDimensionNeuron
      GrammarNeuron      (language-specific)
      WordMonadDictionary (180k monads for this language)
      WernickeNetwork    (understanding — language-specific)
      BrocaNetwork       (production — language-specific)

    Usage:
        # Load a complete language
        english = LanguageNeuron.load('en_us')
        latin   = LanguageNeuron.load('la')
        python  = LanguageNeuron.load('py')

        # Use in a PtolemyFace
        face = PtolemyFace([english, latin])

    The brain doesn't clear a cache and load a new module
    when it encounters a Latin word in an English sentence.
    It traverses the Latin pathways while the English ones
    remain active. PtolemyFace replicates this by keeping
    all loaded LanguageNeurons simultaneously available.

    Args:
        language:   Language code (en_us, la, es, gr_ancient,
                    coptic, demotic_egyptian, py, html_css_js, etc.)
        char_net:   Shared frozen CharacterNeuron.
    """

    SUPPORTED_LANGUAGES = {
        # Natural languages
        'en_us':           'English (United States)',
        'la':              'Latin (Classical)',
        'es':              'Spanish',
        'gr_ancient':      'Ancient Greek',
        'coptic':          'Coptic',
        'demotic_egyptian':'Demotic Egyptian',
        'zh_mandarin':     'Mandarin Chinese',
        # Programming languages
        'py':              'Python',
        'html_css_js':     'HTML/CSS/JavaScript',
        'php':             'PHP',
        'sql':             'SQL',
        'c_cpp':           'C/C++',
        # Historical/research
        'voynich':         'Voynich Manuscript (unknown)',
    }

    def __init__(self, language: str, char_net: CharacterNeuron):
        self.language   = language
        self.char_net   = char_net   # shared, frozen
        self.lexical    = LexicalDimensionNeuron(language=language)
        self.grammar    = GrammarNeuron(language=language)
        self.wernicke   = WernickeNetwork(language=language)
        self.broca      = BrocaNetwork(language=language)
        # Word monads loaded on demand (lazy loading)
        self._monads:   Dict[str, WordMonadNetwork] = {}
        # Class 1 grammar pointer nodes
        self._pointers: Dict[str, GrammarPointerNode] = {}
        self._load_class1_pointers()

    def _load_class1_pointers(self) -> None:
        """Load grammar pointer nodes for Class 1 words."""
        rules_path = (PTOLEMY_BASE / 'grammar' /
                      self.language / 'class1_nodes.json')
        if not rules_path.exists():
            return
        with open(rules_path) as f:
            nodes = json.load(f)
        for token, data in nodes.items():
            self._pointers[token] = GrammarPointerNode(
                token=token,
                pos=data.get('pos', 'unknown'),
                resolution_type=data.get('resolution_type', 'connector'),
                resolution_rules=data.get('resolution_rules', []),
                language=self.language,
            )

    def get_monad(self, word: str) -> Optional[WordMonadNetwork]:
        """
        Get word monad, loading from checkpoint if needed.
        Returns None for Class 1 words (use get_pointer instead).
        """
        if word in self._monads:
            return self._monads[word]
        try:
            monad = WordMonadNetwork.load(word, self.char_net)
            self._monads[word] = monad
            return monad
        except FileNotFoundError:
            return None

    def get_pointer(self, word: str) -> Optional[GrammarPointerNode]:
        """Get grammar pointer node for Class 1 words."""
        return self._pointers.get(word.lower())

    def save(self, base_dir: Optional[str] = None) -> str:
        """Save all components of this language neuron."""
        base = Path(base_dir or CHECKPOINT_BASE / 'languages' / self.language)
        base.mkdir(parents=True, exist_ok=True)
        self.grammar.save(str(base / 'grammar.pt'))
        self.lexical_save(str(base / 'lexical.pt'))
        self.wernicke.save(str(base / 'wernicke.pt'))
        self.broca.save(str(base / 'broca.pt'))
        print(f"LanguageNeuron[{self.language}] saved → {base}")
        return str(base)

    def lexical_save(self, path: str) -> None:
        torch.save({
            'model_state': self.lexical.state_dict(),
            'language':    self.language,
        }, path)

    @classmethod
    def load(cls, language: str,
             char_net: Optional[CharacterNeuron] = None) -> 'LanguageNeuron':
        """
        Load a complete language neuron.

        Args:
            language: Language code.
            char_net: Shared CharacterNeuron. If None, loads from default path.
        """
        if char_net is None:
            char_net = CharacterNeuron.load(freeze=True)
        neuron = cls(language=language, char_net=char_net)
        base   = CHECKPOINT_BASE / 'languages' / language
        if (base / 'grammar.pt').exists():
            neuron.grammar  = GrammarNeuron.load(language, str(base/'grammar.pt'))
        if (base / 'wernicke.pt').exists():
            neuron.wernicke = WernickeNetwork.load(language, str(base/'wernicke.pt'))
        if (base / 'broca.pt').exists():
            neuron.broca    = BrocaNetwork.load(language, str(base/'broca.pt'))
        print(f"LanguageNeuron[{language}] ready")
        return neuron


# =============================================================================
# PtolemyFace — the complete assembled model
# =============================================================================

class PtolemyFace:
    """
    A complete Ptolemy model instance — one or more LanguageNeurons
    combined into a single conversational system.

    The brain doesn't unload English when it encounters Latin.
    All loaded languages remain simultaneously accessible.
    The system traverses whichever language's pathways are
    activated by the current input — exactly as a multilingual
    human brain works.

    Usage:
        char_net = CharacterNeuron.load(freeze=True)
        english  = LanguageNeuron.load('en_us', char_net)
        latin    = LanguageNeuron.load('la', char_net)
        python   = LanguageNeuron.load('py', char_net)

        ptolemy = PtolemyFace(
            name='Ptolemy_v1',
            languages=[english, latin, python],
            char_net=char_net,
        )

        # Process mixed-language input
        response = ptolemy.respond("The sine of an angle (sinus anguli)...")

    Args:
        name:      Name for this Ptolemy instance / face.
        languages: List of loaded LanguageNeuron instances.
        char_net:  Shared frozen CharacterNeuron.
    """

    def __init__(
        self,
        name:      str,
        languages: List[LanguageNeuron],
        char_net:  CharacterNeuron,
    ):
        self.name      = name
        self.char_net  = char_net
        self.languages: Dict[str, LanguageNeuron] = {
            ln.language: ln for ln in languages
        }
        # Working context stack for reference resolution
        # This is what 'it' resolves against
        self._context_stack: List[dict] = []
        self._context_max   = 512  # rolling window

    def detect_language(self, text: str) -> str:
        """
        Detect primary language of input text.
        Falls back to first loaded language if detection fails.

        This is the routing decision — which LanguageNeuron's
        Wernicke network processes this input?
        """
        # Simple heuristic for now — production would use
        # the CharacterNeuron's script_output to classify
        # writing system, then match to language
        if self.languages:
            return list(self.languages.keys())[0]
        return 'en_us'

    def push_context(self, token: str, data: dict) -> None:
        """Add token to rolling context stack."""
        self._context_stack.append({'token': token, **data})
        if len(self._context_stack) > self._context_max:
            self._context_stack.pop(0)

    def resolve_reference(self, pointer_word: str) -> Optional[str]:
        """
        Resolve a Class 1 reference word to its antecedent.
        This is the structural fix for the 'it' drift problem.
        """
        lang_code = self.detect_language(pointer_word)
        if lang_code in self.languages:
            lang = self.languages[lang_code]
            node = lang.get_pointer(pointer_word)
            if node:
                return node.resolve(self._context_stack)
        return None

    def save(self, path: Optional[str] = None) -> str:
        """Save complete PtolemyFace state."""
        path = path or str(CHECKPOINT_BASE / 'faces' / f'{self.name}.pt')
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        torch.save({
            'name':           self.name,
            'languages':      list(self.languages.keys()),
            'context_stack':  self._context_stack,
            'timestamp':      time.time(),
        }, path)
        print(f"PtolemyFace[{self.name}] saved → {path}")
        return path


# =============================================================================
# Dataset utilities — corpus fetching and SemanticWord population
# =============================================================================

class PublicCorpusDownloader:
    """
    Downloads and prepares publicly available linguistic datasets
    for populating the HyperWordContext dictionary.

    Sources used (all public domain or open license):
      WordNet 3.1           — synsets, synonyms, hypernyms, definitions
      Wiktionary dump       — etymologies, pronunciations, definitions
      etymonline scrape     — detailed etymological histories
      CMU Pronouncing Dict  — phoneme sequences for English
      COCA frequency lists  — statistical frequency profiles
      Project Gutenberg     — historical usage examples
      Universal Dependencies — parsed sentence corpora for grammar training
      Leipzig Corpora       — multilingual frequency lists

    Usage:
        downloader = PublicCorpusDownloader(language='en_us')
        downloader.download_all()
        hw = downloader.build_hyperwebster()
        hw.save('en_us_dictionary.json')
    """

    SOURCES = {
        'en_us': {
            'wordnet':     'https://wordnetcode.princeton.edu/wn3.1.dict.tar.gz',
            'cmu_dict':    'http://svn.code.sf.net/p/cmusphinx/code/trunk/cmudict/cmudict-0.7b',
            'ud_treebank': 'https://raw.githubusercontent.com/UniversalDependencies/UD_English-EWT/master/en_ewt-ud-train.conllu',
            'freq_list':   'https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2018/en/en_50k.txt',
        },
        'la': {
            'freq_list':   'https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2018/la/la_50k.txt',
            'ud_treebank': 'https://raw.githubusercontent.com/UniversalDependencies/UD_Latin-PROIEL/master/la_proiel-ud-train.conllu',
        },
        'es': {
            'freq_list':   'https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2018/es/es_50k.txt',
            'ud_treebank': 'https://raw.githubusercontent.com/UniversalDependencies/UD_Spanish-GSD/master/es_gsd-ud-train.conllu',
        },
        'gr_ancient': {
            'freq_list':   'https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2018/grc/grc_50k.txt',
        },
    }

    def __init__(self, language: str = 'en_us',
                 cache_dir: str = '~/.ptolemy/corpora'):
        self.language  = language
        self.cache_dir = Path(cache_dir).expanduser()
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get_frequency_list(self) -> List[Tuple[str, int]]:
        """
        Fetch most common words for this language with frequency counts.

        Returns list of (word, frequency) tuples sorted by frequency.
        This is the seed list for building the HyperWordContext dictionary.
        """
        import urllib.request
        sources = self.SOURCES.get(self.language, {})
        freq_url = sources.get('freq_list')
        if not freq_url:
            print(f"No frequency list available for {self.language}")
            return []
        cache_file = self.cache_dir / f'{self.language}_freq.txt'
        if not cache_file.exists():
            print(f"Downloading frequency list for {self.language}...")
            urllib.request.urlretrieve(freq_url, cache_file)
        words = []
        with open(cache_file, encoding='utf-8') as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) >= 2:
                    try:
                        words.append((parts[0], int(parts[1])))
                    except ValueError:
                        pass
        print(f"Loaded {len(words):,} words for {self.language}")
        return words

    def classify_word(self, word: str, frequency: int) -> WordClass:
        """
        Classify a word into WordClass based on surface features
        and frequency. Used for initial dictionary population.

        This is a heuristic — the LexicalDimensionNeuron will
        refine classifications after training.
        """
        # Simple English structural word check
        structural = {
            'the','a','an','this','that','these','those',
            'i','you','he','she','it','we','they','me','him',
            'her','us','them','my','your','his','its','our',
            'their','in','on','at','by','for','with','from',
            'to','of','and','but','or','nor','yet','so',
            'is','are','was','were','be','been','being',
            'have','has','had','do','does','did','will',
            'would','could','should','may','might',
        }
        if word.lower() in structural:
            return WordClass.CLASS_1_STRUCTURAL

        # High frequency + short = likely Class 2
        if frequency > 10000 and len(word) <= 6:
            return WordClass.CLASS_2_CONCRETE

        # Longer, less frequent = likely Class 3
        if frequency < 1000 or len(word) > 10:
            return WordClass.CLASS_3_EXPERIENTIAL

        return WordClass.CLASS_2_CONCRETE

    def build_hyperwebster(
        self,
        limit: int = 50000
    ) -> Optional[Any]:
        """
        Build a HyperWebster dictionary from downloaded corpora.

        Creates a SemanticWord entry for each word in the frequency
        list, populated with whatever data is available from the
        downloaded corpora.

        This is the seed dictionary — an AI using it will enrich
        each entry through usage over time.

        Args:
            limit: Maximum number of words to include.

        Returns:
            HyperWebster instance, or None if datatype unavailable.
        """
        if not SEMANTIC_WORD_AVAILABLE:
            print("SemanticWord not available. Cannot build HyperWebster.")
            return None

        words = self.get_frequency_list()[:limit]
        hw    = HyperWebster()

        print(f"Building HyperWebster for {self.language} "
              f"({len(words):,} words)...")

        for i, (word, freq) in enumerate(words):
            wc = self.classify_word(word, freq)

            # Skip Class 1 words — they get GrammarPointerNodes, not entries
            if wc == WordClass.CLASS_1_STRUCTURAL:
                continue

            sw = SemanticWord(token=word)
            sw.statistics.corpus_frequency = freq
            sw.statistics.frequency_band   = (
                'high' if freq > 10000 else
                'mid'  if freq > 1000  else 'low'
            )
            sw.acquisition_sources.append(
                f'frequency_corpus_{self.language}')

            hw[word] = sw

            if i % 5000 == 0:
                print(f"  {i:,}/{len(words):,} words processed...")

        print(f"HyperWebster built: {len(hw):,} entries")
        return hw


# =============================================================================
# Training utilities
# =============================================================================

class PtolemyTrainer:
    """
    Manages training of all Ptolemy components with full
    checkpoint persistence.

    Supports:
    - Training CharacterNeuron on multilingual character data
    - Training individual WordMonads on word-specific corpora
    - Training GrammarNeuron on parsed treebank data
    - Training WernickeNetwork on meaning-labeled data
    - Training BrocaNetwork on generation pairs
    - Resume from any checkpoint without loss of progress

    The chronic training problem (catastrophic forgetting)
    is handled through:
    - EWC (Elastic Weight Consolidation) for sequential learning
    - Per-monad isolation (each monad only trains on its own word)
    - Frozen CharacterNeuron (never retrained after initial training)

    Args:
        component:    Network to train.
        language:     Language being trained.
        checkpoint_interval: Save every N steps.
        use_ewc:      Apply EWC to prevent catastrophic forgetting.
    """

    def __init__(
        self,
        component:             nn.Module,
        language:              str = 'en_us',
        checkpoint_interval:   int = 1000,
        use_ewc:               bool = True,
        learning_rate:         float = 1e-4,
    ):
        self.component           = component
        self.language            = language
        self.checkpoint_interval = checkpoint_interval
        self.use_ewc             = use_ewc
        self.optimizer = torch.optim.AdamW(
            [p for p in component.parameters() if p.requires_grad],
            lr=learning_rate,
            weight_decay=0.01,
        )
        self.scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
            self.optimizer, T_max=10000)
        self.step      = 0
        self.epoch     = 0
        self._ewc_data: Optional[dict] = None

    def save_checkpoint(self, path: str, extra: dict = {}) -> None:
        """
        Save complete training state.
        Resuming from this checkpoint loses zero progress.
        """
        torch.save({
            'model_state':     self.component.state_dict(),
            'optimizer_state': self.optimizer.state_dict(),
            'scheduler_state': self.scheduler.state_dict(),
            'step':            self.step,
            'epoch':           self.epoch,
            'language':        self.language,
            'ewc_data':        self._ewc_data,
            'timestamp':       time.time(),
            **extra,
        }, path)
        print(f"Checkpoint saved at step {self.step} → {path}")

    def load_checkpoint(self, path: str) -> None:
        """Resume training from checkpoint. Exact state restored."""
        ckpt = torch.load(path, map_location='cpu')
        self.component.load_state_dict(ckpt['model_state'])
        self.optimizer.load_state_dict(ckpt['optimizer_state'])
        self.scheduler.load_state_dict(ckpt['scheduler_state'])
        self.step      = ckpt['step']
        self.epoch     = ckpt['epoch']
        self._ewc_data = ckpt.get('ewc_data')
        print(f"Resumed from step {self.step} ← {path}")

    def compute_ewc_penalty(self) -> torch.Tensor:
        """
        Elastic Weight Consolidation penalty.

        Resists changing weights that were important for
        previously learned tasks. Enables sequential learning
        across training addendums without catastrophic forgetting.

        Returns zero if EWC not initialized (first training session).
        """
        if not self._ewc_data or not self.use_ewc:
            return torch.tensor(0.0)
        penalty = torch.tensor(0.0)
        for name, param in self.component.named_parameters():
            if name in self._ewc_data['fisher']:
                fisher   = self._ewc_data['fisher'][name]
                old_param = self._ewc_data['params'][name]
                penalty  += (fisher * (param - old_param).pow(2)).sum()
        return penalty * 0.5

    def compute_fisher_information(
        self,
        dataloader: DataLoader,
        n_samples:  int = 200,
    ) -> None:
        """
        Compute Fisher information matrix after training on a task.
        Called at the END of each training addendum, before the next begins.
        Enables the next addendum to preserve this knowledge.
        """
        self.component.eval()
        fisher: Dict[str, torch.Tensor] = {}
        params: Dict[str, torch.Tensor] = {}

        for name, param in self.component.named_parameters():
            if param.requires_grad:
                fisher[name] = torch.zeros_like(param.data)
                params[name] = param.data.clone()

        n = 0
        for batch in dataloader:
            if n >= n_samples:
                break
            # Forward pass — loss computation is model-specific
            # This is a placeholder for the actual loss computation
            # Each component subclass would implement this
            n += 1

        self._ewc_data = {'fisher': fisher, 'params': params}
        print(f"Fisher information computed over {n} samples")
        print("EWC enabled for next training addendum.")


# =============================================================================
# Quick-start utilities
# =============================================================================

def initialize_ptolemy(
    languages:    List[str] = ['en_us'],
    name:         str       = 'Ptolemy_v1',
    char_net_path: Optional[str] = None,
) -> PtolemyFace:
    """
    Initialize a complete Ptolemy system from scratch or checkpoints.

    If checkpoints exist, loads them.
    If not, creates untrained networks ready for training.

    Args:
        languages:     List of language codes to include.
        name:          Name for this Ptolemy face.
        char_net_path: Path to pretrained CharacterNeuron.

    Returns:
        PtolemyFace ready for training or inference.
    """
    # Load or create CharacterNeuron
    cn_path = char_net_path or str(CHECKPOINT_BASE / 'char_neuron.pt')
    if Path(cn_path).exists():
        char_net = CharacterNeuron.load(cn_path, freeze=True)
    else:
        print("No CharacterNeuron checkpoint found. "
              "Creating untrained network. Run training before use.")
        char_net = CharacterNeuron()

    # Load or create language neurons
    language_neurons = []
    for lang in languages:
        lang_path = CHECKPOINT_BASE / 'languages' / lang
        if lang_path.exists():
            ln = LanguageNeuron.load(lang, char_net)
        else:
            print(f"No checkpoint for '{lang}'. "
                  f"Creating untrained network.")
            ln = LanguageNeuron(language=lang, char_net=char_net)
        language_neurons.append(ln)

    return PtolemyFace(
        name=name,
        languages=language_neurons,
        char_net=char_net,
    )


def download_and_seed(
    language: str = 'en_us',
    output:   str = None,
    limit:    int = 50000,
) -> None:
    """
    Download public corpora and build seed HyperWebster dictionary.

    This is the starting point before any training begins.
    Populates the word monad dictionary with base knowledge
    drawn from public linguistic databases.

    Args:
        language: Language code to seed.
        output:   Output JSON path. Defaults to {language}_seed.json
        limit:    Maximum words to include.
    """
    output = output or f'{language}_hyperwebster_seed.json'
    downloader = PublicCorpusDownloader(language=language)
    hw = downloader.build_hyperwebster(limit=limit)
    if hw:
        hw.save(output)
        print(f"Seed dictionary ready: {output}")
        print(f"Next step: train CharacterNeuron, then WordMonads")


# =============================================================================
# Entry point
# =============================================================================

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(
        description='Ptolemy Neural Language Architecture')
    parser.add_argument('--init', nargs='+', metavar='LANG',
        help='Initialize Ptolemy with specified languages')
    parser.add_argument('--seed', metavar='LANG',
        help='Download and seed HyperWebster for a language')
    parser.add_argument('--name', default='Ptolemy_v1',
        help='Name for this Ptolemy face')
    parser.add_argument('--limit', type=int, default=50000,
        help='Word limit for seeding')
    args = parser.parse_args()

    if args.seed:
        download_and_seed(language=args.seed, limit=args.limit)
    elif args.init:
        face = initialize_ptolemy(
            languages=args.init,
            name=args.name,
        )
        print(f"\nPtolemyFace '{face.name}' initialized.")
        print(f"Languages: {list(face.languages.keys())}")
        print(f"Next steps:")
        print(f"  1. python ptolemy_core.py --seed en_us")
        print(f"  2. Train CharacterNeuron on multilingual corpus")
        print(f"  3. Train WordMonads for each language")
        print(f"  4. Train GrammarNeuron per language")
        print(f"  5. Train Wernicke + Broca networks")
    else:
        parser.print_help()
