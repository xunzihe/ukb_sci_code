# Data access and resource terms

## UK Biobank

The public files contain aggregate estimates, test statistics, P values, network counts and cohort-level summaries. Each SC test-table row represents an intensity-band–edge test, not a participant. No participant identifiers, dates of diagnosis or imaging, individual covariates, BOLD series, individual connectomes or MRI volumes are included.

Underlying participant-level data must be accessed through an approved UK Biobank project and its applicable agreements. Removing identifiers from a participant-level table does not make that table suitable for public redistribution. This repository neither grants UK Biobank access nor replaces the project's data-use agreement.

- [UK Biobank data access](https://www.ukbiobank.ac.uk/about-us/how-we-work/access-to-uk-biobank-data/)
- [UK Biobank publication and acknowledgement guidance](https://community.ukbiobank.ac.uk/hc/en-gb/articles/16594178325277-Submitting-publications-and-use-of-UK-Biobank-images)

Before public release, the approved project team is responsible for confirming that the selected aggregate outputs can be disclosed under its agreement. The actual application number and any required acknowledgements belong in the associated paper; none is fabricated in this repository.

## Brainnetome reference tables

`MLR/01_Code/atlas_reference/` contains region-level reference information, not UK Biobank participant data:

- `subregion_func_network_Yeo_updated.csv`: the locally named copy of the official Brainnetome functional-network table.
- `brainnetome_official_yeo7_yeo17_mapping.csv`: the study's indexed annotation table derived from the atlas resources.
- `Brainnetome_subcortical_36node_hierarchy.csv`: the study's four-structure anatomical grouping of the 36 subcortical labels.

Brainnetome Center retains rights in its resources. Its published terms specify noncommercial research use with attribution and share-alike conditions; commercial use requires a separate license. These reference tables and derived annotations are not covered by any future project-code license. Consult the original terms before reuse or redistribution:

- [Brainnetome downloads and legal agreement](https://atlas.brainnetome.org/download.html)
- Fan L, et al. The Human Brainnetome Atlas: A New Brain Atlas Based on Connectional Architecture. Cerebral Cortex. 2016;26:3508–3526. [doi:10.1093/cercor/bhw157](https://doi.org/10.1093/cercor/bhw157)

No volumetric atlas image is redistributed. Cortical labels follow the supplied official network table; subcortical labels are retained as Subcortical rather than forced into Yeo networks.

## Software

The dependencies retain their respective licenses. Model fitting uses the installed packages, not copied package source. The project authors must select any license for their own scripts separately; this release does not assign ownership or grant rights on their behalf.
