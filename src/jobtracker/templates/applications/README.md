# applications/

What actually gets submitted for a specific job: one folder per application, built fresh from
your resume material and the posting, not copied from a master resume.

A tracker record's `folder` field points here once an application has been tailored (see
`jobtracker show <id>`); `jobtracker doctor` expects any record whose status is `Tailored` or later to have
one.

## Folder naming convention

`applications/<company>-<role>/`, using the same slug convention as the tracker record's id, e.g.:

```
applications/acme-senior-engineer/
  resume.tex        (or resume.pdf, resume.docx -- whatever your toolchain produces)
  cover-letter.md    (only if the employer asked for one, or you chose to write one)
```
