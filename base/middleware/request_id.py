import uuid

class RequestIDMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.request_id = str(uuid.uuid4())

        response = self.get_response(request)

        # Also add to headers (very useful for logs & tracing)
        response["X-Request-ID"] = request.request_id
        return response
