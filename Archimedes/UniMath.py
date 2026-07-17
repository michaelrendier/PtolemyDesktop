#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'

from dataclasses import dataclass


@dataclass
class Symbol:

	symbol = {'delta_upper': 'Δ', 'delta_lower': 'δ', 'sigma': 'Σ', 'sigmoid': 'σ', 'gradient': '∇', 'magnitude':'║'}

	al = algebra = {}

	trig = trigonometry = {}

	calc = calculus = {}

	la = linear_algebra = {}

	msymbols = {'plus_minus': '\u00b1', '2_root': '\u221a', '3_root': '\u221b', '4_root': '\u221c', 'increment': '\u2206', 'partial_diff': '\u2202', 'prime': '\u2032', 'prime2': '\u2033', 'prime3': '\u2034', 'integral': '\u222b','integral2': '\u222c','integral3': '\u222d','integral4': '\u2a0c', 'n_ary_summ': '\u2211', 'n_ary_product': '\u2a00', 'micro': 'µ'}

	supd = super_digits = {'0': '⁰', '1': '¹', '2': '²', '3': '³', '4': '⁴', '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸',
	                       '9': '⁹'}

	supop = super_operators = {'+': '⁺', '-': '⁻', '=': '⁼', '(': '⁽', ')': '⁾'}

	subd = sub_digits = {'0': '₀', '1': '₁', '2': '₂', '3': '₃', '4': '₄', '5': '₅', '6': '₆', '7': '₇', '8': '₈',
	                     '9': '₉'}

	subop = sub_operators = {'+': '₊', '-': '₋', '=': '₌', '(': '₍', ')': '₎'}

	supl = super_lower = {'a': 'ᵃ', 'b': 'ᵇ', 'c': 'ᶜ', 'd': 'ᵈ', 'e': 'ᵉ', 'f': 'ᶠ', 'g': 'ᵍ', 'h': 'ʰ', 'i': 'ⁱ',
	                      'j': 'ʲ', 'k': 'ᵏ', 'l': 'ˡ', 'm': 'ᵐ', 'n': 'ⁿ', 'o': 'ᵒ', 'p': 'ᵖ', 'r': 'ʳ', 's': 'ˢ',
	                      't': 'ᵗ', 'u': 'ᵘ', 'v': 'ᵛ', 'w': 'ʷ', 'x': 'ˣ', 'y': 'ʸ', 'z': 'ᶻ'}

	supu = super_upper = {'A': 'ᴬ', 'B': 'ᴮ', 'D': 'ᴰ', 'E': 'ᴱ', 'G': 'ᴳ', 'H': 'ᴴ', 'I': 'ᴵ', 'J': 'ᴶ', 'K': 'ᴷ',
	                      'L': 'ᴸ', 'M': 'ᴹ', 'N': 'ᴺ', 'O': 'ᴼ', 'P': 'ᴾ', 'R': 'ᴿ', 'T': 'ᵀ', 'U': 'ᵁ', 'V': 'ⱽ',
	                      'W': 'ᵂ'}

	subl = sub_lower = {'a': 'ₐ', 'e': 'ₑ', 'h': 'ₕ', 'i': 'ᵢ', 'j': 'ⱼ', 'k': 'ₖ', 'l': 'ₗ', 'm': 'ₘ', 'n': 'ₙ',
	                    'o': 'ₒ', 'p': 'ₚ', 'r': 'ᵣ', 's': 'ₛ', 't': 'ₜ', 'u': 'ᵤ', 'v': 'ᵥ', 'x': 'ₓ'}

	matrix = {'ul': '⌈', 'ur': '⌉', 'll': '⌊', 'lr': '⌋'}

	units = {'nanometer': '㎚', 'micrometer': '㎛', 'millimeter': '㎜', 'centimeter': '㎝', 'kilometer': '㏎', 'inch': '㏌', 'millimeter_squared': '㎟', 'centimeter_squared': '㎠', 'kilometer_squared': '㎢', 'cubic_millimeter': '㎣', 'cubic_centimeter': '㏄', 'cubic_meter': '㎥', 'cubic_kilometer': '㎦', 'micro_liter': '㎕', 'milliliter': '㎖', 'decaliter': '㎗', 'kiloliter': '㎘', 'nanosecond': '㎱', 'microsecond': '㎲', 'millisecond': '㎳', 'microgram': '㎍', 'milligram': '㎎', 'kilogram': '㎏', 'kilobytes': '㎅', 'megabytes': '㎆', 'gigabytes': '㎇', 'hertz': '㎐', 'kilohertz': '㎑', 'megahertz': '㎒', 'gigahertz': '㎓', 'terahertz': '㎔', 'picovolt': '㎴', 'nanovolt': '㎵', 'microvolt': '㎶', 'millivolt': '㎷', 'kilovolt': '㎸', 'megavolt': '㎹', 'picowatt': '㎺', 'nanowatt': '㎻', 'microwatt': '㎼', 'milliwatt': '㎽', 'kilowatt': '㎾', 'megawatt': '㎿', 'kiloohm': '㏀', 'megaohm': '㏁', 'picoamp': '㎀', 'nanoamp': '㎁', 'microamp': '㎂', 'milliamp': '㎃', 'kiloamp': '㎄', 'meters_per_second': '㎧', 'meters_per_second_squared': '㎨', 'radians_per_second': '㎮', 'radians_per_second_squared': '㎯', 'pascal': '㎩', 'kilopascal': '㎪', 'megapascal': '㎫', 'gigapascal': '㎬', 'calorie': '㎈', 'kilocalorie': '㎉', 'decimeter': '㍷', 'decimeter_squared': '㍸', 'cubic_decimeter': '㍹', 'frequency_modulation': '㎙', 'hectopascal': '㍱', 'dalton': '㍲', 'astronomical_unit': '㍳', 'bar': '㍴', 'square_ov': '㍵', 'parsec': '㍶', 'international_unit': '㍺', 'picofarad': '㎊', 'nanofarad': '㎋', 'microfarad': '㎌', 'becquerel': '㏃', 'candela': '㏅', 'roentgen': '㏆', 'centiare': '㏇', 'decibels': '㏈', 'gray': '㏉', 'hectare': '㏊', 'horsepower': '㏋', 'kilo_kaiser': '㏍', 'kiloton': '㏏', 'lumen': '㏐', 'natural_log': '㏑', 'logarithm': '㏒', 'lux': '㏓', 'millibar': '㏔', 'thousanth': '㏕', 'mole': '㏖', 'acid_base': '㏗', 'squarePR': '㏚', 'steradian': '㏛', 'sievert': '㏜', 'weber': '㏝', 'volt_per_meter': '㏞', 'amp_per_meter': '㏟', 'gallon': '㏿', 'ante_meridiem': '㏂', 'post_meridiem': '㏘', 'parts_per_million': '㏙', 'meter_squared': '㎡', 'picosecond': '㎰', 'radian': '㎭'}
	
