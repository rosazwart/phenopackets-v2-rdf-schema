# RDF Schemas for Phenopackets Version 2

In this repository, SHACL is used to specify the structure of RDF datasets complying to [GA4GH Phenopackets Version 2](https://phenopacket-schema.readthedocs.io/en/latest/) and interoperable with the [CARE-SM semantic model](https://github.com/CARE-SM/CARE-Semantic-Model/wiki). The SHACL files are based on the ShEx (Shape Expression) files representing this RDFied phenopackets version 2 data model found [here](https://github.com/LUMC-BioSemantics/phenopackets-rdf-schema/tree/v2/shex).

To represent common predicates, terms from the ontology [Semanticscience Integrated Ontology](http://sio.semanticscience.org/) (SIO) are used. For some common predicates and those originating from biomedical domain knowledge other ontologies have been added such as the [NCI Thesaurus](https://obofoundry.org/ontology/ncit), [Human Phenotype Ontology](https://obofoundry.org/ontology/hp.html) and [Genotype Ontology](https://obofoundry.org/ontology/geno.html). These ontologies are interoperable given the [Open Biological and Biomedical Ontology Foundry](https://obofoundry.org/) (OBO).

For representing predicates related to metadata, the terms defined in the [DCMI Metadata Terms](https://www.dublincore.org/specifications/dublin-core/dcmi-terms/) (dcterms) maintained by [Dublin Core Metadata Initiative](https://www.dublincore.org/about/) are used.

# Workflow of generating RDF data from any given data in another format

To avoid manually converting JSON data to an RDF knowledge graph complying to the GA4GH Phenopackets schema from scratch, a workflow has been set up that facilitates this action as shown below. The workflow consists of multiple steps that will be discussed in the next subsections.

![Worfklow](https://github.com/rosazwart/phenopackets-v2-rdf-schema/blob/main/overviewworkflow.jpg)

## 1. Modelling Phenopackets Schema

For modelling the phenopackets schema, Shapes Constraint Language (SHACL) files have been written that describe how a dataset needs to be structured. To keep the constraints organized, each file stores the shape of a single class or the shapes of similar classes. Shapes are the rules to which the instances of a class need to conform to. 

## 2. Generating YARRRML and example JSON file(s) given SHACL files

A script has been developed that generates a YARRRML file containing the maximum requirements of the data structure following the Phenopackets schema. The generator script can be found in folder [`shacl2yarrrrml`](https://github.com/rosazwart/phenopackets-v2-rdf-schema/tree/main/shacl2yarrrml). Along the generation of a YARRRML file, one or multiple (multiple "root" nodeshapes defined in SHACL results in multiple JSON files) JSON files are created that show how the data that is to be converted should look like. 

## 3. Aligning data to JSON file

The JSON file(s) that show(s) the structure that the YARRRML file will accept and convert correctly to RDF. This structure is mainly built upon indexes that link one data field to another. This allows for robustness of the RDF conversion whatever SHACL structure has been given. Each datafield in the generated JSON file(s) contains a comment to show the user whether the datafield is needed in order to comply to the data model represented by the SHACL files.

In folder [`jsonaligner`](https://github.com/rosazwart/phenopackets-v2-rdf-schema/tree/main/jsonaligner) a script can be found that aligns JSON data following the phenopacket version 2 structure to the JSON data structure that is compatible with the generated YARRRML.

## 4. RML Mapping

A browser-based IDE [Matey](https://rml.io/yarrrml/matey/) can be used to generate RDF triples given your data and YARRRML rules. To enable the automation of this process, in folder [`yarrrml2rdf`](https://github.com/rosazwart/phenopackets-v2-rdf-schema/tree/main/yarrrml2rdf) the script is stored that visits the browser-based IDE, enters the input data files as well as the generated YARRRML rules to then generate the RDF triples that are stored in a Turtle file.

## 5. RDF Validation

To ensure that the resulting RDF knowledge graph still complies to the Phenopackets data model, a script has been written that validates a given RDF file against the SHACL files containing all the class shapes. When the RDF data does not conform to the intended data structure, it will output a report on which instances throw errors. The validator script can be found in folder [`rdfvalidator`](https://github.com/rosazwart/phenopackets-v2-rdf-schema/tree/main/rdfvalidator).

# Used Libraries

Functionalities in the scripts included throughout the workflow are used from the open source Python library [RDFLib](https://rdflib.readthedocs.io/en/stable/index.html) and the additional module [pySHACL](https://github.com/RDFLib/pySHACL). Also, for writing the YARRRML template the package [ruamel.yaml](https://yaml.readthedocs.io/en/latest/) is utilized.

# Used Phenopacket Data
In folder [`example-hamlet`](https://github.com/rosazwart/phenopackets-v2-rdf-schema/tree/main/example-hamlet) mock HAMLET analysis data has been converted to an RDF dataset.

In folder [`example-phenopacket`](https://github.com/rosazwart/phenopackets-v2-rdf-schema/tree/main/example-phenopacket) a selection of phenopacket instances has been extracted from the [Monarch Initiative phenopacket store](https://github.com/monarch-initiative/phenopacket-store/tree/main/notebooks/NRAS/phenopackets) and converted to RDF datasets.
