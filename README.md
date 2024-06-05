# RDF Schemas for Phenopackets Version 2

In this repository, SHACL is used to specify the structure of RDF datasets complying to [GA4GH Phenopackets Version 2](https://phenopacket-schema.readthedocs.io/en/latest/). This schema also incorporates the semantic structure of [GA4GH Variation Representation Specification](https://vrs.ga4gh.org/en/stable/index.html) (VRS) for representing genetic variation information.  

To represent common predicates, terms from the ontology [Semanticscience Integrated Ontology](http://sio.semanticscience.org/) (SIO) are used. For some common predicates and those originating from biomedical domain knowledge other ontologies have been added such as the [NCI Thesaurus](https://obofoundry.org/ontology/ncit), [Human Phenotype Ontology](https://obofoundry.org/ontology/hp.html) and [Genotype Ontology](https://obofoundry.org/ontology/geno.html). These ontologies are interoperable given the [Open Biological and Biomedical Ontology Foundry](https://obofoundry.org/) (OBO).

For representing predicates related to metadata, the terms defined in the [DCMI Metadata Terms](https://www.dublincore.org/specifications/dublin-core/dcmi-terms/) (dcterms) maintained by [Dublin Core Metadata Initiative](https://www.dublincore.org/about/) are used.

In the visualization below, the RDF shape of the upper level model element is shown. The RDF shapes for the other lower level blocks in the phenopackets version 2 model are shown [in this folder](https://github.com/rosazwart/phenopackets-v2-rdf-schema/tree/main/model).

![Phenopacketschema](https://github.com/rosazwart/phenopackets-v2-rdf-schema/blob/main/model/Phenopacket_V2_Phenopacket.jpg)

# RDF Example

For an impression of how an RDF dataset is compiled that adapts the GA4GH Phenopacket data model structure, a simple example has been provided in [this directory](https://github.com/rosazwart/phenopackets-v2-rdf-schema/tree/main/example-rdf). The RDF data is represented in Terse RDF Triple Language (TTL, turtle) and follows the minimum data requirements of a phenopacket.

The RDF dataset is also visualized in a graph shown [here](https://github.com/rosazwart/phenopackets-v2-rdf-schema/blob/main/example-rdf/phenopacketExampleGraph.png). The image has been generated using the [web service](https://www.ldf.fi/service/rdf-grapher) provided by Linked Data Finland enabling parsing of RDF data to a graph visualization.

# Workflow of Generating RDF Data from any given JSON File

To avoid manually converting JSON data to an RDF knowledge graph complying to the GA4GH Phenopackets schema from scratch, a workflow has been set up that facilitates this action as shown below. The workflow consists of multiple steps that will be discussed in the next subsections.

![Worfklow](https://github.com/rosazwart/phenopackets-v2-rdf-schema/blob/main/workflowJSONtoRDF.jpg)

## 1. Modelling Phenopackets Schema

For modelling the phenopackets schema, Shapes Constraint Language (SHACL) files have been written that describe how a dataset needs to be structured. To keep the constraints organized, each file stores the shape of a single class or the shapes of similar classes. Shapes are the rules to which the instances of a class need to conform to. 

## 2. Generating YARRRML Template given SHACL Files

A script has been developed that generates a YARRRML template containing the maximum requirements of the data structure following the Phenopackets schema. Comments in the template inform the user which classes or properties of classes need to be present or not. The generator script can be found [here](https://github.com/rosazwart/phenopackets-v2-rdf-schema/tree/main/shacl2yarrrml).

## 3. Filling in the YARRRML Template

Due to [YARRRML](https://rml.io/yarrrml/) being a user-friendly representation for RML rules, users can easily fill in the template given the JSON data that needs to be converted to RDF. Given the comments provided in the template the user can see which classes or properties need to be included and which can be ommitted in order to meet the minimum requirements while using as much data from their JSON file. YARRRML does have its limitations when it comes to the iterator that can be defined in order to map the JSON data fields to the correct RDF entities. The user needs to ensure that the JSON data schema allows the mapping with YARRRML.

## 4. RML Mapping

There exist multiple ways to map the given JSON data to the correctly structured knowledge graph with the filled in YARRRML. One option is installing the [yarrrml-parser](https://github.com/rmlio/yarrrml-parser) that translates YARRRML to the RML format. Next, use [RMLMapper](https://github.com/RMLio/rmlmapper-java) to generate the RDF knowledge graph. The second and easier option is using the browser-based IDE [Matey](https://rml.io/yarrrml/matey/) that contains the functionalities of loading data sources, writing YARRRML rules and generating RDF triples.

## 5. RDF Validation

To ensure that the resulting RDF knowledge graph still complies to the Phenopackets data model, a script has been written that validates a given RDF file against the SHACL files containing all the class shapes. When the RDF data does not conform to the intended data structure, it will output a report on which instances throw errors. The validator script can be found [here](https://github.com/rosazwart/phenopackets-v2-rdf-schema/tree/main/rdfvalidator).

# Used Libraries

Functionalities in the scripts included throughout the workflow are used from the open source Python library [RDFLib](https://rdflib.readthedocs.io/en/stable/index.html) and the additional module [pySHACL](https://github.com/RDFLib/pySHACL). Also, for writing the YARRRML template the package [ruamel.yaml](https://yaml.readthedocs.io/en/latest/) is utilized.
