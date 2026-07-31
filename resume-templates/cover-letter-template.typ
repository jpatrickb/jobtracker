// Cover Letter (TAILORED TEMPLATE)
//
// Build with Typst:
//   typst compile cover-letter-template.typ cover-letter-template.pdf
//
// Voice: plain, warm, grounded. No em dash in prose, no hype words
// (leveraged, spearheaded, synergy). Written fresh per application from your
// evidence/bullet library + the job description, not copied from a
// talking-points bank.
// Every claim must be accurate and traceable to verified evidence -- same
// non-negotiable rule as the resume.
//
// Deliberately different letterhead from the resume template (sans-serif
// font, accent-colored rule) -- this is a letter, not a resume, and should
// not just be the resume header pasted above paragraphs.

#set page(
  paper: "us-letter",
  margin: (top: 0.9in, bottom: 0.9in, left: 1in, right: 1in),
)
#set text(font: "Helvetica", size: 11pt, lang: "en")
#set par(leading: 0.75em, spacing: 1.1em, justify: false)

#let accent = rgb("#1B3A5C")

// ==================== LETTERHEAD ====================

#grid(
  columns: (58%, 1fr),
  align: (left, right),
  [
    #text(size: 19pt, weight: "bold", tracking: 0.5pt)[Your Name] \
    #v(4pt, weak: true)
    #text(size: 10pt, weight: "bold", fill: accent, tracking: 0.5pt)[YOUR PROFESSIONAL TITLE]
  ],
  [
    #set text(size: 9.5pt, fill: rgb("#000000a6"))
    #text(fill: accent)[Email:] your.email\@example.com \
    #text(fill: accent)[Phone:] (555) 555-5555 \
    #text(fill: accent)[LinkedIn:] #link("https://linkedin.com/in/yourhandle")[linkedin.com/in/yourhandle] \
    #text(fill: accent)[Web:] #link("https://yourportfolio.example.com")[yourportfolio.example.com]
  ],
)

#v(8pt, weak: true)
#line(length: 100%, stroke: 1.4pt + accent)
#v(22pt, weak: true)

// %%TODO%% Date, e.g. datetime.today() formatted, or a fixed date string
#datetime.today().display("[month repr:long] [day], [year]")

#v(6pt, weak: true)
// Recipient block -- omit lines you don't have (many postings don't name a person)
%%TODO%%: Hiring Manager Name (or delete this line) \
%%TODO%%: Company Name

#v(10pt, weak: true)
// Salutation -- "Dear [Name]," if known, otherwise "Dear Hiring Manager," or "Dear [Team] Team,"
Dear %%TODO%%,

// %%TODO%% Opening paragraph: the role, and a brief, genuine reason this one
// caught your interest. Avoid generic template language ("I am writing to
// express my interest in...").
%%TODO%%: opening paragraph.

// %%TODO%% Body paragraph(s), 1-2: proof points tied to what the JD actually
// asks for. Pull facts from your evidence/bullet library. Connect them to
// the role's real requirements, don't just restate resume bullets verbatim.
%%TODO%%: body paragraph(s).

// %%TODO%% Closing paragraph: why this company specifically (something true
// and specific, not flattery), and a plain closing ask/offer to talk further.
%%TODO%%: closing paragraph.

#v(4pt, weak: true)
Thanks, \
#strong[Your Name]
