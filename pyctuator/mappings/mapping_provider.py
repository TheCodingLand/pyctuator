
from dataclasses import dataclass

from typing import List, Optional


@dataclass
class RequestHandlerConditionsProduces:
    mediaType: str
    negated: bool

@dataclass
class RequestHandlerConditions:
    consumes: List[str]
    headers: List[str]
    methods: List[str]
    params: List[str]
    patterns: List[str]
    produces: List[RequestHandlerConditionsProduces]


@dataclass
class HandlerMethod:
    className: str
    name: str
    descriptor: str

@dataclass
class HandlerDetails:
    handlerMethod: HandlerMethod
    handlerFunction: str
    requestHandlerConditions: RequestHandlerConditions



@dataclass
class Endpoints:
    predictate: str
    handler: str
    details: HandlerDetails



@dataclass
class DispatcherHandler:
    webHandler: List[Endpoints]



@dataclass
class Mappings:
    dispatcherHandlers: [DispatcherHandler, ]
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
class Route():
    endpoint: str
    methods: List[str]
    rule: str

    

def get_request_handlers() -> List[RequestHandlerConditionsProduces]:
    from operator import attrgetter
    from flask import current_app as app
    
    
    
    rules = list(app.url_map.iter_rules())
    if not rules:
        
        return
    print (rules[0].endpoint)
    requestHandlers = []
    for rule in rules:
        artefacts = []
        produced = RequestHandlerConditionsProduces(mediaType= "application/json",negated = False)
        artefacts.append(produced)
        rc = RequestHandlerConditions(
            consumes = [], 
            headers = [],
            methods =  [method for method in rule.methods],
            params = [],
            patterns = [],
            produces = artefacts
        )
        requestHandlers.append(rc)
    return requestHandlers
    #print(requestHandlers)
        

class MappingsProvider():

    #def _get_request_mapping_conditions(self, route: Route) -> RequestHandlerConditions:
    #    artefacts = []
    #    produced = RequestHandlerConditionsProduces(mediaType= "application/json",negated = False)
    #    artefacts.append(produced)
    #    return RequestHandlerConditions(
    #        consumes = [], 
    #        headers = [],
    #        methods =  [],
    #        params = [],
    #        patterns = [],
    #        produces = [artefacts],
            
    #    )
    def _get_dispatch_handlers(self, app):
        pass
        


    def get_mappings(self) -> Contexts:
        return MappingProvider(
            contexts=Contexts(
                application=Application(
                    mappings=Mappings(
                        dispatcherHandlers=[DispatcherHandler(webHandler=get_request_handlers())],
                        parentid = None
                            #webHandler() #will do for now as we only have web handlers
                        
                    )
                )
            )
        )
    
    
    