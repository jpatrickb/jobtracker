# listings/

The raw text of every posting that has been **scored** (pass or reject), one file per tracker
record, written and maintained by `track` — never hand-edit these.

## File naming convention

`listings/<id>.md`, where `<id>` is exactly the tracker record's id (see `jobtracker show <id>`),
e.g. `listings/acme-senior-engineer.md`.

Each file starts with a `---`-delimited frontmatter block (company, role, source, url, structured
facts, date scored) followed by the raw posting body. `jobtracker doctor` checks that this frontmatter
stays consistent with the corresponding record in `.jobtracker/applications.json`.
