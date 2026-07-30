# ADR-009: Rider identity separate from edition participation

## Status

Accepted — revises the entity model established in Milestone 1

## Context

The domain entities were designed in Milestone 1 before any real data had been fetched, so their fields encoded assumptions about what ProCyclingStats would provide. With the startlist parser complete and validated against every edition from 2015 to 2024, four of those assumptions turned out to be wrong.

**Rider identity was bound to a single edition.** `Rider.team_id` was a non-nullable foreign key to `teams.id`, and `Team` carries `tour_edition_id`. A rider row was therefore transitively bound to one edition, so a rider who raced in both 2015 and 2023 needed two rows with different UUIDs. This is the consequential one: rider identity would not survive across editions, and the form, history, and career-trajectory features planned for Milestones 3 and 4 all depend on following a rider across years.

**Birth date is not published.** `Rider.birth_date` was non-nullable, but the startlist gives only *age*. Age is measured against the edition, so it is a property of a participation rather than of the rider.

**Team nationality is not published.** `Team.nationality` was non-nullable and the source never provides it.

**Nationality is a country name, not a code.** Both nationality columns were `String(3)`, implying ISO 3166 alpha-3, but the source prints `Denmark`, `United States`, and `Isle of Man`.

There was also nowhere to record the abandonment kind and stage the parser extracts, even though roughly a fifth of each startlist does not reach Paris and abandonment is a prediction target in its own right.

## Decision

Model a startlist row as what it is: a **participation**, not a rider.

**`Rider`** becomes edition-independent, holding only name, nationality, source slug, and an optional birth date. It no longer references a team. `source_slug` is unique, which is what lets ingestion recognise a rider already stored from an earlier edition instead of inserting a duplicate.

**`RiderParticipation`** is new and holds everything true of a rider only for a given year: edition, rider, team, bib number, age, final general classification position, abandonment, and young-rider eligibility. It is unique on `(tour_edition_id, rider_id)` and on `(tour_edition_id, bib_number)`, since a rider appears once per edition and a number is worn by one rider.

**`Team`** stays scoped to an edition, because sponsors and therefore names change between years, and gains a `source_slug` as the thread linking a team's appearances. `nationality` becomes optional.

A participation either has a `final_gc_position` or an `abandonment`, never both; the entity enforces this. Storing abandonment as a `kind` plus an optional `stage_number` keeps "abandoned during stage 14" distinguishable from "withdrew, stage unrecorded".

`AbandonmentKind` lives in the domain, since leaving a race is a racing concept rather than a Wikipedia detail. The mapping from source tokens stays in the ingestion adapter, which also keeps the raw token so `HD` and `OTL` remain distinguishable and an `UNKNOWN` kind stays diagnosable.

Nationality stores the source's country name in a `String(64)` column. Normalising to ISO codes would mean maintaining a name-to-code table for edge cases like `Isle of Man` before anything needs codes; that can be added as a derived field once a consumer requires it.

## Consequences

Rider history across editions becomes a single query, which is what Milestones 3 and 4 need, and abandonment data now has a home so it can serve as a prediction target.

The cost is one more table and a join to answer "which team did this rider ride for", which is the correct shape for a question that is only meaningful once an edition is specified. Migration `002` performs the change and its downgrade drops participation rows rather than folding them back, because the previous shape cannot represent a rider who took part in more than one edition.

The ERD from Milestone 1 no longer matches for these three entities and has been updated. `RiderRating` and `TeamStrategy` reference `rider_id` and `team_id` and are unaffected.

Deferring ISO normalisation means nationality is not directly joinable against external country datasets until a mapping is added.
