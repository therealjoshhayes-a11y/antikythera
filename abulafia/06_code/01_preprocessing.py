"""
01_preprocessing.py
Abulafia — Standards Alignment for Legacy Degree Programs
Part of the Antikythera project tree.

Text preprocessing pipelines for all three similarity measures.
Each measure uses a distinct preprocessing chain appropriate to
its similarity method. Preprocessing is fixed and deterministic —
identical input always produces identical output.

Preprocessing chains:

  SBERT:   None. Raw natural language submitted as-is.

  TF-IDF:  lowercase → stop word removal (NLTK) → lemmatization
           with POS tagging (WordNetLemmatizer) → WordNet verb
           synonym expansion (verbs only) → n-gram tokenization.

  Jaccard: lowercase → stop word removal (NLTK) → Porter stemming.

Copyright (c) 2026. All rights reserved.
Proprietary and confidential. See LICENSE.
"""

import nltk
from nltk.corpus import wordnet, stopwords
from nltk.stem import PorterStemmer, WordNetLemmatizer
from nltk.tokenize import word_tokenize
from typing import List, Set


# ── NLTK resource check ────────────────────────────────────────────────────────

def ensure_nltk_resources() -> None:
    """
    Download required NLTK corpora if not already present.
    Call once at startup before any preprocessing.

    Resources required: punkt, averaged_perceptron_tagger,
    wordnet, stopwords.
    """
    raise NotImplementedError


# ── Shared utilities ───────────────────────────────────────────────────────────

def get_stop_words() -> Set[str]:
    """
    Return the NLTK English stop word set.

    Used by both TF-IDF and Jaccard preprocessing pipelines.
    The set is loaded once and passed to preprocessing functions
    rather than reloaded per call.

    Returns:
        Set of lowercase English stop word strings.
    """
    raise NotImplementedError


def penn_to_wordnet_pos(penn_tag: str) -> str | None:
    """
    Map a Penn Treebank POS tag to a WordNet POS constant.

    Required for accurate lemmatization. Without POS context,
    WordNetLemmatizer defaults to noun, causing verbs to be
    lemmatized incorrectly and breaking downstream synonym lookup.

    Args:
        penn_tag: Penn Treebank tag string (e.g. 'VBZ', 'NN').

    Returns:
        WordNet POS constant (wordnet.VERB, wordnet.NOUN, etc.)
        or None if no mapping exists.
    """
    raise NotImplementedError


# ── TF-IDF preprocessing ───────────────────────────────────────────────────────

def lemmatize_with_pos(tokens: List[str], lemmatizer: WordNetLemmatizer) -> List[str]:
    """
    POS-tag a token list and lemmatize each token to its base form.

    Verbs are reduced to their infinitive form regardless of tense
    or conjugation: 'applied', 'applying', 'applies' → 'apply'.
    Nouns and other tokens are lemmatized with their correct POS.

    Args:
        tokens:     List of lowercase string tokens.
        lemmatizer: Initialized NLTK WordNetLemmatizer instance.

    Returns:
        List of lemmatized string tokens, same length as input.
    """
    raise NotImplementedError


def expand_verb_synonyms(tokens: List[str]) -> List[str]:
    """
    Expand verb tokens with their WordNet synonym lemmas.

    For each token identified as a verb after lemmatization, retrieve
    all synonym lemmas from all WordNet synsets and append them to the
    token stream. Expansion is applied to verbs only. Noun expansion
    is explicitly excluded to preserve domain-specific IDF signal in
    technical curriculum text.

    Example:
        'demonstrate' → ['demonstrate', 'show', 'exhibit', 'evidence',
                         'attest', 'certify']

    Args:
        tokens: List of lemmatized tokens (output of lemmatize_with_pos).

    Returns:
        Expanded token list. Original tokens preserved; synonyms appended
        after each qualifying verb.
    """
    raise NotImplementedError


def preprocess_tfidf(
    text: str,
    stop_words: Set[str],
    lemmatizer: WordNetLemmatizer,
) -> str:
    """
    Full TF-IDF preprocessing pipeline.

    Pipeline: lowercase → stop word removal → lemmatize with POS
    tagging → expand verb synonyms via WordNet → return as
    whitespace-joined string for n-gram vectorization.

    The returned string is passed directly to a fitted
    TfidfVectorizer with stop_words=None. Stop words are removed
    here, not by the vectorizer, to ensure synonym expansion
    operates on a clean token stream.

    Args:
        text:       Raw SLO or standard text string.
        stop_words: NLTK English stop word set (from get_stop_words).
        lemmatizer: Initialized NLTK WordNetLemmatizer instance.

    Returns:
        Preprocessed string ready for TF-IDF vectorization.
    """
    raise NotImplementedError


# ── Jaccard preprocessing ──────────────────────────────────────────────────────

def preprocess_jaccard(
    text: str,
    stop_words: Set[str],
    stemmer: PorterStemmer,
) -> Set[str]:
    """
    Full Jaccard preprocessing pipeline.

    Pipeline: lowercase → stop word removal → whitespace split →
    Porter stemming → return as set of stemmed tokens.

    Stop word removal prevents common function words ('will', 'shall',
    'the', 'students') from inflating the token union and producing
    artificially low Jaccard scores on substantively similar pairs.

    Args:
        text:       Raw SLO or standard text string.
        stop_words: NLTK English stop word set (from get_stop_words).
        stemmer:    Initialized NLTK PorterStemmer instance.

    Returns:
        Set of stemmed, stop-word-filtered token strings.
    """
    raise NotImplementedError


# ── Corpus hydration ───────────────────────────────────────────────────────────

def hydrate_slos(
    client_catalog_path: str,
    degree_plan_path: str,
    acgm_wecm_path: str,
    output_path: str,
) -> None:
    """
    Filter client catalog to degree plan courses and retrieve full
    SLO text from the ACGM/WECM corpus by cross-referencing course IDs.

    Client catalogs typically contain abbreviated descriptions rather
    than full official SLOs. Authoritative SLO text must be retrieved
    from the THECB-published ACGM/WECM corpus. Course title matching
    is used as the primary join key where IDs are inconsistent between
    institutional and state systems.

    Concatenates course description with full SLO text before saving.
    Descriptions provide domain context that improves semantic matching.

    Args:
        client_catalog_path: Path to institution course catalog CSV.
        degree_plan_path:    Path to target degree plan course list CSV.
        acgm_wecm_path:      Path to consolidated ACGM+WECM corpus CSV.
        output_path:         Destination path for hydrated SLO CSV.

    Raises:
        ValueError: If degree plan courses cannot be matched in corpus.
    """
    raise NotImplementedError


def clean_standards(
    standards_path: str,
    output_path: str,
) -> None:
    """
    Validate and clean target standards file.

    Applies the same text normalization as SLO cleaning: whitespace
    normalization, HTML tag removal, UTF-8 enforcement. Checks for
    duplicate standard IDs and empty text fields.

    Args:
        standards_path: Path to raw target standards CSV.
        output_path:    Destination path for cleaned standards CSV.

    Raises:
        ValueError: If duplicate standard IDs are found.
    """
    raise NotImplementedError
