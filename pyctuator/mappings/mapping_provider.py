
from dataclasses import dataclass

from typing import List, Optional

@dataclass
class Products:
    mediaType: str
    negated: bool

@dataclass
class RequestMappingConditions:
    consumes: Optional[List[str]]
    headers: List[str]
    methods: List[str]
    params: List[str]
    patterns: List[str]
    produces: List[Products]

@dataclass
class HandlerMethod:
    className: str
    name: str
    descriptor: str

@dataclass
class ServletDetails:
    handlerMethod: HandlerMethod
    requestMappingConditions: RequestMappingConditions

@dataclass
class Servlet:
    predicate: str
    handler: str
    details: Optional[ServletDetails]

@dataclass
class DispatcherServlet:
    dispatcherServlet: List[Servlet]

@dataclass
class Mappings:
    dispatcherServlets: DispatcherServlet
    parentid : Optional[int]
    
@dataclass 
class Application:
    mappings: Mappings

@dataclass
class Contexts:
    application: Application

@dataclass
class MappingProvider:
    contexts: Contexts

@dataclass
class AllMappings:
    all_mappings: MappingProvider

@dataclass
class Route():
    endpoint: str
    methods: List[str]
    rule: str
   
def get_servlets() -> List[Servlet]:
    from operator import attrgetter
    from flask import current_app as app
    
    rules = list(app.url_map.iter_rules())
    if not rules:
        return
    print (rules[0].endpoint)
    servlets = []
    documented_methods = ["GET", "POST", "PATCH", "PUT", "DELETE"]

    for rule in rules:
        for method in rule.methods:
            if method in documented_methods:

                products = []
                produced = Products(mediaType = "application/json",negated = False)
                products.append(produced)
                predicate_path = rule.rule.replace("<","{").replace(">","}")
                consumes = ["application/json"]
                if method == "GET":
                    consumes = []
                
                rc = RequestMappingConditions(
                    consumes = consumes, # we cannot know because 
                    headers = [],
                    methods = [method],
                    params = [],
                    patterns = [predicate_path],
                    produces = products
                )
                sd= ServletDetails(handlerMethod=HandlerMethod(className="test", name = "name", descriptor = "descriptor"),           
                                    requestMappingConditions = rc)
                
                
                servlet = Servlet(predicate=f"{{{method} {predicate_path}, produces [application/json]}}",
                                    handler = rule.endpoint, #name of the endpoint in flask
                                    details = sd)

                servlets.append(servlet)
    return servlets


class MappingsProvider():


    def get_mappings(self) -> AllMappings:
        return AllMappings(
            all_mappings=MappingProvider(
                contexts=Contexts(
                    application=Application(
                        mappings=Mappings(
                            dispatcherServlets=DispatcherServlet(dispatcherServlet=get_servlets()),
                                parentid = None
                        )
                    )
                )
            )
        )

    
    
    