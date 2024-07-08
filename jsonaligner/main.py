import json
import hashlib

import jsonutil.loader as json_loader
import iriconstants as iri_constants

def get_hash(values_to_hash: list):
    """
    """
    hash_collection = hashlib.md5()
    str_values_to_hash = []

    for value_el in values_to_hash:
        str_values_to_hash.append(str(value_el))

    for value_el in str_values_to_hash:
        hash_collection.update(value_el.encode())

    #return hash_collection.hexdigest()
    return ''.join(str_values_to_hash)

class IdCollector:
    def __init__(self):
        self.counter = 0
        self.all_ids_dict = { 'id': [] }

    def create_id(self, role_index: str, id_value: str):
        self.counter += 1
        id_dict = {}

        id_dict['index'] = get_hash(['id', self.counter])

        id_dict['role'] = {}
        id_dict['role']['index'] = role_index
        id_dict['role']['parent_index'] = id_dict['index']

        id_dict['sio_has-value'] = id_value

        self.all_ids_dict['id'].append(id_dict)

class Aligner:
    def __init__(self, phenopacket_name: str, origin_phenop_data: dict):
        self.id_collector = IdCollector()

        self.origin_phenop_data = origin_phenop_data

        self.store_json_file(filename=f'phenopacket.json', dict_values=self.align_data())
        self.store_json_file(filename=f'id.json', dict_values=self.id_collector.all_ids_dict)

    def get_literal_value(self, dict_values: dict, literal_name: str):
        """
        """
        if literal_name in dict_values:
            literal_value = dict_values[literal_name]
        else:
            literal_value = None

        return literal_value

    def get_iri_value(self, label_value: str):
        """
        """
        if label_value in iri_constants.iri_mapper:
            iri_value = iri_constants.iri_mapper[label_value]
        else:
            iri_value = iri_constants.iri_mapper['UNKNOWN']
            label_value = 'UNKNOWN'
        
        return label_value, iri_value

    def add_index(self, index_dict: dict, curr_hash_path: list, parent_index_dict: dict | None = None):
        """
        """
        index_dict['index'] = get_hash(curr_hash_path)
        if parent_index_dict:
            index_dict['parent_index'] = parent_index_dict['index']
    
    def add_role_id(self, curr_dict: dict, curr_hash_path: list, id_value: str):
        """
        """
        curr_dict['role'] = {}
        next_hash_path = curr_hash_path + ['role', 1]
        curr_dict['role']['index'] = get_hash(next_hash_path)
        curr_dict['role']['parent_index'] = curr_dict['index']

        self.id_collector.create_id(role_index=curr_dict['role']['index'], id_value=id_value)

    def add_ontologyclass(self, curr_dict: dict, curr_hash_path: list, iri_value: str):
        """
        """
        hash_path = curr_hash_path + ['ontologyclass', 1]
        ont_ent = {}

        self.add_index(index_dict=ont_ent, curr_hash_path=hash_path, parent_index_dict=curr_dict)

        ont_ent['sh_IRI'] = iri_value
        
        curr_dict['ontologyclass'] = ont_ent
    
    def add_literal_output(self, curr_dict: dict, curr_hash_path: list):
        """
        """
        hash_path = curr_hash_path + ['literaloutput', 1]
        literal_ent = {}

        self.add_index(index_dict=literal_ent, curr_hash_path=hash_path, parent_index_dict=curr_dict)
        
        curr_dict['literaloutput'] = literal_ent

    def add_subject(self, curr_dict: dict, curr_hash_path: list):
        """
        """
        hash_path = curr_hash_path + ['individual', 1]
        subj_ent = {}

        self.add_index(index_dict=subj_ent, curr_hash_path=hash_path, parent_index_dict=curr_dict)
        self.add_role_id(curr_dict=subj_ent, curr_hash_path=hash_path, id_value=self.origin_phenop_data['subject']['id'])

        # Add Sex

        sub_hash_path = hash_path + ['sex', 1]
        subj_ent['sex'] = {}
        self.add_index(index_dict=subj_ent['sex'], curr_hash_path=sub_hash_path, parent_index_dict=subj_ent)
        
        sub_sub_hash_path = sub_hash_path + ['sexvalue', 1]
        subj_ent['sex']['sexvalue'] = {}
        self.add_index(index_dict=subj_ent['sex']['sexvalue'], curr_hash_path=sub_sub_hash_path, parent_index_dict=subj_ent['sex'])

        label_value = self.origin_phenop_data['subject']['sex'].upper()
        label_value, iri_value = self.get_iri_value(label_value=label_value)
        
        self.add_ontologyclass(curr_dict=subj_ent['sex'], curr_hash_path=sub_hash_path, iri_value=iri_value)

        subj_ent['sex']['rdfs_label'] = label_value

        # Add Age

        sub_hash_path = hash_path + ['age', 1]
        subj_ent['age'] = {}
        self.add_index(index_dict=subj_ent['age'], curr_hash_path=sub_hash_path, parent_index_dict=subj_ent)

        sub_sub_hash_path = sub_hash_path + ['agevalue', 1]
        subj_ent['age']['agevalue'] = {}
        self.add_index(index_dict=subj_ent['age']['agevalue'], curr_hash_path=sub_sub_hash_path, parent_index_dict=subj_ent['age'])
        self.add_literal_output(curr_dict=subj_ent['age']['agevalue'], curr_hash_path=sub_sub_hash_path)
        subj_ent['age']['agevalue']['sio_has-value'] = self.origin_phenop_data['subject']['timeAtLastEncounter']['age']['iso8601duration']

        curr_dict['individual'] = subj_ent

    def add_pheno_feats(self, curr_dict: dict, curr_hash_path: list):
        """
        """
        phenofeat_entities = []
        index_nr = 0

        for phenofeat_data in self.origin_phenop_data['phenotypicFeatures']:
            index_nr += 1
            hash_path = curr_hash_path + ['phenotypicfeature', index_nr]
            
            phenofeat_ent = {}

            self.add_index(index_dict=phenofeat_ent, curr_hash_path=hash_path, parent_index_dict=curr_dict)

            sub_hash_path = hash_path + ['phenotypicfeaturevalue', 1]
            phenofeat_ent['phenotypicfeaturevalue'] = {}
            self.add_index(index_dict=phenofeat_ent['phenotypicfeaturevalue'], curr_hash_path=sub_hash_path, parent_index_dict=phenofeat_ent)

            if 'excluded' in phenofeat_data:
                sub_hash_path = hash_path + ['excluded', 1]
                phenofeat_ent['excluded'] = {}
                self.add_index(index_dict=phenofeat_ent['excluded'], curr_hash_path=sub_hash_path, parent_index_dict=phenofeat_ent)

                sub_sub_hash_path = sub_hash_path + ['excludedvalue', 1]
                phenofeat_ent['excluded']['excludedvalue'] = {}
                self.add_index(index_dict=phenofeat_ent['excluded']['excludedvalue'], curr_hash_path=sub_sub_hash_path, parent_index_dict=phenofeat_ent['excluded'])

                self.add_literal_output(curr_dict=phenofeat_ent['excluded']['excludedvalue'], curr_hash_path=sub_sub_hash_path)
                
                phenofeat_ent['excluded']['excludedvalue']['sio_has-value'] = phenofeat_data['excluded']
            
            self.add_ontologyclass(curr_dict=phenofeat_ent, curr_hash_path=hash_path, iri_value=iri_constants.get_iri(id_value=phenofeat_data['type']['id']))

            phenofeat_ent['dct_identifier'] = phenofeat_data['type']['id']
            phenofeat_ent['rdfs_label'] = phenofeat_data['type']['label']

            phenofeat_entities.append(phenofeat_ent)

        curr_dict['phenotypicfeature'] = phenofeat_entities

    def add_progressstatus(self, curr_dict: dict, curr_hash_path: list, status_value: str):
        """
        """
        hash_path = curr_hash_path + ['progressstatus', 1]
        status_ent = {}

        self.add_index(index_dict=status_ent, curr_hash_path=hash_path, parent_index_dict=curr_dict)

        sub_hash_path = hash_path + ['progressstatusvalue', 1]
        status_ent['progressstatusvalue'] = {}

        self.add_index(index_dict=status_ent['progressstatusvalue'], curr_hash_path=sub_hash_path, parent_index_dict=status_ent)
        self.add_literal_output(curr_dict=status_ent['progressstatusvalue'], curr_hash_path=sub_hash_path)

        status_ent['progressstatusvalue']['sio_has-value'] = status_value

        curr_dict['progressstatus'] = status_ent

    def add_disease(self, curr_dict: dict, curr_hash_path: list, id_value: str, label_value: str):
        """
        """
        hash_path = curr_hash_path + ['disease', 1]
        disease_ent = {}

        self.add_index(index_dict=disease_ent, curr_hash_path=hash_path, parent_index_dict=curr_dict)

        sub_hash_path = hash_path + ['diseasevalue', 1]
        disease_ent['diseasevalue'] = {}

        self.add_index(index_dict=disease_ent['diseasevalue'], curr_hash_path=sub_hash_path, parent_index_dict=disease_ent)

        self.add_ontologyclass(curr_dict=disease_ent, curr_hash_path=hash_path, iri_value=iri_constants.get_iri(id_value))

        disease_ent['dct_identifier'] = id_value
        disease_ent['rdfs_label'] = label_value

        curr_dict['disease'] = disease_ent

    def add_acmg_class(self, curr_dict: dict, curr_hash_path: list, class_value: str | None):
        """
        """
        hash_path = curr_hash_path + ['acmgpathogenicityclass', 1]
        acmg_ent = {}

        self.add_index(index_dict=acmg_ent, curr_hash_path=hash_path, parent_index_dict=curr_dict)

        sub_hash_path = hash_path + ['acmgpathogenicityclassvalue', 1]
        acmg_ent['acmgpathogenicityclassvalue'] = {}

        self.add_index(index_dict=acmg_ent['acmgpathogenicityclassvalue'], curr_hash_path=sub_hash_path, parent_index_dict=acmg_ent)
        self.add_literal_output(curr_dict=acmg_ent['acmgpathogenicityclassvalue'], curr_hash_path=sub_hash_path)

        if class_value is None:
            class_value = 'NOT_PROVIDED'

        acmg_ent['acmgpathogenicityclassvalue']['sio_has-value'] = class_value.upper()

        curr_dict['acmgpathogenicityclass'] = acmg_ent

    def add_therapeutic_action(self, curr_dict: dict, curr_hash_path: list, class_value: str | None):
        """
        """
        hash_path = curr_hash_path + ['therapeuticactionability', 1]
        therap_ent = {}

        self.add_index(index_dict=therap_ent, curr_hash_path=hash_path, parent_index_dict=curr_dict)

        sub_hash_path = hash_path + ['therapeuticactionabilityvalue', 1]
        therap_ent['therapeuticactionabilityvalue'] = {}

        self.add_index(index_dict=therap_ent['therapeuticactionabilityvalue'], curr_hash_path=sub_hash_path, parent_index_dict=therap_ent)
        self.add_literal_output(curr_dict=therap_ent['therapeuticactionabilityvalue'], curr_hash_path=sub_hash_path)

        if class_value is None:
            class_value = 'UNKNOWN_ACTIONABILITY'

        therap_ent['therapeuticactionabilityvalue']['sio_has-value'] = class_value.upper()

        curr_dict['therapeuticactionability'] = therap_ent

    def add_gene_descr(self, curr_dict: dict, curr_hash_path: list, gene_descr_data: dict):
        """
        """
        hash_path = curr_hash_path + ['genedescriptor', 1]
        gene_descr_ent = {}

        self.add_index(index_dict=gene_descr_ent, curr_hash_path=hash_path, parent_index_dict=curr_dict)

        sub_hash_path = curr_hash_path + ['genesymbol', 1]
        gene_descr_ent['genesymbol'] = {}

        self.add_index(index_dict=gene_descr_ent['genesymbol'], curr_hash_path=sub_hash_path, parent_index_dict=gene_descr_ent)

        # TODO:
        gene_descr_ent['genesymbol']['altid'] = []

        gene_descr_ent['genesymbol']['sio_has-value'] = gene_descr_data['symbol']

        # TODO:
        gene_descr_ent['altid'] = []

        gene_descr_ent['dct_identifier'] = gene_descr_data['valueId']

        curr_dict['genedescriptor'] = gene_descr_ent

    def add_vcf_record(self, curr_dict: dict, curr_hash_path: list, vcf_record_data: dict):
        """
        """
        hash_path = curr_hash_path + ['vcfrecord', 1]
        vcf_ent = {}

        self.add_index(index_dict=vcf_ent, curr_hash_path=hash_path, parent_index_dict=curr_dict)

        attr_list = ['genomeassembly', 'chromosome', 'position', 'reference', 'alternate']
        origin_attr_list = ['genomeAssembly', 'chrom', 'pos', 'ref', 'alt']
        field_names = ['dct_identifier', 'dct_identifier', 'rdfs_label', 'rdfs_label', 'rdfs_label']

        for attr_value, origin_attr_value, field_name in zip(attr_list, origin_attr_list, field_names):
            sub_hash_path = hash_path + [attr_value, 1]
            vcf_ent[attr_value] = {}
            self.add_index(index_dict=vcf_ent[attr_value], curr_hash_path=sub_hash_path, parent_index_dict=vcf_ent)

            if origin_attr_value == 'pos':
                vcf_ent[attr_value][field_name] = int(vcf_record_data[origin_attr_value])
            else:
                vcf_ent[attr_value][field_name] = vcf_record_data[origin_attr_value]

        curr_dict['vcfrecord'] = vcf_ent

    def add_expr(self, curr_dict: dict, curr_hash_path: list, expr_data_list: list):
        """
        """
        expr_entities = []
        index_nr = 0

        for expr_data in expr_data_list:
            index_nr += 1
            hash_path = curr_hash_path + ['expression', index_nr]

            expr_ent = {}

            self.add_index(index_dict=expr_ent, curr_hash_path=hash_path, parent_index_dict=curr_dict)

            expr_ent['sh_IRI'] = iri_constants.iri_mapper['UNKNOWN']    # TODO:
            expr_ent['rdfs_label'] = expr_data['value']
            expr_ent['sio_has-value'] = expr_data['value']
            expr_ent['dct_hasVersion'] = expr_data['syntax']

            expr_entities.append(expr_ent)

        curr_dict['expression'] = expr_entities
    
    def add_mol_context(self, curr_dict: dict, curr_hash_path: list, mol_context: str):
        """
        """
        hash_path = curr_hash_path + ['moleculecontext', 1]
        mol_cont_ent = {}

        self.add_index(index_dict=mol_cont_ent, curr_hash_path=hash_path, parent_index_dict=curr_dict)

        sub_hash_path = hash_path + ['moleculecontextvalue', 1]
        mol_cont_ent['moleculecontextvalue'] = {}

        self.add_index(index_dict=mol_cont_ent['moleculecontextvalue'], curr_hash_path=sub_hash_path, parent_index_dict=mol_cont_ent)

        self.add_literal_output(curr_dict=mol_cont_ent['moleculecontextvalue'], curr_hash_path=sub_hash_path)

        mol_cont_ent['moleculecontextvalue']['sio_has-value'] = mol_context

        curr_dict['moleculecontext'] = mol_cont_ent

    def add_allelic_state(self, curr_dict: dict, curr_hash_path: list, allelic_state_data: dict):
        """
        """
        hash_path = curr_hash_path + ['allelicstate', 1]
        all_st_ent = {}

        self.add_index(index_dict=all_st_ent, curr_hash_path=hash_path, parent_index_dict=curr_dict)

        self.add_ontologyclass(curr_dict=all_st_ent, curr_hash_path=hash_path, iri_value=iri_constants.get_iri(allelic_state_data['id']))

        curr_dict['allelicstate'] = all_st_ent

    def add_var_descr(self, curr_dict: dict, curr_hash_path: list, var_descr_data: dict):
        """
        """
        hash_path = curr_hash_path + ['variationdescriptor', 1]
        var_descr_ent = {}

        self.add_index(index_dict=var_descr_ent, curr_hash_path=hash_path, parent_index_dict=curr_dict)

        self.add_role_id(curr_dict=var_descr_ent, curr_hash_path=hash_path, id_value=var_descr_data['id'])

        if 'geneContext' in var_descr_data:
            self.add_gene_descr(curr_dict=var_descr_ent, curr_hash_path=hash_path, gene_descr_data=var_descr_data['geneContext'])

        if 'vcfRecord' in var_descr_data:
            self.add_vcf_record(curr_dict=var_descr_ent, curr_hash_path=hash_path, vcf_record_data=var_descr_data['vcfRecord'])

        if 'expressions' in var_descr_data:
            self.add_expr(curr_dict=var_descr_ent, curr_hash_path=hash_path, expr_data_list=var_descr_data['expressions'])

        self.add_mol_context(curr_dict=var_descr_ent, curr_hash_path=hash_path, mol_context=var_descr_data['moleculeContext'])

        if 'allelicState' in var_descr_data:
            self.add_allelic_state(curr_dict=var_descr_ent, curr_hash_path=hash_path, allelic_state_data=var_descr_data['allelicState'])

        curr_dict['variationdescriptor'] = var_descr_ent

    def add_interpr_status(self, curr_dict: dict, curr_hash_path: list, status_value: str):
        """
        """
        hash_path = curr_hash_path + ['interpretationstatus', 1]
        interpr_status_ent = {}

        self.add_index(index_dict=interpr_status_ent, curr_hash_path=hash_path, parent_index_dict=curr_dict)

        sub_hash_path = hash_path + ['interpretationstatusvalue', 1]
        interpr_status_ent['interpretationstatusvalue'] = {}
        self.add_index(index_dict=interpr_status_ent['interpretationstatusvalue'], curr_hash_path=sub_hash_path, parent_index_dict=interpr_status_ent)
        self.add_literal_output(curr_dict=interpr_status_ent['interpretationstatusvalue'], curr_hash_path=sub_hash_path)

        interpr_status_ent['interpretationstatusvalue']['sio_has-value'] = status_value

        curr_dict['interpretationstatus'] = interpr_status_ent

    def add_genomic_interpr(self, curr_dict: dict, curr_hash_path: list, diagnosis_data: dict):
        """
        """
        genomic_interpr_entities = []
        index_nr = 0

        for genomic_interpr_data in diagnosis_data['genomicInterpretations']:
            index_nr += 1
            hash_path = curr_hash_path + ['genomicinterpretation', index_nr]

            genomic_interpr_ent = {}

            self.add_index(index_dict=genomic_interpr_ent, curr_hash_path=hash_path, parent_index_dict=curr_dict)

            if 'variantInterpretation' in genomic_interpr_data:
                var_interpr_data = genomic_interpr_data['variantInterpretation']

                sub_hash_path = hash_path + ['variantinterpretation', 1]
                genomic_interpr_ent['variantinterpretation'] = {}

                self.add_index(index_dict=genomic_interpr_ent['variantinterpretation'], curr_hash_path=sub_hash_path, parent_index_dict=genomic_interpr_ent)

                self.add_acmg_class(curr_dict=genomic_interpr_ent['variantinterpretation'], curr_hash_path=sub_hash_path, 
                                    class_value=self.get_literal_value(dict_values=var_interpr_data, literal_name='acmgPathogenicityClassification'))

                self.add_therapeutic_action(curr_dict=genomic_interpr_ent['variantinterpretation'], curr_hash_path=sub_hash_path, 
                                            class_value=self.get_literal_value(dict_values=var_interpr_data, literal_name='therapeuticActionability'))

                self.add_var_descr(curr_dict=genomic_interpr_ent['variantinterpretation'], curr_hash_path=sub_hash_path, var_descr_data=var_interpr_data['variationDescriptor'])

            # TODO: if genedescriptor in genomic interpretation

            if genomic_interpr_data['subjectOrBiosampleId'] == self.origin_phenop_data['subject']['id']:
                self.add_subject(curr_dict=genomic_interpr_ent, curr_hash_path=hash_path)
            # TODO: if id referring to biosample 

            self.add_interpr_status(curr_dict=genomic_interpr_ent, curr_hash_path=hash_path, status_value=genomic_interpr_data['interpretationStatus'])

            genomic_interpr_entities.append(genomic_interpr_ent)

        curr_dict['genomicinterpretation'] = genomic_interpr_entities

    def add_diagnosis(self, curr_dict: dict, curr_hash_path: list, interpr_data: dict, index_nr: int):
        """
        """
        if 'diagnosis' in interpr_data:
            hash_path = curr_hash_path + ['diagnosis', 1]
            diagnosis_ent = {}

            self.add_index(index_dict=diagnosis_ent, curr_hash_path=hash_path, parent_index_dict=curr_dict)

            sub_hash_path = hash_path + ['diagnosisvalue', 1]
            diagnosis_ent['diagnosisvalue'] = {}

            self.add_index(index_dict=diagnosis_ent['diagnosisvalue'], curr_hash_path=sub_hash_path, parent_index_dict=diagnosis_ent)

            self.add_disease(curr_dict=diagnosis_ent, curr_hash_path=hash_path, 
                             id_value=interpr_data['diagnosis']['disease']['id'],
                             label_value=interpr_data['diagnosis']['disease']['label'])
            
            self.add_genomic_interpr(curr_dict=diagnosis_ent, curr_hash_path=hash_path, diagnosis_data=interpr_data['diagnosis'])

            # TODO: what kinds of IRIs and how to acquire them
            self.add_ontologyclass(curr_dict=diagnosis_ent, curr_hash_path=hash_path, iri_value=iri_constants.iri_mapper['UNKNOWN'])
            
            diagnosis_ent['dct_identifier'] = f'diagnosis {index_nr}'
            diagnosis_ent['rdfs_label'] = f'{interpr_data['diagnosis']['disease']['label']} diagnosis'

            curr_dict['diagnosis'] = diagnosis_ent

    def add_interpr(self, curr_dict: dict, curr_hash_path: list):
        """
        """
        interpr_entities = []
        index_nr = 0

        for interpr_data in self.origin_phenop_data['interpretations']:
            index_nr += 1
            hash_path = curr_hash_path + ['interpretation', index_nr]

            interpr_ent = {}

            self.add_index(index_dict=interpr_ent, curr_hash_path=hash_path, parent_index_dict=curr_dict)

            self.add_role_id(curr_dict=interpr_ent, curr_hash_path=hash_path, id_value=f'{interpr_data['id']}_{index_nr}')

            self.add_progressstatus(curr_dict=interpr_ent, curr_hash_path=hash_path, status_value=interpr_data['progressStatus'])
            self.add_diagnosis(curr_dict=interpr_ent, curr_hash_path=hash_path, interpr_data=interpr_data, index_nr=index_nr)

            interpr_entities.append(interpr_ent)

        curr_dict['interpretation'] = interpr_entities

    def add_metadata_attr(self, curr_dict: dict, curr_hash_path: list, metadata_data: dict, attr_name: str, origin_attr: str):
        """
        """
        hash_path = curr_hash_path + [attr_name, 1]
        attr_ent = {}

        self.add_index(index_dict=attr_ent, curr_hash_path=hash_path, parent_index_dict=curr_dict)

        sub_hash_path = hash_path + [f'{attr_name}value', 1]
        attr_ent[f'{attr_name}value'] = {}

        self.add_index(index_dict=attr_ent[f'{attr_name}value'], curr_hash_path=sub_hash_path, parent_index_dict=attr_ent)
        self.add_literal_output(curr_dict=attr_ent[f'{attr_name}value'], curr_hash_path=sub_hash_path)

        attr_ent[f'{attr_name}value']['sio_has-value'] = metadata_data[origin_attr]

        curr_dict[attr_name] = attr_ent

    def add_metadata(self, curr_dict: dict, curr_hash_path: list):
        """
        """
        hash_path = curr_hash_path + ['metadata', 1]
        metadata_ent = {}

        self.add_index(index_dict=metadata_ent, curr_hash_path=hash_path, parent_index_dict=curr_dict)

        attr_list = ['created', 'createdby', 'version']
        origin_attr_list = ['created', 'createdBy', 'phenopacketSchemaVersion']
        for attr_name, origin_attr in zip(attr_list, origin_attr_list):
            self.add_metadata_attr(curr_dict=metadata_ent, curr_hash_path=hash_path, metadata_data=self.origin_phenop_data['metaData'], attr_name=attr_name, origin_attr=origin_attr)

        curr_dict['metadata'] = metadata_ent

    def align_data(self):
        """
        """
        phenop_data = {
            'phenopacket': []
        }

        hash_path = ['phenopacket', 1]
        phenop_ent = {}

        self.add_index(index_dict=phenop_ent, curr_hash_path=hash_path)
        self.add_role_id(curr_dict=phenop_ent, curr_hash_path=hash_path, id_value=self.origin_phenop_data['id'])

        self.add_subject(curr_dict=phenop_ent, curr_hash_path=hash_path)

        self.add_pheno_feats(curr_dict=phenop_ent, curr_hash_path=hash_path)
        self.add_interpr(curr_dict=phenop_ent, curr_hash_path=hash_path)

        # TODO: missing diseases block?

        self.add_metadata(curr_dict=phenop_ent, curr_hash_path=hash_path)

        phenop_data['phenopacket'].append(phenop_ent)

        return phenop_data

    def store_json_file(self, filename: str, dict_values: dict):
        json_loader.store_json_file(filename, dict_values)

if __name__ == "__main__":
    all_phenopacket_json_filenames = json_loader.get_all_json_filenames()
    for json_filename in all_phenopacket_json_filenames:
        phenopacket_data = json_loader.load_hamlet_json_file(json_filename)
        json_aligner = Aligner(phenopacket_name=json_filename.replace('.json', ''),
                               origin_phenop_data=phenopacket_data)

