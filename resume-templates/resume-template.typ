// Resume (TAILORED TEMPLATE)
//
// Build with Typst:
//   typst compile resume-template.typ resume-template.pdf
//
// This is the master template used by the `tailor-application` agent.
// Do not hand-write bullets directly here -- pull them from ../BULLETS.md (or
// your own bullet library), verify against ../EVIDENCE.md, and select/reorder
// per the job description.
//
// Placeholders are marked with %%TODO%%. Every %%TODO%% must be resolved
// before this is a finished resume.

#set page(
  paper: "us-letter",
  margin: (top: 0.5in, bottom: 0.5in, left: 0.6in, right: 0.6in),
)
#set text(font: "Times New Roman", size: 10.5pt, lang: "en")
#set par(leading: 0.62em, spacing: 0.62em, justify: false)
#set block(spacing: 0.65em)

// ==================== HELPER FUNCTIONS ====================

// Contact label, used in the header line (e.g. "Email:", "Phone:").
// #ci("Email", "your.email@example.com")
#let ci(tag, label) = box[
  #text(size: 9pt, fill: rgb("#000000a6"), weight: "bold")[#tag:] #h(3pt) #label
]

// Name rendered in Word-style small caps: large initials, smaller caps for
// the rest of each name part. Call with a list of name parts, e.g.
// #namecaps(("Your", "Name"))
#let namecaps(parts) = {
  let piece(word) = {
    let first = word.slice(0, 1)
    let rest = upper(word.slice(1))
    text(size: 20pt)[#first] + text(size: 14pt)[#rest]
  }
  parts.map(piece).join(h(0.22em))
}

// Ruled section header: rule above + below, bold uppercase text between.
// #rsection[EXPERIENCE]
#let rsection(body) = block[
  #v(6pt, weak: true)
  #line(length: 100%, stroke: 0.9pt + black)
  #v(2pt, weak: true)
  #text(size: 13pt, weight: "bold")[#upper(body)]
  #v(2pt, weak: true)
  #line(length: 100%, stroke: 0.9pt + black)
  #v(4pt, weak: true)
]

// Job/role header: title (bold) -- company (italic), dates flush right.
// #job("Title", "Company (location)", "Dates")
#let job(title, company, dates) = block[
  #v(3pt, weak: true)
  #grid(
    columns: (1fr, auto),
    align(left)[#strong[#title] --- #emph[#company]],
    align(right)[#strong[#dates]],
  )
  #v(1pt, weak: true)
]

// Tight bullet list matching the LaTeX \setlist tuning (small leftmargin,
// minimal spacing between items).
#let blist(..items) = list(
  ..items,
  marker: [•],
  indent: 0pt,
  body-indent: 0.6em,
  spacing: 1.5pt,
)
#set list(marker: [•], indent: 0pt, body-indent: 0.6em, spacing: 1.5pt)

// ==================== HEADER ====================

#align(center)[
  #namecaps(("Your", "Name"))
  #v(3pt, weak: true)
  #ci("Email", "your.email@example.com") #h(6pt) $|$ #h(6pt)
  #ci("Phone", "(555) 555-5555") #h(6pt) $|$ #h(6pt)
  #ci("LinkedIn", link("https://linkedin.com/in/yourhandle")[linkedin.com/in/yourhandle]) #h(6pt) $|$ #h(6pt)
  #ci("Web", link("https://yourportfolio.example.com")[yourportfolio.example.com])
]
#v(4pt, weak: true)

// %%TODO%% Summary: 2-3 sentences, tailored to this JD's role/keywords.
// Keep your core professional framing unless the role calls for a genuinely
// different framing -- don't invent a new identity per job.
#strong[Your professional framing, e.g. "Backend engineer focused on distributed systems"] who builds production systems. %%TODO%%: finish/tailor the rest of this summary for the role.

// ==================== EDUCATION ====================
#rsection[Education]

#grid(
  columns: (1fr, auto),
  align(left)[#strong[Your Degree / Major]],
  align(right)[#strong[Grad Month Year]],
)
#emph[Your University]
#blist(
  [GPA: X.XX $|$ Honors/Scholarships $|$ Dean's List (Nx)],
  [Coursework: Relevant Course 1, Relevant Course 2, Relevant Course 3],
)

// ==================== EXPERIENCE ====================
#rsection[Experience]

// %%TODO%% For each role below: pull 3-5 bullets from your bullet library,
// most relevant to the JD first. Verify every bullet against EVIDENCE.md
// before use. Light keyword mirroring is fine; new facts are not.

#job("Your Title", "Company Name (Location)", "Month Year – Present")
#blist(
  [%%TODO%%: bullet from bullet library (Company Name section)],
  [%%TODO%%],
  [%%TODO%%],
)

#job("Your Title", "Company Name, City, ST", "Month Year – Month Year")
#blist(
  [%%TODO%%: bullet from bullet library (Company Name section)],
  [%%TODO%%],
)

// %%TODO%% Additional roles, projects, or leadership: include only if
// relevant/space allows for this JD. Delete a #job(...) block entirely
// rather than leaving it empty.

// ==================== PROJECTS ====================
// %%TODO%% Include only projects relevant to this JD (see bullet library's
// Projects section). Delete this whole section if nothing is relevant and
// space is tight.
#rsection[Projects]

// ==================== SKILLS ====================
#rsection[Skills]
#blist(
  // %%TODO%% Pull the subset of skill categories/keywords relevant to this
  // JD from your bullet library's "Skills reference". Mirror the JD's own
  // terminology where true.
  [#strong[Category Name]: %%TODO%%],
)
