import unittest

from datetime import date

from app.financial_register.contribution_coverage.service import (
    _week_anchor_on_or_before,
    _generate_week_dates,
)


class ContributionCoverageTests(
    unittest.TestCase
):

    def test_ten_week_payment_spans_months(self):

        payment_date = date(
            2026,
            9,
            25,
        )

        first_week = (
            _week_anchor_on_or_before(
                payment_date,
                3,
            )
        )

        weeks = _generate_week_dates(
            first_week,
            10,
        )

        self.assertEqual(
            weeks[0],
            date(2026, 9, 24),
        )

        self.assertEqual(
            weeks[1],
            date(2026, 10, 1),
        )

        self.assertEqual(
            weeks[5],
            date(2026, 10, 29),
        )

        self.assertEqual(
            weeks[6],
            date(2026, 11, 5),
        )

        self.assertEqual(
            weeks[-1],
            date(2026, 11, 26),
        )

        self.assertEqual(
            len(weeks),
            10,
        )


if __name__ == "__main__":
    unittest.main()
