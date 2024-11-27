## 1.14.0 (Current)

### Features
- Updated the format of the generated report to:
    - provide more space for the chart at the bottom
    - include legend items for confidence
    - remove redundant information (eg. years shown for every tile instead of just the month)
- Updated error reporting for OpenET data (2008 to 2023 data)
    - Now includes average cloud coverage percentage as a bar chart behind the lines
    - ET confidence interval is the OpenET Ensemble model min and max value range
- Release Notes are now generated automatically from the `CHANGELOG.md` file.
    - Persists yellow "new" state whether release notes for this version have been checked or not
- Persists the sorting options for the backlog

### Bug Fixes
- The `status` line on items in the queue would overflow out of the container if the job failed and it was too long