from pathlib import Path

path = Path(r".\app\financial_register\ledger_service.py")
text = path.read_text(encoding="utf-8-sig")

anchor = '''        all_time_summary = (
            all_time_register.get("summary")
            or {}
        )
'''

if 'lifetime_member_totals' in text:
    print("Lifetime member totals patch already installed.")
    raise SystemExit(0)

patch = '''        # --------------------------------------------------------
        # LIFETIME MEMBER TOTALS
        #
        # The selected month controls the transaction rows and the
        # month's coverage amount, but each member's Total
        # Contributions must remain cumulative from the beginning.
        # --------------------------------------------------------

        all_time_members = (
            all_time_register.get("members")
            or []
        )

        lifetime_member_totals = {}

        for lifetime_member in all_time_members:

            if not isinstance(lifetime_member, dict):
                continue

            lifetime_member_id = (
                lifetime_member.get("member_id")
                or lifetime_member.get("Member ID")
                or lifetime_member.get("memberId")
                or lifetime_member.get("id")
            )

            if not lifetime_member_id:
                continue

            lifetime_total = lifetime_member.get(
                "total_contributions"
            )

            if lifetime_total is None:
                lifetime_total = (
                    lifetime_member.get("weekly_contributions")
                    or 0
                )

                lifetime_total += (
                    lifetime_member.get("registration_fees")
                    or 0
                )

            try:
                lifetime_total = float(
                    lifetime_total or 0
                )
            except (TypeError, ValueError):
                lifetime_total = 0.0

            lifetime_member_totals[
                str(lifetime_member_id).strip().upper()
            ] = round(
                lifetime_total,
                2
            )

        for current_member in members:

            if not isinstance(current_member, dict):
                continue

            current_member_id = (
                current_member.get("member_id")
                or current_member.get("Member ID")
                or current_member.get("memberId")
                or current_member.get("id")
            )

            if not current_member_id:
                continue

            lifetime_total = lifetime_member_totals.get(
                str(current_member_id).strip().upper()
            )

            if lifetime_total is not None:
                current_member["total_contributions"] = (
                    lifetime_total
                )

                current_member["lifetime_total_contributions"] = (
                    lifetime_total
                )

'''

if anchor not in text:
    raise SystemExit(
        "Lifetime totals insertion point not found. No file changed."
    )

text = text.replace(
    anchor,
    anchor + patch,
    1
)

path.write_text(
    text,
    encoding="utf-8"
)

print("LIFETIME MEMBER TOTALS PATCH INSTALLED.")
