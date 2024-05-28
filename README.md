# RDF Schemas for Phenopackets Version 2

In this repository, SHACL is used to specify the structure of RDF datasets complying to [GA4GH Phenopackets Version 2](https://phenopacket-schema.readthedocs.io/en/latest/). This schema also incorporates the semantic structure of [GA4GH Variation Representation Specification](https://vrs.ga4gh.org/en/stable/index.html) (VRS) for representing genetic variation information.  

To represent common predicates, terms from the ontology [Semanticscience Integrated Ontology](http://sio.semanticscience.org/) (SIO) are used. For some common predicates and those originating from biomedical domain knowledge other ontologies have been added such as the [NCI Thesaurus](https://obofoundry.org/ontology/ncit), [Human Phenotype Ontology](https://obofoundry.org/ontology/hp.html) and [Genotype Ontology](https://obofoundry.org/ontology/geno.html). These ontologies are interoperable given the [Open Biological and Biomedical Ontology Foundry](https://obofoundry.org/) (OBO).

For representing predicates related to metadata, the terms defined in the [DCMI Metadata Terms](https://www.dublincore.org/specifications/dublin-core/dcmi-terms/) (dcterms) maintained by [Dublin Core Metadata Initiative](https://www.dublincore.org/about/) are used.

In the next visualizations, the RDF shapes are depicted for each block in the phenopackets version 2 model.

## Phenopacket

![Phenopacketschema](https://github.com/rosazwart/phenopackets-v2-rdf-schema/blob/main/model/Phenopacket_V2_Phenopacket.jpg)

## Individual

![Individualschema](https://github.com/rosazwart/phenopackets-v2-rdf-schema/blob/main/model/Phenopacket_V2_Individual.jpg)

## PhenotypicFeature

![PhenotypicFeatureschema](https://github.com/rosazwart/phenopackets-v2-rdf-schema/blob/main/model/Phenopacket_V2_PhenotypicFeature.jpg)

## Measurement

![Measurementschema](https://github.com/rosazwart/phenopackets-v2-rdf-schema/blob/main/model/Phenopacket_V2_Measurement.jpg)

## Biosample

![Biosampleschema](https://github.com/rosazwart/phenopackets-v2-rdf-schema/blob/main/model/Phenopacket_V2_Biosample.jpg)

## Interpretation

![Interpretationschema](https://github.com/rosazwart/phenopackets-v2-rdf-schema/blob/main/model/Phenopacket_V2_Interpretation.jpg)

## Disease

![Diseaseschema](https://github.com/rosazwart/phenopackets-v2-rdf-schema/blob/main/model/Phenopacket_V2_Disease.jpg)

## MedicalAction

![MedicalActionschema](https://github.com/rosazwart/phenopackets-v2-rdf-schema/blob/main/model/Phenopacket_V2_MedicalAction.jpg)

## File and Metadata

![FileMetadataschema](https://github.com/rosazwart/phenopackets-v2-rdf-schema/blob/main/model/Phenopacket_V2_File_Metadata.jpg)

## (GA4GH VRS) Variation

The visualization of the RDF shapes for each block of the GA4GH VRS is shown below.

![Variationschema](https://github.com/rosazwart/phenopackets-v2-rdf-schema/blob/main/model/Phenopacket_V2_Variation.jpg)

# RDF Example

For an impression of how an RDF dataset is compiled that adapts the GA4GH Phenopacket data model structure, an example has been provided in [this directory](https://github.com/rosazwart/phenopackets-v2-rdf-schema/tree/main/example-rdf). The RDF data is represented in Terse RDF Triple Language (TTL, turtle) and follows the minimum data requirements of a phenopacket.

The RDF dataset is also visualized in a graph shown [here](https://github.com/rosazwart/phenopackets-v2-rdf-schema/blob/main/example-rdf/phenopacketExampleGraph.png). The image has been generated using the [web service](https://www.ldf.fi/service/rdf-grapher) provided by Linked Data Finland enabling parsing of RDF data to a graph visualization.

# RDF Validation

To validate that an RDF dataset complies to the GA4GH Phenopacket data model such as the [given phenopacket example](https://github.com/rosazwart/phenopackets-v2-rdf-schema/blob/main/example-rdf/phenopacketExample.ttl), a script is provided that can be found in [this directory](https://github.com/rosazwart/phenopackets-v2-rdf-schema/blob/main/validator/main.py). Functionalities are taken from the open source Python library [RDFLib](https://rdflib.readthedocs.io/en/stable/index.html) and the additional module [pySHACL](https://github.com/RDFLib/pySHACL).
