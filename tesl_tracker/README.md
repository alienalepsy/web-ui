# TESL Balance Tracker

A comprehensive web application for tracking **Training, Education and Study Leave (TESL)** entitlements, balances, and claims for NSW Health Staff Specialists.

## Overview

This application helps NSW Health facilities manage TESL entitlements in accordance with:
- **Staff Specialists (State) Award 2022**
- **NSW Health Policy Directive PD2019_043**
- **NSW Health Information Bulletins (IB2024_060, etc.)**

### Key Features

- **Staff Management**: Maintain records of staff specialists with employment details
- **Entitlement Tracking**: Automatic calculation of TESL entitlements based on level, FTE, and employment dates
- **Claims Management**: Submit, approve, and track TESL claims
- **Balance Enquiry**: Real-time balance checking with detailed history
- **Approval Workflow**: Multi-level approval process based on claim amounts
- **Reporting**: Comprehensive reports including expiring balances and facility summaries
- **Year-End Processing**: Automated rollover of balances to new financial year
- **Audit Trail**: Complete audit logging for compliance

## Business Requirements

### Staff Specialist Categories

- **Level 1-5 Staff Specialists**: Eligible for TESL entitlements
- **Scheme D Staff Specialists**: Not eligible for TESL (different entitlement scheme)

### Entitlement Rules

1. **Level 1 Staff Specialists**:
   - Annual entitlement: $38,000 (2022/23 onwards)
   - Maximum accrual: 2 years ($76,000)
   - Pro-rata based on FTE and employment period

2. **Level 2-5 Staff Specialists**:
   - Variable entitlements set by local No. 2 Account committee
   - Proportional to Level 1 entitlement
   - Facility-specific allocations

3. **Accrual and Rollover**:
   - Unused balances carry forward to next financial year
   - Maximum 2 years accrual
   - Excess over maximum expires at year end

4. **Claims**:
   - Used for conferences, training, education, courses
   - Require appropriate approvals
   - Deducted from current balance

## Installation

### Prerequisites

- Python 3.11 or higher
- pip or uv package manager

### Quick Start

1. **Clone or navigate to the directory**:
   ```bash
   cd tesl_tracker
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

   Or using uv:
   ```bash
   uv pip install -r requirements.txt
   ```

3. **Configure environment** (optional):
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

4. **Run the application**:
   ```bash
   python run.py
   ```

   Or:
   ```bash
   python -m tesl_tracker.app
   ```

5. **Access the web interface**:
   Open your browser to `http://localhost:7789`

## First Time Setup

When you first run the application:

1. Go to the **System** tab
2. Click **"Initialize Database"** to create the database tables
3. Click **"Seed Sample Data"** to populate with example data
4. Explore the sample data to understand the system

### Sample Data Includes:

- 3 facilities (RPA, RNSH, Liverpool Hospital)
- 5 staff specialists across different levels
- Sample TESL claims in various states
- User accounts for testing

## Usage Guide

### Dashboard

View overall TESL statistics including:
- Total staff and TESL liability
- Claimed and available amounts
- Utilization rates
- System-wide metrics

### Staff Management

**Search Staff**:
- Search by name, email, or employee ID
- Filter by facility
- View all active staff

**Add New Staff**:
- Enter employee details
- Select facility and employment scheme
- Set FTE and start date
- System automatically creates initial entitlement

### Balance Enquiry

**Check Balance**:
- Enter staff ID and financial year
- View detailed balance breakdown
- See claims history
- Monitor expiring balances

**Balance Information**:
- Opening balance (from previous year)
- Annual entitlement (based on level and FTE)
- Claimed amount (approved/paid)
- Pending amount (awaiting approval)
- Current available balance
- Maximum balance and expiry warnings

### Claims Management

**Submit Claim**:
- Enter staff ID and claim details
- Select claim type (conference, training, etc.)
- Specify activity dates and amount
- Provide description/purpose
- System validates against available balance

**Approve/Reject Claims**:
- View all pending claims
- Approve or reject with reasons
- Track approval workflow
- Automatic balance updates

### Reports

**Expiring Balances Report**:
- Lists staff with balances at risk of expiry
- Sorted by expiring amount
- Includes contact information
- Useful for year-end planning

**Facility Summary Report**:
- Overview of facility's TESL usage
- Total liability and utilization
- Staff statistics
- Claims summary

## Architecture

### Modular Design

The application uses a clean, extensible architecture:

```
tesl_tracker/
├── config/          # Configuration management
│   └── settings.py  # Centralized settings with Pydantic
├── models/          # SQLAlchemy ORM models
│   ├── base.py      # Base model with common fields
│   ├── staff.py     # Staff specialist model
│   ├── entitlement.py  # Entitlement tracking
│   ├── claim.py     # Claims and approvals
│   ├── facility.py  # Facilities and committees
│   ├── user.py      # User authentication
│   └── audit.py     # Audit logging
├── services/        # Business logic layer
│   ├── staff_service.py
│   ├── entitlement_service.py
│   ├── claim_service.py
│   ├── approval_service.py
│   └── reporting_service.py
├── utils/           # Utility functions
│   ├── database.py  # Database management
│   ├── financial_year.py  # FY calculations
│   └── seed_data.py # Sample data
├── ui/              # User interface components
├── app.py           # Main Gradio application
└── run.py           # Entry point
```

### Database Models

- **StaffSpecialist**: Employee records
- **Entitlement**: Annual TESL entitlements
- **EntitlementHistory**: Audit trail of balance changes
- **Claim**: TESL claim submissions
- **ClaimApproval**: Multi-level approval workflow
- **Facility**: Hospitals and facilities
- **No2AccountCommittee**: Committee members
- **User**: System users and roles
- **AuditLog**: Complete system audit trail

### Extensibility Features

1. **Configuration-Driven**:
   - All entitlement amounts in config
   - Easy to update for policy changes
   - Feature flags for new functionality

2. **Modular Services**:
   - Business logic separated from UI
   - Easy to add new services
   - Reusable across different interfaces

3. **Flexible Data Model**:
   - Extensible with custom fields
   - Support for facility-specific rules
   - Audit trail for all changes

4. **Database Agnostic**:
   - Supports SQLite (default), PostgreSQL, MySQL
   - Easy migration and scaling

## Future Enhancements

The application is designed to support:

- [ ] Email notifications for expiring balances
- [ ] Automated approval for small claims
- [ ] Document attachment upload
- [ ] Advanced analytics and dashboards
- [ ] Bulk data import/export
- [ ] REST API for integrations
- [ ] Mobile app interface
- [ ] SSO/LDAP authentication
- [ ] Multi-tenancy for multiple facilities

## Configuration

### Entitlement Settings

Modify `config/settings.py` or set environment variables:

```python
# Annual entitlement for Level 1
LEVEL_1_ANNUAL_ENTITLEMENT=38000.00

# Maximum accrual years
MAX_ACCRUAL_YEARS=2

# FY start (July 1 for Australian FY)
FINANCIAL_YEAR_START_MONTH=7
FINANCIAL_YEAR_START_DAY=1

# Pro-rata settings
ENABLE_FTE_PRORATA=True
ENABLE_PARTIAL_YEAR_PRORATA=True
```

### Approval Thresholds

Configure approval requirements:

```python
approval_thresholds = {
    "supervisor": 0,      # All claims
    "committee": 5000,    # Claims > $5000
    "finance": 10000,     # Claims > $10000
}
```

## Database Management

### SQLite (Default)

- Database file: `tesl_tracker.db`
- No additional setup required
- Suitable for single-facility use

### PostgreSQL (Production)

Update `.env`:
```bash
DATABASE_TYPE=postgresql
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=tesl_tracker
DATABASE_USER=tesl_user
DATABASE_PASSWORD=your_secure_password
```

### Backup and Recovery

**SQLite**:
```bash
# Backup
cp tesl_tracker.db tesl_tracker_backup.db

# Restore
cp tesl_tracker_backup.db tesl_tracker.db
```

**PostgreSQL**:
```bash
# Backup
pg_dump tesl_tracker > tesl_tracker_backup.sql

# Restore
psql tesl_tracker < tesl_tracker_backup.sql
```

## Security and Compliance

### Data Retention

- Audit logs: 7 years (Australian requirement)
- Financial records: 7 years
- Historical data: Indefinite

### Audit Trail

All actions are logged including:
- Staff changes
- Entitlement adjustments
- Claim submissions and approvals
- User activities
- System configuration changes

### Privacy

- Employee data encrypted at rest
- Access control by role
- Session timeouts
- Audit logging of access

## Support and Contribution

### Reporting Issues

For bugs or feature requests, please document:
- Steps to reproduce
- Expected vs actual behavior
- Screenshots if applicable
- System environment

### Development

To contribute:
1. Review the codebase structure
2. Follow existing patterns
3. Add tests for new features
4. Update documentation

## License

This application is developed for NSW Health in accordance with applicable licensing and usage policies.

## Version History

### Version 1.0.0 (Current)
- Initial release
- Staff specialist management
- Entitlement tracking and calculation
- Claims submission and approval
- Balance enquiry and reporting
- Audit logging
- Sample data for testing

---

**Based on**:
- Staff Specialists (State) Award 2022
- NSW Health Policy Directive PD2019_043
- NSW Health Information Bulletin IB2024_060

**For questions or support**, contact your facility's TESL administrator or IT support.
