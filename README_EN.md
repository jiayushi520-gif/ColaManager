# ColaManager

Version 2.0.0 release candidate. Native Apple Shortcuts for cola logging, rinsing,
brushing, weekly quotas and next-week penalties. No third-party app, Python runtime,
API key or server is required by the native workflows.

Install dist/ColaManager-v2.0.0.shortcut from the delivery archive and keep its in-app
name **ColaManager**. Install optional entry shortcuts afterwards. In the development
checkout, new signed artifacts are in dist/v2/. Export old data before upgrading.

Choose **On My iPhone** in every picker. Explicitly confirm first installation; on
later runs select the latest state snapshot. Each write creates a new file and asks
you to reselect it for verification. Previous files remain available for rollback.
The workflow cannot discover the latest file or enforce a local provider. Selecting
stale snapshots can create divergent histories. No atomic transaction is claimed.

The original quota, penalties, 48-hour check-ins, reminder creation, history ranges,
statistics, JSON export/restore and entry shortcuts are retained. Today and About
are new. Migration preserves v1 dictionaries and extension fields. Restore previews
and confirmation precede a new snapshot save.

File operations require interaction. Weekly reports and deadline checks cannot be
promised to run unattended while locked. The independent bedtime reminder does not
read data. The legacy optional Scriptable numeric widget remains as source, outside
the dependency-free distribution. Native button widgets are not a live numeric dashboard.

The user confirmed that full-app basic tests passed on iOS 26.1 with iCloud Drive disabled,
including record rereading, check-ins, duplicate prevention, backup/restore, offline use
and reboot persistence. Advanced and failure-case acceptance remains pending;
signing and development tests do not certify iPhone runtime behavior. System Reminders
may sync according to account settings; the workflow has no network actions.

Keep independent JSON backups. Device loss, reset or deletion can destroy local data.
No screenshots or public install links have been fabricated.
[Source](https://github.com/jiayushi520-gif/ColaManager) and
[signed downloads](https://github.com/jiayushi520-gif/ColaManager/releases) are hosted on GitHub.
[RoutineHub](https://routinehub.co/shortcut/26832/) and
[Apple install link](https://www.icloud.com/shortcuts/58dce0926d154d95a3c3698637ad4a06).
The shared name is ColaManager-v2.0.0. For optional entry shortcuts, back up/rename any old
ColaManager first, then rename the new main shortcut to ColaManager.
Licensed under MIT with owner approval; see LICENSE.
See README.md and docs/ for build and test details.
