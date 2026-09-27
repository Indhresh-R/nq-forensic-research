# CME-session volume profile

Research dataset only. No trading strategy.

The filename date is a UTC day. Session dates are assigned with `assign_cme_session`: a New York time at or after 18:00 belongs to that calendar date; an earlier time belongs to the previous calendar date. That session runs until 17:00 New York the next day.

Parameters live in `CONFIG.yaml`. Read `reports/DATASET_REPORT.md` and `reports/MECHANISM_REPORT.md` after a run.

```text
python volume_profile/code/validation.py --unit
python volume_profile/code/build_session_profiles.py
python volume_profile/code/validation.py --data
python volume_profile/code/build_research_dataset.py
python volume_profile/code/validation.py --events
python volume_profile/code/mechanism_tests.py
```
