## 1.2.0 (Current)

### Features
- Updated the format of the generated report to:
    - provide more space for the line chart at the bottom
    - include legend items for confidence
    - make legends more readable (changes orientation of text labels on the color gradient bar displayed next to the ROI charts)
    - remove redundant information (eg. years shown for every tile instead of just the month)
- Updated error reporting for OpenET data (2008 to 2023 data)
    - Now includes average cloud coverage percentage as a bar chart behind the lines
    - ET confidence interval is the OpenET Ensemble model min and max value range
- Older PT-JPL data confidence is now displayed as a bar chart behind the lines for report standardization
- Release Notes are now generated automatically from the `CHANGELOG.md` file.
    - Persists yellow "new" state whether release notes for this version have been checked or not
- Persists the sorting options for the backlog
- Adds simple 404 page allowing the user to return back to the application

### Bug Fixes
- The `status` line on items in the queue would overflow out of the container if the job failed and it was too long
- Caches the list of users for 1 to 10 minutes (deep and shallow caching time limits) to reduce the number of fetches to the authentication provider (only visible to admins)
  - In some cases, this was leading to slow user list load times due to rate limiting on the Auth0 side
- Better handles missing uncertainty data (shows as unavailable in the report if we don't have any data for the month)


---

> **Note:** The changelog history started on 2024-12-04.