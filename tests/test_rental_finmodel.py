"""Regression checks: rental capital lab must be independently calculable and unindexed."""
from pathlib import Path
import re
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT/'tools'/'rental_finmodel'/'index.html'


class RentalFinmodelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html=HTML.read_text(encoding='utf-8')
        cls.js=re.findall(r'<script>\s*(.*?)\s*</script>',cls.html,re.S)

    def test_self_contained_private_by_default(self):
        self.assertIn('noindex,nofollow,noarchive',self.html)
        self.assertNotIn('<script src=',self.html)
        self.assertNotIn('<form',self.html)
        self.assertNotIn('fetch(',self.html)
        self.assertNotIn('https://mc.yandex.ru/',self.html)
        self.assertEqual(len(self.js),2)
        self.assertIn('Матрица перелома',self.html)
        self.assertIn('скачать',self.html.lower())

    @unittest.skipUnless(shutil.which('node'),'Node.js not installed')
    def test_exact_daily_financial_mechanics(self):
        code=self.js[0]+'''
const assert=require('node:assert/strict');
const x=simulate(RENT_LAB_DEFAULTS);
assert.equal(x.series[99].active,1000);
assert.equal(x.series[99].monthlyRunRate,6000000);
assert.equal(x.series[99].debt,25800000);
assert.equal(x.summary.neededDay,210);
assert.equal(x.summary.peakNeed,37000000);
assert.equal(x.summary.positiveOperationalDay,211);
assert.equal(x.summary.rentOnlyDay,241);
assert.equal(x.summary.recoveryDay,396);
const r=simulate({...RENT_LAB_DEFAULTS,reservePercent:100});
assert.ok(r.summary.peakNeed>x.summary.peakNeed);
assert.ok(r.series.every(t=>t.cash>=t.deposits-1e-4));
const p=simulate({...RENT_LAB_DEFAULTS,rentalPrice:6200});
assert.equal(p.series[99].monthlyRunRate-x.series[99].monthlyRunRate,200000);
const z=simulate({...RENT_LAB_DEFAULTS,demand:0});
assert.equal(z.summary.recoveryDay,null);
assert.equal(z.summary.positiveOperationalDay,null);
const b=simulate({...RENT_LAB_DEFAULTS,rentalMonths:1,returnDelay:0,horizon:100});
assert.equal(b.series[30].purchases,0);
const s=simulate({...RENT_LAB_DEFAULTS,rentalMonths:1,buyoutPercent:100,horizon:100});
assert.ok(s.summary.totalSales>0);
'''
        run=subprocess.run(['node','-'],input=code,text=True,capture_output=True,timeout=25)
        self.assertEqual(run.returncode,0,run.stdout+run.stderr)

    @unittest.skipUnless(shutil.which('node'),'Node.js not installed')
    def test_both_javascript_parts_have_valid_syntax(self):
        for fragment in self.js:
            run=subprocess.run(['node','--check','-'],input=fragment,text=True,capture_output=True,timeout=12)
            self.assertEqual(run.returncode,0,run.stderr)


if __name__=='__main__':
    unittest.main()
