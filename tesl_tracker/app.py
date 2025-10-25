"""
TESL Balance Tracker - Main Application

A comprehensive web application for tracking TESL balances for NSW Health Staff Specialists.
"""

import gradio as gr
import pandas as pd
from datetime import date
from typing import Optional

from .config.settings import get_config
from .utils.database import get_db, init_database, check_database_connection
from .utils.seed_data import seed_all
from .utils.financial_year import get_current_financial_year, format_financial_year
from .models import (
    StaffSpecialist, Facility, Claim, ClaimType, ClaimStatus,
    EmploymentScheme, StaffLevel
)
from .services import (
    StaffService, EntitlementService, ClaimService,
    ApprovalService, ReportingService
)


config = get_config()


# ============================================================================
# Dashboard Tab
# ============================================================================

def load_dashboard():
    """Load dashboard summary"""
    try:
        with get_db() as db:
            reporting_service = ReportingService(db)
            current_fy = get_current_financial_year()

            stats = reporting_service.get_utilization_statistics(current_fy)

            if stats.get("no_data"):
                return (
                    "No Data Available",
                    0, 0, 0, 0, 0.0,
                    "Please add staff specialists and entitlements to see statistics."
                )

            summary_text = f"""
## TESL Balance Tracker Dashboard
### {stats['financial_year_display']}

**Overall Statistics:**
- Total Staff: {stats['total_staff']}
- Total TESL Liability: ${stats['total_entitlement']:,.2f}
- Total Claimed: ${stats['total_claimed']:,.2f}
- Total Pending: ${stats['total_pending']:,.2f}
- Total Available: ${stats['total_available']:,.2f}

**Utilization Metrics:**
- Overall Utilization Rate: {stats['overall_utilization_rate']:.1f}%
- Average Staff Utilization: {stats['average_utilization_rate']:.1f}%
- Staff Fully Utilized (≥90%): {stats['staff_fully_utilized']}
- Staff Not Utilized (0%): {stats['staff_not_utilized']}
- Staff at Maximum Balance: {stats['staff_at_maximum']}
            """

            return (
                summary_text,
                stats['total_staff'],
                stats['total_entitlement'],
                stats['total_claimed'],
                stats['total_available'],
                stats['overall_utilization_rate'],
                ""
            )

    except Exception as e:
        return f"Error loading dashboard: {str(e)}", 0, 0, 0, 0, 0.0, str(e)


# ============================================================================
# Staff Management Tab
# ============================================================================

def load_facilities():
    """Load facility list for dropdown"""
    try:
        with get_db() as db:
            facilities = db.query(Facility).filter(Facility.is_active == True).all()
            return [(f"{f.facility_name} ({f.facility_code})", f.id) for f in facilities]
    except Exception as e:
        return [("Error loading facilities", None)]


def search_staff(search_term, facility_id):
    """Search for staff specialists"""
    try:
        with get_db() as db:
            staff_service = StaffService(db)

            if search_term:
                staff_list = staff_service.search_staff(
                    search_term=search_term,
                    facility_id=facility_id if facility_id else None
                )
            elif facility_id:
                staff_list = staff_service.get_staff_by_facility(facility_id)
            else:
                staff_list = db.query(StaffSpecialist).filter(
                    StaffSpecialist.is_active == True
                ).limit(50).all()

            if not staff_list:
                return pd.DataFrame({"Message": ["No staff found"]})

            data = []
            for staff in staff_list:
                data.append({
                    "ID": staff.id,
                    "Employee ID": staff.employee_id,
                    "Name": staff.full_name,
                    "Email": staff.email,
                    "Facility": staff.facility.facility_name if staff.facility else "",
                    "Level": staff.employment_scheme.value,
                    "FTE": staff.fte,
                    "Start Date": staff.start_date,
                    "TESL Eligible": "Yes" if staff.tesl_eligible else "No"
                })

            return pd.DataFrame(data)

    except Exception as e:
        return pd.DataFrame({"Error": [str(e)]})


def add_staff(employee_id, first_name, last_name, email, facility_id, scheme, level, fte, start_date):
    """Add new staff specialist"""
    try:
        with get_db() as db:
            staff_service = StaffService(db)

            # Convert scheme and level strings to enums
            employment_scheme = EmploymentScheme[scheme.replace(" ", "_").upper()]
            staff_level = StaffLevel[f"LEVEL_{level}"] if level else None

            staff = staff_service.create_staff(
                employee_id=employee_id,
                first_name=first_name,
                last_name=last_name,
                email=email,
                facility_id=facility_id,
                employment_scheme=employment_scheme,
                staff_level=staff_level,
                fte=float(fte),
                start_date=start_date
            )

            return f"✓ Successfully added {staff.full_name} (ID: {staff.employee_id})"

    except Exception as e:
        return f"✗ Error: {str(e)}"


# ============================================================================
# Balance Enquiry Tab
# ============================================================================

def check_balance(staff_id, fy=None):
    """Check TESL balance for a staff member"""
    try:
        if not staff_id:
            return "Please enter a Staff ID", pd.DataFrame()

        with get_db() as db:
            reporting_service = ReportingService(db)

            if not fy:
                fy = get_current_financial_year()

            summary = reporting_service.get_staff_balance_summary(int(staff_id), int(fy))

            if summary.get("no_entitlement"):
                balance_text = f"""
## Balance Summary - {summary['financial_year_display']}

**Staff:** {summary['staff_name']}

No entitlement record found for this financial year.
                """
                return balance_text, pd.DataFrame()

            balance_text = f"""
## TESL Balance Summary - {summary['financial_year_display']}

**Staff Details:**
- Name: {summary['staff_name']}
- Employee ID: {summary['employee_id']}
- Facility: {summary['facility']}

**Balance Information:**
- Opening Balance: ${summary['opening_balance']:,.2f}
- Annual Entitlement: ${summary['annual_entitlement']:,.2f}
- **Total Available: ${summary['total_entitlement']:,.2f}**

**Usage:**
- Claimed (Approved/Paid): ${summary['claimed_amount']:,.2f}
- Pending Approval: ${summary['pending_amount']:,.2f}
- **Current Balance: ${summary['current_balance']:,.2f}**

**Limits:**
- Maximum Balance: ${summary['maximum_balance']:,.2f}
- Expiring Amount: ${summary['expiring_amount']:,.2f}
- Utilization Rate: {summary['utilization_rate']:.1f}%

**Claims Summary:**
- Total Claims: {summary['total_claims']}
            """

            # Get claims history
            claims = db.query(Claim).filter(
                Claim.staff_specialist_id == int(staff_id),
                Claim.financial_year == int(fy)
            ).all()

            if claims:
                claims_data = []
                for claim in claims:
                    claims_data.append({
                        "Reference": claim.claim_reference,
                        "Type": claim.claim_type.value,
                        "Activity": claim.activity_name,
                        "Amount": f"${claim.claim_amount:,.2f}",
                        "Status": claim.status.value,
                        "Submitted": claim.submitted_date or "-"
                    })
                claims_df = pd.DataFrame(claims_data)
            else:
                claims_df = pd.DataFrame({"Message": ["No claims for this period"]})

            return balance_text, claims_df

    except Exception as e:
        return f"Error: {str(e)}", pd.DataFrame()


# ============================================================================
# Claims Management Tab
# ============================================================================

def submit_new_claim(staff_id, claim_type, amount, activity_name, start_date, end_date, description):
    """Submit a new TESL claim"""
    try:
        with get_db() as db:
            claim_service = ClaimService(db)

            claim_type_enum = ClaimType[claim_type.replace(" ", "_").upper()]

            claim = claim_service.create_claim(
                staff_id=int(staff_id),
                claim_type=claim_type_enum,
                claim_amount=float(amount),
                activity_name=activity_name,
                activity_start_date=start_date,
                activity_end_date=end_date,
                activity_description=description
            )

            claim_service.submit_claim(claim.id)

            return f"✓ Claim submitted successfully! Reference: {claim.claim_reference}"

    except Exception as e:
        return f"✗ Error: {str(e)}"


def load_pending_claims():
    """Load all pending claims"""
    try:
        with get_db() as db:
            claims = db.query(Claim).filter(
                Claim.status.in_([ClaimStatus.SUBMITTED, ClaimStatus.UNDER_REVIEW])
            ).join(StaffSpecialist).all()

            if not claims:
                return pd.DataFrame({"Message": ["No pending claims"]})

            data = []
            for claim in claims:
                data.append({
                    "Claim ID": claim.id,
                    "Reference": claim.claim_reference,
                    "Staff": claim.staff_specialist.full_name,
                    "Type": claim.claim_type.value,
                    "Activity": claim.activity_name,
                    "Amount": f"${claim.claim_amount:,.2f}",
                    "Submitted": claim.submitted_date,
                    "Status": claim.status.value
                })

            return pd.DataFrame(data)

    except Exception as e:
        return pd.DataFrame({"Error": [str(e)]})


def approve_claim_action(claim_id):
    """Approve a claim"""
    try:
        with get_db() as db:
            claim_service = ClaimService(db)
            claim = claim_service.approve_claim(int(claim_id), "admin")
            return f"✓ Claim {claim.claim_reference} approved successfully"
    except Exception as e:
        return f"✗ Error: {str(e)}"


def reject_claim_action(claim_id, reason):
    """Reject a claim"""
    try:
        with get_db() as db:
            claim_service = ClaimService(db)
            claim = claim_service.reject_claim(int(claim_id), reason, "admin")
            return f"✓ Claim {claim.claim_reference} rejected"
    except Exception as e:
        return f"✗ Error: {str(e)}"


# ============================================================================
# Reports Tab
# ============================================================================

def generate_expiring_balances_report(fy=None):
    """Generate report of expiring balances"""
    try:
        with get_db() as db:
            reporting_service = ReportingService(db)

            if not fy:
                fy = get_current_financial_year()

            results = reporting_service.get_expiring_balances_report(int(fy))

            if not results:
                return pd.DataFrame({"Message": ["No staff with expiring balances"]})

            return pd.DataFrame(results)

    except Exception as e:
        return pd.DataFrame({"Error": [str(e)]})


def generate_facility_report(facility_id, fy=None):
    """Generate facility summary report"""
    try:
        with get_db() as db:
            reporting_service = ReportingService(db)

            if not fy:
                fy = get_current_financial_year()

            summary = reporting_service.get_facility_summary(int(facility_id), int(fy))

            report_text = f"""
## Facility TESL Summary - {summary['financial_year_display']}

**Facility:** {summary['facility_name']} ({summary['facility_code']})

**Staff Overview:**
- Active Staff: {summary['staff_count']}
- Staff with Expiring Balances: {summary['staff_with_expiring_balances']}

**Financial Summary:**
- Total TESL Entitlements: ${summary['total_entitlement']:,.2f}
- Total Claimed: ${summary['total_claimed']:,.2f}
- Total Pending: ${summary['total_pending']:,.2f}
- Current Balance: ${summary['total_balance']:,.2f}
- Expiring Amount: ${summary['total_expiring']:,.2f}

**Utilization:**
- Utilization Rate: {summary['utilization_rate']:.1f}%

**Claims Summary:**
- Total Claims: {summary['total_claims']}
            """

            return report_text

    except Exception as e:
        return f"Error: {str(e)}"


# ============================================================================
# Main Application
# ============================================================================

def create_app():
    """Create the Gradio application"""

    with gr.Blocks(title="TESL Balance Tracker", theme=gr.themes.Soft()) as app:
        gr.Markdown("""
# TESL Balance Tracker
## NSW Health Staff Specialists - Training, Education and Study Leave Management

Track and manage TESL entitlements, balances, and claims in accordance with the Staff Specialists (State) Award 2022.
        """)

        with gr.Tabs():
            # Dashboard Tab
            with gr.Tab("Dashboard"):
                gr.Markdown("### System Overview")
                refresh_btn = gr.Button("Refresh Dashboard", variant="primary")

                dashboard_summary = gr.Markdown()
                with gr.Row():
                    total_staff_box = gr.Number(label="Total Staff", interactive=False)
                    total_liability_box = gr.Number(label="Total TESL Liability ($)", interactive=False)
                    total_claimed_box = gr.Number(label="Total Claimed ($)", interactive=False)

                with gr.Row():
                    total_available_box = gr.Number(label="Total Available ($)", interactive=False)
                    utilization_box = gr.Number(label="Utilization Rate (%)", interactive=False)

                dashboard_status = gr.Textbox(label="Status", interactive=False)

                refresh_btn.click(
                    load_dashboard,
                    outputs=[
                        dashboard_summary, total_staff_box, total_liability_box,
                        total_claimed_box, total_available_box, utilization_box,
                        dashboard_status
                    ]
                )

            # Staff Management Tab
            with gr.Tab("Staff Management"):
                gr.Markdown("### Manage Staff Specialists")

                with gr.Row():
                    search_box = gr.Textbox(label="Search (Name, Email, or Employee ID)", placeholder="Enter search term...")
                    facility_filter = gr.Dropdown(label="Filter by Facility", choices=load_facilities())
                    search_btn = gr.Button("Search", variant="primary")

                staff_results = gr.Dataframe(label="Staff Results")

                search_btn.click(
                    search_staff,
                    inputs=[search_box, facility_filter],
                    outputs=staff_results
                )

                gr.Markdown("### Add New Staff Specialist")

                with gr.Row():
                    new_emp_id = gr.Textbox(label="Employee ID")
                    new_first_name = gr.Textbox(label="First Name")
                    new_last_name = gr.Textbox(label="Last Name")

                with gr.Row():
                    new_email = gr.Textbox(label="Email")
                    new_facility = gr.Dropdown(label="Facility", choices=load_facilities())

                with gr.Row():
                    new_scheme = gr.Dropdown(
                        label="Employment Scheme",
                        choices=["Level 1", "Level 2", "Level 3", "Level 4", "Level 5", "Scheme D"]
                    )
                    new_level = gr.Dropdown(label="Staff Level", choices=["1", "2", "3", "4", "5"])
                    new_fte = gr.Number(label="FTE", value=1.0, minimum=0.1, maximum=1.0, step=0.1)

                with gr.Row():
                    new_start_date = gr.Textbox(label="Start Date (YYYY-MM-DD)", value=str(date.today()))

                add_staff_btn = gr.Button("Add Staff Specialist", variant="primary")
                add_staff_status = gr.Textbox(label="Status", interactive=False)

                add_staff_btn.click(
                    add_staff,
                    inputs=[
                        new_emp_id, new_first_name, new_last_name, new_email,
                        new_facility, new_scheme, new_level, new_fte, new_start_date
                    ],
                    outputs=add_staff_status
                )

            # Balance Enquiry Tab
            with gr.Tab("Balance Enquiry"):
                gr.Markdown("### Check TESL Balance")

                with gr.Row():
                    balance_staff_id = gr.Number(label="Staff ID", precision=0)
                    balance_fy = gr.Number(
                        label="Financial Year",
                        value=get_current_financial_year(),
                        precision=0
                    )
                    check_balance_btn = gr.Button("Check Balance", variant="primary")

                balance_summary = gr.Markdown()
                claims_history = gr.Dataframe(label="Claims History")

                check_balance_btn.click(
                    check_balance,
                    inputs=[balance_staff_id, balance_fy],
                    outputs=[balance_summary, claims_history]
                )

            # Claims Management Tab
            with gr.Tab("Claims Management"):
                gr.Markdown("### Submit New Claim")

                with gr.Row():
                    claim_staff_id = gr.Number(label="Staff ID", precision=0)
                    claim_type = gr.Dropdown(
                        label="Claim Type",
                        choices=["Conference", "Training", "Education", "Study Leave", "Course", "Workshop", "Seminar", "Other"]
                    )
                    claim_amount = gr.Number(label="Claim Amount ($)", minimum=0)

                with gr.Row():
                    claim_activity = gr.Textbox(label="Activity Name")
                    claim_start = gr.Textbox(label="Start Date (YYYY-MM-DD)", value=str(date.today()))
                    claim_end = gr.Textbox(label="End Date (YYYY-MM-DD)", value=str(date.today()))

                claim_description = gr.Textbox(label="Description/Purpose", lines=3)

                submit_claim_btn = gr.Button("Submit Claim", variant="primary")
                submit_claim_status = gr.Textbox(label="Status", interactive=False)

                submit_claim_btn.click(
                    submit_new_claim,
                    inputs=[
                        claim_staff_id, claim_type, claim_amount,
                        claim_activity, claim_start, claim_end, claim_description
                    ],
                    outputs=submit_claim_status
                )

                gr.Markdown("### Pending Claims")

                refresh_claims_btn = gr.Button("Refresh Pending Claims")
                pending_claims_table = gr.Dataframe(label="Pending Claims")

                refresh_claims_btn.click(
                    load_pending_claims,
                    outputs=pending_claims_table
                )

                gr.Markdown("### Approve/Reject Claims")

                with gr.Row():
                    approve_claim_id = gr.Number(label="Claim ID", precision=0)
                    approve_btn = gr.Button("Approve", variant="primary")
                    reject_reason = gr.Textbox(label="Rejection Reason")
                    reject_btn = gr.Button("Reject", variant="stop")

                approval_status = gr.Textbox(label="Status", interactive=False)

                approve_btn.click(
                    approve_claim_action,
                    inputs=approve_claim_id,
                    outputs=approval_status
                )

                reject_btn.click(
                    reject_claim_action,
                    inputs=[approve_claim_id, reject_reason],
                    outputs=approval_status
                )

            # Reports Tab
            with gr.Tab("Reports"):
                gr.Markdown("### Expiring Balances Report")

                with gr.Row():
                    expiring_fy = gr.Number(
                        label="Financial Year",
                        value=get_current_financial_year(),
                        precision=0
                    )
                    generate_expiring_btn = gr.Button("Generate Report", variant="primary")

                expiring_report = gr.Dataframe(label="Staff with Expiring Balances")

                generate_expiring_btn.click(
                    generate_expiring_balances_report,
                    inputs=expiring_fy,
                    outputs=expiring_report
                )

                gr.Markdown("### Facility Summary Report")

                with gr.Row():
                    facility_report_id = gr.Dropdown(label="Facility", choices=load_facilities())
                    facility_report_fy = gr.Number(
                        label="Financial Year",
                        value=get_current_financial_year(),
                        precision=0
                    )
                    generate_facility_btn = gr.Button("Generate Report", variant="primary")

                facility_report = gr.Markdown()

                generate_facility_btn.click(
                    generate_facility_report,
                    inputs=[facility_report_id, facility_report_fy],
                    outputs=facility_report
                )

            # System Tab
            with gr.Tab("System"):
                gr.Markdown("### System Administration")

                gr.Markdown("""
**Database Status:** Check if the database is initialized and accessible.

**Initialize Database:** Create all tables in the database.

**Seed Sample Data:** Populate the database with sample facilities, staff, and claims for testing.
                """)

                with gr.Row():
                    check_db_btn = gr.Button("Check Database Connection")
                    init_db_btn = gr.Button("Initialize Database", variant="secondary")
                    seed_db_btn = gr.Button("Seed Sample Data", variant="secondary")

                system_status = gr.Textbox(label="Status", interactive=False, lines=10)

                def check_db():
                    if check_database_connection():
                        return "✓ Database connection successful"
                    return "✗ Database connection failed"

                def init_db():
                    try:
                        init_database()
                        return "✓ Database initialized successfully"
                    except Exception as e:
                        return f"✗ Error: {str(e)}"

                def seed_db():
                    try:
                        with get_db() as db:
                            seed_all(db)
                        return "✓ Sample data seeded successfully"
                    except Exception as e:
                        return f"✗ Error: {str(e)}"

                check_db_btn.click(check_db, outputs=system_status)
                init_db_btn.click(init_db, outputs=system_status)
                seed_db_btn.click(seed_db, outputs=system_status)

        gr.Markdown("""
---
**TESL Balance Tracker** v1.0.0 | Based on Staff Specialists (State) Award 2022 and NSW Health Policy Directive PD2019_043
        """)

    return app


def main():
    """Main entry point"""
    print("=" * 60)
    print("TESL Balance Tracker for NSW Health Staff Specialists")
    print("=" * 60)

    # Check database connection
    print("\nChecking database connection...")
    if not check_database_connection():
        print("Database not initialized. Initializing now...")
        init_database()
        print("✓ Database initialized successfully")

    # Create and launch app
    app = create_app()
    app.launch(
        server_name=config.ui.server_name,
        server_port=config.ui.server_port,
        share=False
    )


if __name__ == "__main__":
    main()
