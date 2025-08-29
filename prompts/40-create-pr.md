# Create a PR with Checklist

**Agent steps:**
1) Summarize the problem, the minimal fix, and any data rows changed.
2) Include a checklist:
   - [ ] Loader tests pass
   - [ ] README updated (Unit/Index/Description/Source)
   - [ ] No schema violations (value col == symbol; no extra cols)
   - [ ] Mappings complete
   - [ ] `uHrLoad` mean=1; `uHrCap` ∈ [0,1]
3) Add diffs inline or as a patch file.