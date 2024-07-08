iri_mapper = {
    'UNKNOWN': 'http://purl.obolibrary.org/obo/NCIT_C17998',
    'FEMALE': 'http://purl.obolibrary.org/obo/NCIT_C46113',
    'MALE': 'http://purl.obolibrary.org/obo/NCIT_C46112',
    'INTERSEX': 'http://purl.obolibrary.org/obo/NCIT_C45908'
}

def get_iri(id_value: str):
    """
    """

    if 'HP:' in id_value or 'GENO:' in id_value:
        return f'http://purl.obolibrary.org/obo/{id_value.replace(':', '_')}'
    elif 'OMIM:' in id_value:
        omim_entry_nr = id_value.replace('OMIM:', '')
        return f'https://omim.org/entry/{omim_entry_nr}'
    else:
        return iri_mapper['UNKNOWN']