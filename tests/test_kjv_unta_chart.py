from fractions import Fraction
import unittest

from tools.kjv_archive import load_register
from tools.kjv_unta_chart import VERSION, chart_quantity


class BibleChartSpellings(unittest.TestCase):
    def test_source_letters_and_roman_readings(self):
        language, _ = load_register(VERSION)
        examples = [
            (2, 'ÕÅtus', 'ŧhātus'),
            (48, 'Çramen', 'ãramen'),
            (84, 'lanserß', 'lanserō'),
            (108, 'Õen×um', 'ŧhenēum'),
            (120, 'mesidÉl', 'mesidäl'),
            (1728, 'neksus ÕÍid', 'neksus ŧhėrid'),
        ]
        for amount, slots, roman in examples:
            with self.subTest(amount=amount):
                q = chart_quantity(amount, 'cardinal')
                self.assertEqual(q['form'], slots)
                self.assertEqual(language.reading(slots), roman)
                self.assertEqual(int(q['base12'], 12), amount)
        self.assertEqual(language.reading(language.maxima('ÕÅtus')), 'Ŧhātus')

    def test_compound_fraction_and_ordinal(self):
        self.assertEqual(chart_quantity(12**6 * 2, 'cardinal')['form'], 'ÕÅtus nßrum nekra')
        self.assertEqual(chart_quantity(3, 'ordinal')['form'], 'venik’t')
        sixth = chart_quantity(1, 'fraction', 6)
        self.assertEqual(sixth['form'], 'fßlem’Ñã ÕÅtus')
        self.assertEqual(Fraction(sixth['value']), Fraction(1, 6))
        self.assertEqual(chart_quantity(143, 'fraction', 12)['form'], 'yamen’Ñã yamen')
        self.assertEqual(chart_quantity(120, 'cardinal', notation='digits')['form'], 'À0')
