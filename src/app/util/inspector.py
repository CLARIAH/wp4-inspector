from app.config import ENDPOINT_URL
import networkx as nx
import requests
import json
from networkx.readwrite import json_graph


PREFIXES = """
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX np: <http://www.nanopub.org/nschema#>
    PREFIX prov: <http://www.w3.org/ns/prov#>
    PREFIX foaf: <http://xmlns.com/foaf/0.1/>
    PREFIX example: <http://www.example.org/rdf#>
    PREFIX qb: <http://purl.org/linked-data/cube#>
"""

dimensions_query = PREFIXES + """
    SELECT DISTINCT ?source_dataset ?source_dimension WHERE {
      {
        # ?source_np np:hasAssertion ?source_assertion .
        # GRAPH ?source_assertion {
    	   ?source_dataset qb:structure/qb:component/(qb:dimension|qb:measure) ?source_dimension .
           ?source_dataset a qb:DataSet .
        # }
      }
      UNION
      {
        ?source_dimension a qb:DimensionProperty .
      }
      UNION
      {
        ?source_dimension a qb:MeasureProperty .
      }
      UNION
      {
        ?source_dimension a qb:CodedProperty .
      }
    }
"""

provenance_query = PREFIXES + """
    SELECT DISTINCT ?source_dataset ?person ?label ?image  WHERE {
		?source_np np:hasProvenance ?source_provenance .
        ?source_np np:hasAssertion ?source_assertion .
        GRAPH ?source_assertion {
            ?source_dataset a qb:DataSet .
        }
        GRAPH ?source_provenance {
         	?source_assertion prov:wasAttributedTo ?p .
        }
        ?p a foaf:Person .
        ?p foaf:name ?label .
        OPTIONAL { ?p foaf:depiction ?image . }

        BIND(IF(bound(?p), ?p, example:datalegend) as ?person)
    }
"""

mappings_query = """
    SELECT DISTINCT ?source_dimension ?target_dimension WHERE {
      [] qb:dimension|qb:measure ?source_dimension .

      { ?source_dimension rdfs:subPropertyOf ?target_dimension . }
      UNION
      { ?target_dimension rdfs:subPropertyOf ?source_dimension . }
      UNION
      {
        ?source_dimension rdfs:subPropertyOf ?shared_parent_dimension .
        ?target_dimension rdfs:subPropertyOf ?shared_parent_dimension .
        FILTER(?source_dimension != ?target_dimension)
      }
    }
"""


overview_datasets_query = """
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX qb: <http://purl.org/linked-data/cube#>
PREFIX np: <http://www.nanopub.org/nschema#>
PREFIX prov: <http://www.w3.org/ns/prov#>
SELECT DISTINCT ?assertion ?assertion_time ?person ?dataset ?source WHERE {

  GRAPH ?assertion {
  	?dataset a qb:DataSet .
  }

  OPTIONAL {
    ?np np:hasAssertion ?assertion .
    ?np np:hasProvenance ?provenance .
    GRAPH ?provenance {
      ?assertion prov:wasAttributedTo ?person .
      ?assertion prov:wasDerivedFrom ?source .
      ?assertion prov:generatedAtTime ?assertion_time .
    }
  }
} ORDER BY ?person
"""

overview_datasets_and_dimensions_query = """
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX qb: <http://purl.org/linked-data/cube#>
PREFIX np: <http://www.nanopub.org/nschema#>
PREFIX prov: <http://www.w3.org/ns/prov#>
SELECT DISTINCT ?dataset ?assertion ?assertion_time ?dimension ?dimension_type ?mapped_dimension WHERE {
  GRAPH ?assertion {
  	?dataset a qb:DataSet .
  	?dataset qb:structure/qb:component/(qb:dimension|qb:measure) ?dimension .
    OPTIONAL { ?dimension a ?dimension_type . }
    OPTIONAL {?dimension rdfs:subPropertyOf ?mapped_dimension}
  }


      ?np np:hasAssertion ?assertion .
      ?np np:hasProvenance ?provenance .
      GRAPH ?provenance {
      	?assertion prov:generatedAtTime ?assertion_time .
      }
  # BIND(IF(bound(?at),?at,"unknown") AS ?assertion_time ).
} GROUP BY ?dataset ORDER BY ?assertion_time
"""



# edges_query = """
#     PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
#     PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
#     PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
#     PREFIX dct: <http://purl.org/dc/terms/>
#     PREFIX prov: <http://www.w3.org/ns/prov#>
#     PREFIX qb: <http://purl.org/linked-data/cube#>
#     PREFIX foaf: <http://xmlns.com/foaf/0.1/>
#
#
#     SELECT DISTINCT ?dataset ?dimension ?person ?name ?image ?dataset2 ?dimension2 ?person2 ?name2 ?image2 WHERE {
#         {
#             GRAPH ?provenance_graph {
#                 ?assertion_graph prov:wasAttributedTo ?person .
#             }
#             ?person foaf:depiction ?image .
#             ?person foaf:name ?name .
#             GRAPH ?assertion_graph {
#                 ?dataset qb:structure/qb:component/qb:dimension ?dimension .
#                 { ?dimension rdfs:subPropertyOf ?dimension2 . }
#                 UNION
#                 { ?dimension2 rdfs:subPropertyOf ?dimension . }
#                 UNION
#                 {
#                     ?dimension rdfs:subPropertyOf ?joint_parent .
#                 }
#             }
#             OPTIONAL {

#                 GRAPH ?assertion_graph2 {
#                         {
#                             ?dataset2 qb:structure/qb:component/qb:dimension ?dimension2 .
#                         }
#                         UNION
#                         {
#                             ?dimension2 rdfs:label [] .
#                         }
#                         UNION
#                         {
#                             ?dimension2 rdfs:subPropertyOf ?joint_parent .
#                         }
#                 }
#                 GRAPH ?provenance_graph2 {
#                       ?assertion_graph2 prov:wasAttributedTo ?person2
#                 }
#                 ?person2 foaf:name ?name2 .
#                 ?person2 foaf:depiction ?image2 .
#                 FILTER(?assertion_graph != ?assertion_graph2)
#             }
# } UNION {
#     GRAPH ?provenance_graph {
#         ?assertion_graph prov:wasAttributedTo ?person .
#     }
#     ?person foaf:depiction ?image .
#     ?person foaf:name ?name .
#     GRAPH ?assertion_graph {
#         ?dataset qb:structure/qb:component/qb:dimension ?dimension .
#     }
# }
#     }
# """

# edges_query = """
#     PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
#                 PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
#                 PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
#                 PREFIX dct: <http://purl.org/dc/terms/>
#                 PREFIX prov: <http://www.w3.org/ns/prov#>
#                 PREFIX qb: <http://purl.org/linked-data/cube#>
#
#     SELECT ?dataset ?structure ?component ?dimension ?codelist ?code ?dimension2 ?codelist2 ?code2 WHERE {
#             ?dataset qb:structure ?structure .
#             ?structure qb:component ?component .
#             ?component qb:dimension ?dimension .
#             ?dimension qb:codeList ?codelist .
#             {?codelist skos:member ?code . }
#             UNION
#             {?code skos:inScheme ?codelist .}
#             { ?dimension rdfs:subPropertyOf ?dimension2 . }
#             UNION
#             { ?dimension2 rdfs:subPropertyOf ?dimension .}
#             { ?codelist prov:wasDerivedFrom ?codelist2 .}
#             UNION
#             { ?codelist2 prov:wasDerivedFrom ?codelist .}
#             { ?code skos:exactMatch ?code2 . }
#             UNION
#             { ?code2 skos:exactMatch ?code . }
#     }
#
# """

# query_all = """
#     PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
#                 PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
#                 PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
#                 PREFIX dct: <http://purl.org/dc/terms/>
#                 PREFIX prov: <http://www.w3.org/ns/prov#>
#                 PREFIX qb: <http://purl.org/linked-data/cube#>
#
#     SELECT ?dataset ?structure ?component ?dimension ?codelist ?code ?dimension2 ?codelist2 ?code2 WHERE {
#         ?dataset qb:structure ?structure .
#         ?structure qb:component ?component .
#         ?component qb:dimension ?dimension .
#         ?dimension qb:codeList ?codelist .
#         {?codelist skos:member ?code . } UNION {?code skos:inScheme ?codelist .}
#         OPTIONAL {?dimension rdfs:subPropertyOf ?dimension2 }
#         OPTIONAL {?codelist prov:wasDerivedFrom ?codelist2 }
#         OPTIONAL {?code skos:exactMatch ?code2 }
#     }
#
# """


def query(q):
    # This is old style, but leaving for backwards compatibility with earlier versions of Stardog
    QUERY_HEADERS = {'Accept': 'application/sparql-results+json'}

    result = requests.get(ENDPOINT_URL,
                          params={'query': q},
                          headers=QUERY_HEADERS)

    results = json.loads(result.content)['results']['bindings']

    return results


def build_graph(dimensions, provenance, mappings):
    g = nx.DiGraph()

    for r in dimensions:
        if 'source_dataset' not in r:
            if r['source_dimension'] not in g.nodes():
                g.add_node(r['source_dimension'], {'name': r['source_dimension'], 'type': 'dimension', 'origin': 'external'})
        else:
            g.add_node(r['source_dimension'],
                       {'name': r['source_dimension'], 'type': 'dimension', 'origin': r['source_dataset']})

            g.add_node(r['source_dataset'],
                       {'name': r['source_dataset'], 'type': 'dataset', 'origin': r['source_dataset']})

            g.add_edge(r['source_dataset'], r['source_dimension'])

    for r in provenance:
        if 'image' in r:
            g.add_node(r['person'], {'name': r['person'], 'label': r['label'], 'type': 'person', 'image': r['image']})
        else:
            g.add_node(r['person'], {'name': r['person'], 'label': r['label'], 'type': 'person'})

        g.add_edge(r['source_dataset'], r['person'])

    for r in mappings:
        if not r['target_dimension'] in g.nodes():
            print r['target_dimension'], "not in graph"
            g.add_node(r['target_dimension'], {'name': r['target_dimension'], 'type': 'dimension', 'origin': 'external'})

        g.add_edge(r['source_dimension'], r['target_dimension'])

    return g


def update(graph=None):

    dimensions = dictize(query(dimensions_query))
    provenance = dictize(query(provenance_query))
    mappings = dictize(query(mappings_query))

    g = build_graph(dimensions, provenance, mappings)

    data = json_graph.node_link_data(g)

    with open('graph.json', 'w') as f:
        json.dump(data, f)

    return data


def overview():
    datasets = dictize(query(overview_datasets_query))
    dimensions = dictize(query(overview_datasets_and_dimensions_query))

    return datasets, dimensions


def dictize(sparql_results):
    # If the results are a dict, just return the list of bindings
    if isinstance(sparql_results, dict):
        sparql_results = sparql_results['results']['bindings']

    results = []

    for r in sparql_results :
        result = {}
        for k,v in r.items():
            try :
                result[k] = v['value']
            except :
                print k, v

        results.append(result)

    return results
