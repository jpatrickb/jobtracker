# inbox/

Postings you (or a capture tool/browser extension/etc.) have dropped as files but haven't scored
yet. `jobtracker inbox` lists what's waiting; `jobtracker inbox-dupes` flags likely-duplicate postings
before you spend time scoring the same job twice.

Once a posting from here has been scored, its text moves into `listings/<id>.md` and it should be
removed from this directory — an empty `inbox/` means "everything's been looked at."

## File naming convention

Any `*.md` filename works (other than `README.md`, which is ignored); a short slug plus a
timestamp or source tag is a reasonable default, e.g.:

```
inbox/acme-senior-engineer-2026-01-15.md
```

A file may optionally start with a `---`-delimited frontmatter block (e.g. a `url:` line) if
whatever captured it wants to carry that metadata through to scoring; the body below it is the
raw posting text.
