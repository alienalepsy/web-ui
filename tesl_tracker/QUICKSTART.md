# TESL Balance Tracker - Quick Start Guide

Get up and running with the TESL Balance Tracker in 5 minutes!

## Installation

### Step 1: Install Dependencies

```bash
cd tesl_tracker
pip install -r requirements.txt
```

### Step 2: Run the Application

```bash
python run.py
```

The application will start and be available at: **http://localhost:7789**

## First Time Setup

1. **Open your browser** to http://localhost:7789

2. **Go to the System tab**

3. **Click "Initialize Database"** - Creates the database tables

4. **Click "Seed Sample Data"** - Adds example data for testing

5. **Done!** You now have a working system with sample data

## What's Included in Sample Data?

### Facilities
- Royal Prince Alfred Hospital (RPA)
- Royal North Shore Hospital (RNSH)
- Liverpool Hospital

### Staff Specialists
- 5 sample staff across different levels
- Mix of Level 1, Level 2, and Scheme D staff
- Various FTE percentages

### Sample Claims
- Approved and paid claims
- Pending claims awaiting approval
- Draft claims being prepared

## Quick Tour

### 1. Dashboard
- View overall system statistics
- See total TESL liability
- Check utilization rates

### 2. Staff Management
- Search for "John" or "Emma"
- View staff details and entitlements
- Add new staff specialists

### 3. Balance Enquiry
- Try Staff ID: **1** (John Smith)
- Financial Year: **2024**
- See detailed balance breakdown and claims history

### 4. Claims Management
- View pending claims requiring approval
- Submit a test claim for Staff ID 1
- Practice approving/rejecting claims

### 5. Reports
- Generate expiring balances report
- View facility summary for RPA (Facility ID: 1)

## Common Tasks

### Check a Staff Member's Balance

1. Go to **Balance Enquiry** tab
2. Enter Staff ID (try **1** for John Smith)
3. Click **Check Balance**
4. View balance details and claims history

### Submit a New Claim

1. Go to **Claims Management** tab
2. Fill in claim details:
   - Staff ID: 1
   - Claim Type: Conference
   - Amount: 2000
   - Activity Name: Test Conference
   - Dates: Use today's date
3. Click **Submit Claim**
4. Check status message

### Approve a Pending Claim

1. Go to **Claims Management** tab
2. Click **Refresh Pending Claims**
3. Note a Claim ID from the table
4. Enter the Claim ID in the approval section
5. Click **Approve** or **Reject**

### View Reports

**Expiring Balances:**
1. Go to **Reports** tab
2. Click **Generate Report** under Expiring Balances
3. View staff with balances at risk

**Facility Summary:**
1. Go to **Reports** tab
2. Select a facility from dropdown
3. Click **Generate Report** under Facility Summary
4. View comprehensive facility statistics

## Understanding TESL Entitlements

### For Level 1 Staff Specialists

- **Annual Entitlement**: $38,000 per year
- **Maximum Accrual**: 2 years ($76,000 total)
- **Pro-rata**: Based on FTE and employment period

**Example:**
- John Smith (Level 1, 1.0 FTE, started July 1)
- Annual entitlement: $38,000
- Can accumulate up to $76,000 over 2 years
- Unused balance rolls over to next year

### For Level 2-5 Staff Specialists

- Entitlements set by local No. 2 Account committee
- Typically lower than Level 1
- Facility-specific allocations

### For Scheme D Staff Specialists

- **Not eligible for TESL**
- Different entitlement scheme
- Not tracked in this system

## Financial Year

The application uses Australian financial year:
- **FY 2024** = July 1, 2023 to June 30, 2024
- **FY 2025** = July 1, 2024 to June 30, 2025

## Sample Scenarios to Try

### Scenario 1: New Staff Member

1. Go to **Staff Management**
2. Add a new staff specialist:
   - Employee ID: TEST001
   - Name: Jane Doe
   - Email: jane.doe@health.nsw.gov.au
   - Facility: RPA (or any facility)
   - Scheme: Level 1
   - Level: 1
   - FTE: 1.0
   - Start Date: Current date
3. Note the Staff ID assigned
4. Go to **Balance Enquiry** and check the new staff's balance

### Scenario 2: Full Claim Lifecycle

1. **Submit** a claim (Claims Management)
2. **Check balance** to see pending amount (Balance Enquiry)
3. **Approve** the claim (Claims Management)
4. **Check balance** again to see claimed amount updated

### Scenario 3: Year-End Analysis

1. Go to **Reports**
2. Generate **Expiring Balances Report**
3. Identify staff who need to use their TESL
4. Generate **Facility Summary** to see overall utilization

## Tips and Best Practices

### Search Efficiently
- Use partial names: "Joh" finds "John"
- Search by email domain: "@health.nsw.gov.au"
- Filter by facility for focused results

### Track Balances Regularly
- Check balances before year-end
- Monitor expiring amounts
- Plan training early to use entitlements

### Claim Management
- Submit claims with complete information
- Provide clear descriptions
- Attach documentation (future feature)

### Reporting
- Run expiring balances report quarterly
- Review facility summaries monthly
- Track utilization trends

## Troubleshooting

### Can't Connect to Database

**Problem**: Database initialization failed

**Solution**:
1. Check file permissions in the directory
2. Ensure Python has write access
3. Try manually: `python -c "from tesl_tracker.utils.database import init_database; init_database()"`

### Sample Data Already Exists

**Problem**: Error when seeding data

**Solution**: Sample data may already be loaded. Check the Staff Management tab to see if data exists.

### Port Already in Use

**Problem**: Port 7789 is already in use

**Solution**: Edit `.env` file and change `SERVER_PORT` to a different port (e.g., 7790)

### Claims Not Appearing

**Problem**: Submitted claim doesn't show up

**Solution**: Click the **Refresh** button in the relevant section

## Next Steps

Once comfortable with the basics:

1. **Read the Full Documentation**: See README.md for complete details
2. **Customize Configuration**: Edit settings in `config/settings.py`
3. **Clear Sample Data**: Reset database and add real data
4. **Explore Advanced Features**: Try different claim types, approval workflows
5. **Generate Reports**: Export data for analysis

## Configuration (Optional)

### Change Server Settings

Create a `.env` file:

```bash
cp .env.example .env
```

Edit `.env`:
```bash
SERVER_NAME=0.0.0.0  # Listen on all interfaces
SERVER_PORT=7789     # Change port if needed
```

### Update Entitlement Amounts

If policy changes, update in `config/settings.py`:

```python
level_1_annual_entitlement: float = 40000.00  # Updated amount
```

## Support

For issues or questions:

1. Check README.md for detailed documentation
2. Review the configuration settings
3. Check the audit log for system activities
4. Contact your system administrator

## Summary

You should now be able to:
- ✓ Run the TESL Balance Tracker
- ✓ Navigate the interface
- ✓ Check staff balances
- ✓ Submit and approve claims
- ✓ Generate reports
- ✓ Understand TESL entitlements

**Happy tracking!**

---

For detailed information, see the full [README.md](README.md)
