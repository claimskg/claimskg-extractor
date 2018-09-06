from rdflib import URIRef, BNode, Literal
from rdflib.namespace import RDF,DC, FOAF
from rdflib.namespace import Namespace, NamespaceManager
from rdflib import Graph
import cgi


import rdflib
# Now we create a graph, a representaiton of the ontology

# import rdflib
# from rdflib import Graph
# from rdflib.namespace import Namespace, NamespaceManager
# exNs = Namespace('https://schema.org/ClaimReview/')
# namespace_manager = NamespaceManager(Graph())
# namespace_manager.bind('ex', exNs, override=False)
# g = Graph()
# g.namespace_manager = namespace_manager
# all_ns = [n for n in g.namespace_manager.namespaces()]
# assert ('ex', rdflib.term.URIRef('https://schema.org/ClaimReview/')) in all_ns

 

import json


namespace_manager = NamespaceManager(Graph())

rdf_pref=rdflib.Namespace("http://www.w3.org/2000/01/rdf-schema#")
namespace_manager.bind('rdfs', rdf_pref, override=False)

schema_pref=rdflib.Namespace("http://schema.org/")
namespace_manager.bind('schema', schema_pref, override=False)




nee_pref=rdflib.Namespace("http://www.ics.forth.gr/isl/oae/core#")
namespace_manager.bind('nee', nee_pref, override=False)

import urllib

def export_rdf(pdf, criteria):

    index_=0
    g = rdflib.Graph()
    g.namespace_manager = namespace_manager
    for index, row in pdf.iterrows():
        index_+=1
        
        #n = Namespace("http://example.org/people/")
        
        #n.bob # = rdflib.term.URIRef(u'http://example.org/people/bob')
        
        claim = URIRef("/claim"+str(index_))
        #claim = URIRef(u'schema:2')
        #claim = rdflib.URIRef("_:claim"+str(index_),base='http://www.w3.org/2001/XMLSchema#')
        #claim = n["_:claim"+str(index_)]
        #claim = BNode(value=str(index_))
        #claim =  rdflib.term.BNode(str(index_))
        
        #g.add( (claim, RDF.type, rdflib.term.URIRef("https://schema.org/ClaimReview") ) )
        g.add( (claim, rdflib.term.URIRef(schema_pref['claimReviewed']), Literal(row['extra_title']) ) )
        g.add( (claim, rdflib.term.URIRef(schema_pref['url']), Literal(row['claimReview_url']) ) )
        g.add( (claim, rdflib.term.URIRef(schema_pref['datePublished']), Literal(row['claimReview_datePublished']) ) )
        #g.add( (claim, rdflib.term.URIRef(schema_pref['reviewRating']), Literal(row['conclusion']) ) )
        author_org=rdflib.term.URIRef("http://pl.dbpedia.org/page/Snopes.com")
        g.add( (author_org, rdflib.term.URIRef(schema_pref['url']), Literal("http://www.snopes.com") ) )
        g.add( (author_org, rdflib.term.URIRef(schema_pref['name']), Literal("Snopes") ) )
        g.add( (claim, rdflib.term.URIRef(schema_pref['author']),author_org) )


        
        #print 
        if (type(row['rating_alternateName'])==type(1.0)):
            str_=""
        else:
            str_=cgi.escape(row['rating_alternateName']).encode('ascii', 'xmlcharrefreplace')

        rating = rdflib.term.URIRef("/rating_"+str(str_))
        #rating = rdflib.term.URIRef("https://schema.org/reviewRating") 
        
        
        # Having defined the things and the edge weights, now assemble the graph
        g.add( (rating, RDF.type, rdflib.term.URIRef("https://schema.org/Rating") ) )
        g.add( (rating,  rdflib.term.URIRef(schema_pref['alternateName']),  Literal(str_) ))
        g.add( (rating,  rdflib.term.URIRef(schema_pref['bestRating']),  Literal(row['rating_bestRating']) ))
        g.add( (rating,  rdflib.term.URIRef(schema_pref['ratingValue']),  Literal(row['rating_ratingValue']) ))
        g.add( (rating,  rdflib.term.URIRef(schema_pref['worstRating']),  Literal(row['rating_worstRating']) ))
        
        g.add( (claim, rdflib.term.URIRef(schema_pref['reviewRating']), rating ) )
        

        # Having defined the things and the edge weights, now assemble the graph
        #print row['date']
        CreativeWork = rdflib.term.URIRef("http://example.org/CreativeWork_"+str(index_))
        g.add( (CreativeWork, rdflib.term.URIRef(schema_pref['datePublished']), Literal(row['creativeWork_datePublished']) ) )
        g.add( (claim, rdflib.term.URIRef(schema_pref['itemReviewed']), CreativeWork ) )
        
        #author
        person_unknown = rdflib.term.URIRef("_:person_unknown")
        g.add( (person_unknown, rdflib.term.URIRef(schema_pref['givenName']), Literal(row['creativeWork_author_name']) ) )        
        g.add( (CreativeWork,  rdflib.term.URIRef(schema_pref['author']),  person_unknown ))
        
    #     #url
    #     url_unknown = rdflib.term.URIRef("_:url_unknown") 
    #     g.add( (person_unknown, rdflib.term.URIRef(schema_pref['givenName']), Literal("unknown") ) )        
    #     g.add( (CreativeWork,  rdflib.term.URIRef(schema_pref['url']),  person_unknown ))

        g.add( (CreativeWork,  rdflib.term.URIRef(schema_pref['url']),  Literal(row['creativeWork_author_sameAs']) ))
        
        #print json.loads( row[u'entities_claim'])
        index_ent=0
        #print row[u'extra_entities_claimReview_claimReviewed']
        if (row[u'extra_entities_claimReview_claimReviewed']):
            for i in json.loads( row[u'extra_entities_claimReview_claimReviewed']):
                if (i[u'URI']):
                    index_ent+=1
                    #ne= rdflib.term.URIRef(nee_pref) 
                    ne= rdflib.term.URIRef(i[u'URI'])
                    g.add( (ne, rdflib.term.URIRef(nee_pref['detectedAs']), Literal(i[u'surfaceForm'])) )
                    
                    resource=rdflib.term.URIRef(i[u'URI'])
                    g.add( (resource, rdflib.term.URIRef(rdf_pref['Resource']), Literal(i[u'URI'])))
                    
                    #g.add( (resource, rdflib.term.URIRef(rdf_pref['Resource']), Literal(i[u'URI'])))
                    g.add( (ne, rdflib.term.URIRef(nee_pref['hasMatchedURI']), resource))
                    g.add( (ne, rdflib.term.URIRef(nee_pref['confidence']),  Literal(i[u'similarityScore'])) )
                    g.add( (claim, rdflib.term.URIRef(schema_pref['mentions']), ne ) )
        
        
        
        #break
        #if index_ > max_int:
        #    break
        #g.add(test1)

    #print g.serialize(format='turtle')
    return g.serialize(format=criteria.rdf)
    print 
    print_graph(g)