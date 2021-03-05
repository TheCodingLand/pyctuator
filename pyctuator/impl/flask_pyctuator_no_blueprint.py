import json
from collections import defaultdict
from datetime import datetime, date
from http import HTTPStatus
from typing import Dict, Tuple, Any, Mapping, List

from flask import Flask, Blueprint, request, jsonify, after_this_request
from flask import Response, make_response
from flask.json import JSONEncoder
from werkzeug.datastructures import Headers

from pyctuator.httptrace import TraceRecord, TraceRequest, TraceResponse
from pyctuator.impl import SBA_V2_CONTENT_TYPE
from pyctuator.impl.pyctuator_impl import PyctuatorImpl
from pyctuator.impl.pyctuator_router import PyctuatorRouter


class CustomJSONEncoder(JSONEncoder):
    """ Override Flask's JSON encoding of datetime to assure ISO format is used.

    By default, when Flask is rendering a response to JSON, it is formatting datetime, date and time according to
    RFC-822 which is different from the ISO format used by SBA.

    This encoder overrides the default datetime encoding and is only used by the Pyctuator blueprint so it shouldn't
    interfere with whatever encoding users are using.

    See https://stackoverflow.com/questions/43663552/keep-a-datetime-date-in-yyyy-mm-dd-format-when-using-flasks-jsonify
    """

    # pylint: disable=method-hidden
    def default(self, o: Any) -> Any:
        try:
            if isinstance(o, (datetime, date)):
                return o.isoformat()
            iterable = iter(o)
        except TypeError:
            pass
        else:
            return list(iterable)
        return JSONEncoder.default(self, o)


class FlaskPyctuator(PyctuatorRouter):

    # pylint: disable=too-many-locals, unused-variable
    def __init__(
            self,
            app: Flask,
            pyctuator_impl: PyctuatorImpl

    ) -> None:
        super().__init__(app, pyctuator_impl)

        path_prefix: str = pyctuator_impl.pyctuator_endpoint_path_prefix
        pyctuator_endpoints = [ "/env", "/info", "/health", "/metrics", "/loggers", "/threaddump", "/dump", "/logfile", "/mappings" ]
        pyctuator_routes = [ path_prefix  +  endpoint for endpoint in pyctuator_endpoints ]
        #flask_blueprint: Blueprint = Blueprint("flask_blueprint", "pyctuator", )
        #flask_blueprint.json_encoder = CustomJSONEncoder

        @app.before_request
        def intercept_requests_and_responses() -> None:
            request_time = datetime.now()

            @after_this_request
            def after_response(response: Response) -> Response:
                

                # Set the SBA-V2 content type for responses from Pyctuator
                if request.path in pyctuator_routes:
                    response_time = datetime.now()
                
                    response.headers["Content-Type"] = SBA_V2_CONTENT_TYPE

                # Record the request and response
                    self.record_request_and_response(response, request_time, response_time)
                return response

        #@flask_blueprint.route("/")
        #def get_endpoints() -> Any:
        #    return jsonify(self.get_endpoints_data())

        @app.route(f"{path_prefix}/env")
        def get_environment() -> Any:
            return jsonify(pyctuator_impl.get_environment())

        @app.route(f"{path_prefix}/info")
        def get_info() -> Any:
            return jsonify(pyctuator_impl.app_info)

        @app.route(f"{path_prefix}/health")
        def get_health() -> Any:
            return jsonify(pyctuator_impl.get_health())

        @app.route(f"{path_prefix}/metrics")
        def get_metric_names() -> Any:
            return jsonify(pyctuator_impl.get_metric_names())

        @app.route(f"{path_prefix}/metrics/<metric_name>")
        def get_metric_measurement(metric_name: str) -> Any:
            return jsonify(pyctuator_impl.get_metric_measurement(metric_name))

        # Retrieving All Loggers
        @app.route(f"{path_prefix}/loggers")
        def get_loggers() -> Any:
            return jsonify(pyctuator_impl.logging.get_loggers())

        @app.route(f"{path_prefix}/loggers/<logger_name>", methods=['POST'])
        def set_logger_level(logger_name: str) -> Dict:
            request_dict = json.loads(request.data)
            pyctuator_impl.logging.set_logger_level(logger_name, request_dict.get("configuredLevel", None))
            return {}

        @app.route(f"{path_prefix}/loggers/<logger_name>")
        def get_logger(logger_name: str) -> Any:
            return jsonify(pyctuator_impl.logging.get_logger(logger_name))

        @app.route(f"{path_prefix}/threaddump")
        @app.route(f"{path_prefix}/dump")
        def get_thread_dump() -> Any:
            return jsonify(pyctuator_impl.get_thread_dump())

        @app.route(f"{path_prefix}/logfile")
        def get_logfile() -> Tuple[Response, int]:
            range_header: str = request.headers.environ.get('HTTP_RANGE')
            if not range_header:
                response: Response = make_response(pyctuator_impl.logfile.log_messages.get_range())
                return response, HTTPStatus.OK

            str_res, start, end = pyctuator_impl.logfile.get_logfile(range_header)

            resp: Response = make_response(str_res)
            resp.headers["Content-Type"] = "text/html; charset=UTF-8"
            resp.headers["Accept-Ranges"] = "bytes"
            resp.headers["Content-Range"] = f"bytes {start}-{end}/{end}"

            return resp, HTTPStatus.PARTIAL_CONTENT

        @app.route(f"{path_prefix}/trace")
        @app.route(f"{path_prefix}/httptrace")
        def get_httptrace() -> Any:
            return jsonify(pyctuator_impl.http_tracer.get_httptrace())

        @app.route(f"{path_prefix}/mappings")
        def get_mappings() -> Any:
            return jsonify(pyctuator_impl.get_mappings())
        #app.register_blueprint(flask_blueprint, url_prefix=path_prefix)

    def _create_headers_dictionary_flask(self, headers: Headers) -> Mapping[str, List[str]]:
        headers_dict: Mapping[str, List[str]] = defaultdict(list)
        for (key, value) in headers.items():
            headers_dict[key].append(value)
        return dict(headers_dict)

    def record_request_and_response(
            self,
            response: Response,
            request_time: datetime,
            response_time: datetime,
    ) -> None:
        new_record = TraceRecord(
            request_time,
            None,
            None,
            TraceRequest(request.method, str(request.url), self._create_headers_dictionary_flask(request.headers)),
            TraceResponse(response.status_code, self._create_headers_dictionary_flask(response.headers)),
            int((response_time.timestamp() - request_time.timestamp()) * 1000),
        )
        self.pyctuator_impl.http_tracer.add_record(record=new_record)
