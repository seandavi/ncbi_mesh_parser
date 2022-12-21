from xml.etree import cElementTree as elemtree
from datetime import date
import pydantic

"""
Use this to parse XML from MeSH (Medical Subject Headings). More information 
on the format at: http://www.ncbi.nlm.nih.gov/mesh

End users will primarily want to call the `parse_mesh` function and do something
with the output.
"""

from typing import Generator, Any


def date_from_mesh_xml(xml_elem: elemtree.Element) -> date:
    year: str = xml_elem.find("./Year").text  # type: ignore
    month: str = xml_elem.find("./Month").text  # type: ignore
    day: str = xml_elem.find("./Day").text  # type: ignore
    return date(int(year), int(month), int(day))


class PharmacologicalAction(pydantic.BaseModel):
    """A pharmacological action, denoting the effects of a MeSH descriptor."""

    descriptor_ui: str = str(None)

    @classmethod
    def from_xml_elem(cls, elem):
        rec = cls()
        rec.descriptor_ui = elem.find("./DescriptorReferredTo/DescriptorUI").text
        return rec


class SlotsToNoneMixin(object):
    def __init__(self, **kwargs):
        for attr in self.__slots__:
            setattr(self, attr, kwargs.get(attr, None))

    def __repr__(self):
        attrib_repr = ", ".join(
            "%s=%r" % (attr, getattr(self, attr)) for attr in self.__slots__
        )
        return self.__class__.__name__ + "(" + attrib_repr + ")"


class Term(pydantic.BaseModel):
    """A term from within a MeSH concept."""

    name: str = str(None)
    ui: str = str(None)
    string: str = str(None)
    is_concept_preferred: bool = False
    is_record_preferred: bool = False
    is_permuted: bool = False
    lexical_tag: str = str(None)
    date_created: date = None
    thesaurus_list: list = []

    @classmethod
    def from_xml_elem(cls, elem):
        term = cls()
        term.is_concept_preferred = elem.get("ConceptPreferredYN", None) == "Y"
        term.is_record_preferred = elem.get("RecordPreferredYN", None) == "Y"
        term.is_permuted = elem.get("IsPermutedTermYN", None) == "Y"
        term.lexical_tag = elem.get("LexicalTag")
        for child_elem in elem:
            if child_elem.tag == "TermUI":
                term.ui = child_elem.text
            elif child_elem.tag == "String":
                term.name = child_elem.text
            elif child_elem.tag == "DateCreated":
                term.date_created = date_from_mesh_xml(child_elem)
            elif child_elem.tag == "ThesaurusIDlist":
                term.thesaurus_list = [th_elem.text for th_elem in child_elem]
        return term


class SemanticType(pydantic.BaseModel):
    ui: str = str(None)
    name: str = str(None)

    @classmethod
    def from_xml_elem(cls, elem):
        sem_type = cls()
        for child_elem in elem:
            if child_elem.tag == "SemanticTypeUI":
                sem_type.ui = child_elem.text
            elif child_elem.tag == "SemanticTypeName":
                sem_type.name = child_elem.text


class Concept(pydantic.BaseModel):
    """A concept within a MeSH Descriptor."""

    ui: str = str(None)
    name: str = str(None)
    is_preferred: bool = False
    umls_ui: str = str(None)
    casn1_name: str = str(None)
    registry_num: str = str(None)
    scope_note: str = str(None)
    sem_types: list[SemanticType] = []
    terms: list[Term] = []

    @classmethod
    def from_xml_elem(cls, elem):
        concept = cls()
        concept.is_preferred = elem.get("PreferredConceptYN", None) == "Y"
        for child_elem in elem:
            if child_elem.tag == "ConceptUI":
                concept.ui = child_elem.text
            elif child_elem.tag == "ConceptName":
                concept.name = child_elem.find("./String").text
            elif child_elem.tag == "ConceptUMLSUI":
                concept.umls_ui
            elif child_elem.tag == "CASN1Name":
                concept.casn1_name = child_elem.text
            elif child_elem.tag == "RegistryNumber":
                concept.registry_num = child_elem.text
            elif child_elem.tag == "ScopeNote":
                concept.scope_note = child_elem.text
            elif child_elem.tag == "SemanticTypeList":
                concept.sem_types = [
                    SemanticType.from_xml_elem(st_elem)
                    for st_elem in child_elem.findall("SemanticType")
                ]
            elif child_elem.tag == "TermList":
                concept.terms = [
                    Term.from_xml_elem(term_elem)
                    for term_elem in child_elem.findall("Term")
                ]
        return concept


def ancestor_tree_numbers_from_trees(tree_numbers: list[str]) -> list[dict[str, str]]:
    ancestors = []
    for tree in tree_numbers:
        tot_depth = len(tree.split("."))
        for i in range(1, len(tree.split(".")) + 1):
            ancestors.append(
                {"distance": tot_depth - i, "tree": ".".join(tree.split(".")[0:i])}
            )
    ancestors = list(map(dict, set(tuple(sorted(sub.items())) for sub in ancestors)))
    return ancestors


class DescriptorRecord(pydantic.BaseModel):
    "A MeSH Descriptor Record." ""

    ui: str = str(None)
    name: str = str(None)
    date_created: date = None
    date_revised: date = None
    pharm_actions: list = []
    tree_numbers: list = []
    ancestor_tree_numbers: list = []
    concepts: list[Concept] = []

    @classmethod
    def from_xml_elem(cls, elem):
        rec = cls()
        for child_elem in elem:
            if child_elem.tag == "DescriptorUI":
                rec.ui = child_elem.text
            elif child_elem.tag == "DescriptorName":
                rec.name = child_elem.find("./String").text
            elif child_elem.tag == "DateCreated":
                rec.date_created = date_from_mesh_xml(child_elem)
            elif child_elem.tag == "DateRevised":
                rec.date_revised = date_from_mesh_xml(child_elem)
            elif child_elem.tag == "TreeNumberList":
                rec.tree_numbers = [
                    tn_elem.text for tn_elem in child_elem.findall("TreeNumber")
                ]
                rec.ancestor_tree_numbers = ancestor_tree_numbers_from_trees(
                    rec.tree_numbers
                )
            elif child_elem.tag == "ConceptList":
                rec.concepts = [
                    Concept.from_xml_elem(c_elem)
                    for c_elem in child_elem.findall("Concept")
                ]
            elif child_elem.tag == "PharmacologicalActionList":
                rec.pharm_actions = [
                    PharmacologicalAction.from_xml_elem(pa_elem)
                    for pa_elem in child_elem.findall("PharmacologicalAction")
                ]
        return rec


def parse_mesh(filename: str) -> Generator[DescriptorRecord, None, None]:
    """Parse a mesh file, successively generating
    `DescriptorRecord` instance for subsequent processing.

    >>> for rec in parse_mesh("data/desc2019.xml"):
    ...     print(rec.json(indent=2))
    """
    for _evt, elem in elemtree.iterparse(filename):
        if elem.tag == "DescriptorRecord":
            yield DescriptorRecord.from_xml_elem(elem)
