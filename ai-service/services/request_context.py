from contextvars import ContextVar


_request_id_var = ContextVar("request_id", default=None)
_auth_header_var = ContextVar("auth_header", default=None)


def set_request_id(request_id):
    _request_id_var.set(request_id)


def get_request_id():
    return _request_id_var.get()


def set_auth_header(auth_header):
    _auth_header_var.set(auth_header)


def get_auth_header():
    return _auth_header_var.get()
