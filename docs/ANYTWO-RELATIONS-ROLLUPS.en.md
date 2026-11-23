# Anytwo relations and rollups: API verification

**[Français](ANYTWO-RELATIONS-ROLLUPS.fr.md) · [English](ANYTWO-RELATIONS-ROLLUPS.en.md)**

Verification of the local client on 31 October 2026, read-only. No migration test was written into Anytwo.

## Relation

The API documents a `kind: array` property with `xFormat.type: relation`. Values are arrays of `any://<objectId>` references. The descriptor notably carries `config.multiple` and target restrictions. Conversion must remap object, owner and property identifiers; Notion identifiers cannot be used directly. Inverse relations and targets outside the selection require a separate adaptation.

Source: [Anytwo data types](https://docs.any.org/database/data-types.html).

## Rollup

The local contract `GET /v1/openapi.json` does not advertise a dedicated “rollup” route. It does expose the generic property routes for collections/types and an `xFormat` that preserves its client namespace settings.

Reading properties already created in Test space confirms:

- `kind: object`, `xFormat.type: rollup`;
- JSON configuration serialized in `xFormat.anyui.rollup`;
- `relation.direction: own`, `relation.ownerId` and `relation.propertyId`;
- `target.ownerId` and `target.propertyId`;
- observed operators `calculate: sum` and `calculate: original`, with `showAs: number`.

The configuration can therefore be carried by the generic property API. Conversion must create schemas and relations before remapping these references. It must not write the Notion result in place of a calculation definition. The calculation behaviour after creation by the importer still has to be validated in the client: the observations do not prove that every Notion operator is equivalent.

The report now classifies the rollup as **to adapt**, rather than as a systematically frozen result. A function without a validated mapping keeps a warning and its archived result. The Notion module now configures these two aggregations when the relation and target property identifiers have been remapped. The descriptors were created in the dedicated test space; visual recalculation in the client still has to be verified.

Real examples are not copied into this document: personal identifiers and property names remain outside the repository.

## Fix and check of 1 November 2026

A relation restriction must set relation.targetTypes with the xKey of the target supertag. Without this restriction, the client also cannot offer the relation in the rollup editor. The target title uses the any.name identifier, associated with the target collection owner; the initially generated any / name pair matched no client choice.

After fixing the model imported into Sri, the client's real functions recognize the Projet → Name and Projet → Budget choices. The calculations return the expected names and the sums 100, 180 and 0. This validates these sum/original-value configurations; other operations still have to be verified. Property values were not rewritten.


## Two-way and average: check of 1 November 2026

The client stores the inverse link in xFormat.anyui.inverseOwner and inverseProperty. It only recognizes the pair when the opposite definition points back to the first one, with the destination owner/property identifiers. The Notion conversion applies them after creating the schemas, without recreating properties.

The native average operator is calculate: average in the same anyui.rollup descriptor. The generic API can carry it; evaluation by the client on the in-memory copy of imported objects reproduces the 53 numeric results of the controlled Notion report, including 11.5. No PATCH was sent for this verification: only the simulated definitions were replaced in the isolated calculation context. The average follows each object's own relation; it does not cover the whole target collection.
