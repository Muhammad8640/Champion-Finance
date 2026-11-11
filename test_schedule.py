import unittest
from datetime import date
from schedule import occurrences, build_occurrences

class TestSchedule(unittest.TestCase):
    def tx(self, due='2026-01-31', frequency='Monthly'):
        return {'id':1,'name':'Rent','kind':'Expense','amount_cents':10000,'due_date':due,'frequency':frequency,'notes':''}

    def test_month_end_anchor(self):
        self.assertEqual(list(occurrences(self.tx(),date(2026,1,1),date(2026,4,30))),
                         [date(2026,1,31),date(2026,2,28),date(2026,3,31),date(2026,4,30)])

    def test_biweekly(self):
        self.assertEqual(list(occurrences(self.tx('2026-11-01','Every 2 weeks'),date(2026,11,10),date(2026,12,1))),
                         [date(2026,11,15),date(2026,11,29)])

    def test_one_time(self):
        self.assertEqual(list(occurrences(self.tx('2026-11-11','One-time'),date(2026,11,10),date(2026,11,20))),[date(2026,11,11)])

    def test_independent_paid_occurrences(self):
        tx = self.tx('2026-11-01','Weekly')
        states = {(1,'2026-11-08'):True}
        rows=build_occurrences([tx],states,date(2026,11,1),date(2026,11,15))
        self.assertEqual([r['paid'] for r in rows],[False,True,False])

if __name__ == '__main__': unittest.main()
