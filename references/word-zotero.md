<!-- SENTINEL: Preserves verified library identity, native citation refresh and field-safe current-path edits with a bundled read-only probe. -->
# Word + Zotero working contract

Load this reference when verifying literature or editing/inserting Zotero citations in the authoritative DOCX. Do not add separate audit documents or scientific assessment stages.

## Claim → literature → insertion

1. For each claim needing support in Introduction/Discussion (and whenever literature is needed elsewhere), read the **proposed manuscript claim** before searching. Identify the aspect that needs evidence: population, association, magnitude, direction, mechanism, methodology, or comparison with previous work.
2. Locate the original work via the provided anchor bibliography, PubMed, Crossref, publisher record, or a credible indexed source. Confirm **title, author, year, journal, DOI/PMID**, avoiding fabricated or conflated records. Confirm the paper truly supports this exact proposition, with appropriately comparable population/design and inferential strength.
3. If a claim is very specific (subgroup, number, method, mechanism), inspect the relevant methods/results/discussion in the source. Metadata or an abstract alone may not establish such detail. Distinguish genuine full-text verification from a title/abstract-level check.
4. If the original anchor source is unsuitable for the adapted claim, search for a genuine replacement. Where no verifiable source exists, narrow or remove the statement; do not attach a convenient but unrelated paper.
5. Use the **actual verified project Zotero collection**, including an upstream RRA collection or an explicitly chosen existing collection; do not create a second library for writing. Only for standalone work without a declared collection, default to one named after the manuscript project folder and create it if authorized and possible. Search existing Zotero items by DOI/PMID before importing to prevent duplicates. Import verified metadata and confirm the item is in the collection. Do not assume a `.ris`/BibTeX export is equivalent to importing an item into Zotero.
6. With a working Word/Zotero integration, use **Add/Edit Citation** or the verified Windows path below to insert editable fields (`Fields` preference). Use the journal-required or approved project style; otherwise use APA. Refresh citations and bibliography through Zotero and confirm library resolution.
7. Deletion: when a claim or entire section is dropped, remove its unused Word citation insertion point and refresh the bibliography. **Do not delete** the Zotero item from the project collection. If multiple claims still need the same paper, retain those insertion points.

## Windows automation when needed

- **Check connectivity before recovery.** A proxy/Privoxy error on `localhost:23119` does not establish that Zotero is down. Retry the loopback request without a proxy (for example, a request-local `urllib.request.ProxyHandler({})`); do not change global proxy settings or restart Zotero on that evidence alone.
- **Create usable field ranges.** Build citation JSON from actual library CSL metadata, canonical item URIs and verified collection membership. Follow Zotero's native `insertFieldRaw`: create a `wdFieldQuote` (35) with a nonempty quoted placeholder, then set `Code.Text` to the citation or bibliography ADDIN code. Direct ADDIN creation (81), or empty fields assigned ADDIN text, can leave no result separator and put display text outside the field. A native citation example, with a real library-bound `citationJson`, is:

  ```vb
  Set f = doc.Fields.Add(rng, 35, Chr(34) & "Zotero pending" & Chr(34), True)
  f.Code.Text = " ADDIN ZOTERO_ITEM CSL_CITATION " & citationJson & " "
  ```

- **Use native preferences and refresh.** When automation sets document preferences, use Word's `ZOTERO_PREF_n` custom properties in chunks of at most 255 characters, retaining the chosen style. `ZoteroRefresh` returns before its integration work finishes: use a bounded wait for populated results and bibliography, not a fixed sleep. Reacquire field objects after refresh because Zotero can replace the bibliography object.
- **Recover one task document.** If destination open/save fails while a control document opens, try one task-local temporary DOCX, save and close it in Word, verify it, then replace the authoritative file and remove the temporary copy. Avoid accumulating Word instances; recover only identifiable task-owned processes. Remove an orphaned hidden `~$` lock only after confirming its owner has closed; PowerShell may require `-Force` for that hidden file.

## Word editing safety

- Default to **in-place editing of the one current `.docx`**, without automatic persistent backup or alternate manuscript. When the researcher requests a separate file, use their specified destination.
- Treat Zotero fields, bookmarks, cross-reference fields, comments, section properties, and paragraph styles as protected document structure. Avoid `paragraph.text = ...` or rewriting whole paragraph XML containing fields. A textual conversion via Markdown/plain text may strip live citations. Do not blindly round-trip the working Word through tools that cannot preserve Zotero fields.
- Word's Zotero `Unlink Citations` removes dynamic links and is **forbidden in this working manuscript**. Zotero's formatted bibliography should be managed with the plugin, not hand-typed bibliography text.
- For editing prose surrounding an existing citation, retain its exact field element and placement when relevant; for changing a cited claim, relocate/edit/remove it intentionally rather than silently leave it attached to a different claim.
- When native Word/Zotero operations are unavailable, do not synthesize fake `ADDIN ZOTERO_ITEM` OOXML. Existing intact Zotero fields can be preserved with suitable targeted editing; new live insertions require a **verified** Zotero-compatible path. Record any outstanding insertion/import as an explicit blocker, not as a completed action.
- An optional read-only probe `<skill-directory>/scripts/docx_zotero_probe.py` reports visible Word field instructions. It is a smoke test, **not evidence** of correct content or an operational Zotero installation. Check the actual Word+Zotero integration when available.

## Minimum visible completion claim

You may report `Zotero complete` only after library membership and canonical item identity are confirmed, live fields survive saving, and Zotero has refreshed the cited-only bibliography with no pending locations. Code counts and `formattedCitation` metadata alone are insufficient: check valid field result ranges (including separators), nonempty visible citation results, and bibliography entries. Resolved item IDs may change from URI strings to local integers; verify canonical URIs and bibliographic identity (DOI/PMID when available) instead of assuming an ID type. Check saved prose and rendered layout. Otherwise report the exact completed subset and unresolved tasks.

Official workflow references:
- https://www.zotero.org/support/word_processor_plugin_usage
- https://www.zotero.org/support/kb/word_field_codes
- https://github.com/zotero/zotero-word-for-windows-integration/blob/main/build/zoteroWinWordIntegration/document.cpp (`insertFieldRaw`)
