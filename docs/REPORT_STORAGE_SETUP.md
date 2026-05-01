# Extension Edge - Usage Analytics and Report Backup Setup

Extension Edge can store usage analytics and PDF report backups when Supabase credentials are configured in Streamlit Cloud.

The app still works if storage is not configured. In that case, no analytics or report backups are saved.

## What Gets Saved

For each submitted recommendation, the app stores:

- Field ID
- Timestamp
- County
- Result status
- Forage label
- Selected weeds
- Livestock label
- Primary recommendation
- Backup recommendation
- Engine and guide version
- Input JSON
- Result summary JSON
- PDF report path
- PDF report backup in Supabase Storage

## Privacy Note

Farm name and operator name are optional. If a user enters them, they are included in the input JSON and in the PDF backup. If you want anonymous analytics only, remove those optional fields from the app before public launch.

## Supabase Setup

1. Create a Supabase project.
2. Open the SQL editor.
3. Run the SQL in `supabase_schema.sql` from this project.
4. Open Project Settings -> API.
5. Copy:
   - Project URL
   - Service role key
6. In Streamlit Cloud, open the app settings.
7. Add these secrets:

```toml
[report_storage]
url = "https://YOUR-PROJECT-REF.supabase.co"
service_role_key = "YOUR-SUPABASE-SERVICE-ROLE-KEY"
table = "recommendation_reports"
bucket = "extension-edge-reports"
```

Do not commit a real service role key to GitHub.

## Usage Queries

Total submitted reports:

```sql
select count(*) as total_reports
from recommendation_reports;
```

Reports by county:

```sql
select county, count(*) as reports
from recommendation_reports
group by county
order by reports desc, county;
```

Reports by day:

```sql
select date_trunc('day', generated_at) as day, count(*) as reports
from recommendation_reports
group by day
order by day desc;
```

Recommendations by status:

```sql
select status, count(*) as reports
from recommendation_reports
group by status
order by reports desc;
```

Most selected weeds:

```sql
select weed, count(*) as selections
from recommendation_reports, unnest(weeds) as weed
group by weed
order by selections desc, weed;
```

## PDF Backups

PDF backups are saved in the `extension-edge-reports` Supabase Storage bucket under:

```text
FIELD-ID/timestamp.pdf
```

Example:

```text
AL-092A8C43/2026-05-01T17-35-25.pdf
```

The bucket should remain private. Download reports from the Supabase dashboard or by using a service-role authenticated script.
