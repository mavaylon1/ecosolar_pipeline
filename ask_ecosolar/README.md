# ask_ecosolar

Forms that are otherwise ready (fillable PDF + drafted `mapping.json`) but are blocked on a
question only EcoSolar can answer — not a structural dead-end like `not_possible_forms/`, and not
a normal "still needs mapping work" item like an unfinished city in `forms/`. Kept here so the
blocker is visible and the form doesn't get silently skipped or assumed done.

## Kern County — Building Permit Application

**Why it's blocked:** can't pull real JNB data to test the mapping against, because EcoSolar
appears to have **zero job history in Kern County at all** — not an unincorporated-territory
naming issue like LA County turned out to be, where the fix was using a real community name
("Rowland Heights") instead of the county name. This looks structurally different: there's no
substitute city name to try, because there's no evidence of a Kern County job under *any* name.

**What we tried:**
1. Queried JNB for jobs with `city = "Kern County"` — 0 results (expected; "Kern County" isn't a
   real JNB city value, same class of problem as LA County).
2. Suspecting the same fix would apply (a real community name for unincorporated territory, e.g.
   Bakersfield-area or Ridgecrest-area places), scanned **every job in the system** (1,940 total —
   effectively the full history, paginated in batches of 100) for a zip code in the Kern County
   range (932xx–936xx, covering Bakersfield, Ridgecrest, Tehachapi, Delano, Wasco, Lake Isabella,
   California City, Mojave, and the rest of the county) regardless of what the `city` field said.
   **Zero matches.** So this isn't a naming mismatch to work around — there's simply no job on
   record anywhere in or near Kern County.

**What would unblock it:** EcoSolar completing (or already having, under a name/zip we didn't
think to check) a real Kern County job in JobNimbus. Once one exists, this form moves straight
into `forms/kern_county/` and gets tested the same way as every other city. If EcoSolar has done
Kern County work that predates or otherwise isn't in this JNB account, that's also worth
knowing — it would mean the scan above can't see it and a different lookup (or manual example
data) is needed instead.

**Files:** `BuildingPermitApplication_fillable.pdf` (already-fillable native PDF, no conversion
needed), `mapping.json` (fully drafted during Phase A — covers the main application page and part
of the Licensed Contractor/Workers' Comp Declaration section on page 2; pages 3-4's Property
Owner's Package and all Owner-Builder Declaration checkboxes are intentionally unmapped per
GUARDRAILS.md rule 1, same as every other city). The mapping itself was never run against real
data, since there's no real data to run it against.

## Long Beach — app-011 ("Express Building Permit Application")

**Why it's blocked:** it's unclear whether this is even the right document for EcoSolar's solar
permits, as opposed to Long Beach's other form, app-012 ("Express Electrical Permit"). app-011's
whole scope, once you get past its generic page-1 applicant/owner/contractor block, is a
repair/remodel questionnaire — window/door replacement, kitchen/bathroom repair, seismic retrofit
(cripple wall/anchor bolting/bracing), security bars/grilles/shutters, reroofing — with no
solar or electrical content anywhere across its 3 pages. app-012, by contrast, has an explicit "E12
New Rooftop Mounted Solar PV System" line item (kW DC/AC, module count) and was tested clean
against real JNB data during Phase A. Mapping app-011's generic page-1 block was easy (same
applicant/owner/contractor fields as every other city), so it *looks* done, but filing a
repair/remodel-scoped form for a solar-only job may be the wrong document entirely, or may need to
be filed alongside app-012 for reasons this pipeline can't determine from the PDFs alone.

**What we tried:** read every field on all 3 pages and confirmed the scope-of-work content doesn't
overlap with solar/electrical at all (see comparison with app-012 above). This is a judgment call
about Long Beach's actual permit-filing requirements, not something resolvable by reading the PDF
more carefully.

**What would unblock it:** confirming with Long Beach's building department (or EcoSolar's own
filing experience) whether solar PV permits require app-011 filed alongside app-012, or just
app-012 alone. If just app-012, this form can likely move to `not_possible_forms/` instead (wrong
document, not blocked-pending-data) rather than back into the pipeline.

**Files:** `app-011_fillable.pdf` (already-fillable native PDF), `mapping_011.json` (drafted during
Phase A — only the generic page-1 applicant/owner/contractor block is mapped; the repair/remodel
scope on pages 2-3 was left entirely unmapped as out of scope for solar). Never run against real
data, since it's not clear it should be filled out at all.

## Orange — Express Checklist for Residential Solar PV and ESS System

**Why it's blocked:** this PDF isn't a data-collection application like every other form in this
pipeline — it's roughly 150 Yes/No engineering self-certification questions (NEC 120% rapid
shutdown rule calculations, energy storage system installation location, bollard/wheel-barrier
specs, which roof plane the array sits on relative to the point of interconnection, smoke/heat
alarm requirements, rafter/truss spacing) that a real person has to answer per job by reviewing
that job's actual system design and site conditions. None of it is JNB data, and none of it is a
default that's safe to guess — these are code-compliance attestations, not form fields with a
knowable answer ahead of time. Only the identification block at the bottom of the last page (job
address, contractor/installer name, license/class, phone) has anything with a real JNB source, and
that's already mapped and tested clean.

**What we tried:** read every field across all 5 pages to confirm none of the ~150 checkboxes map
to anything EcoSolar tracks - they're all genuinely per-installation engineering judgment calls,
not gaps in what we're pulling from JNB.

**What would unblock it:** this isn't really "unblockable" by more mapping work - the open question
is whether EcoSolar wants this form in the automated pipeline at all, given automation can only
ever cover the small ID block at the bottom. Worth asking EcoSolar directly: is this checklist
something an engineer/installer fills out by hand per job (in which case it probably shouldn't be
in this pipeline at all, or belongs in `not_possible_forms/` instead), or is there a subset of the
~150 questions that's actually answerable the same way for every EcoSolar job (in which case it's
worth identifying that subset explicitly, rather than mapping the ID block alone and calling it
done)?

**Files:** `ExpressChecklist_fillable.pdf` (already-fillable native PDF), `mapping.json` (drafted
during Phase A — only the bottom identification block is mapped, tested clean against real data).
