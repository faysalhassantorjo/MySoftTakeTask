from rest_framework.renderers import JSONRenderer

class RequestIDJSONRenderer(JSONRenderer):
    def render(self, data, accepted_media_type=None, renderer_context=None):
        request = renderer_context.get("request")
        response = renderer_context.get("response")

        # If DRF already returned non-dict data (e.g. list)
        if not isinstance(data, dict):
            return super().render(data, accepted_media_type, renderer_context)

        data["request_id"] = getattr(request, "request_id", None)

        return super().render(data, accepted_media_type, renderer_context)
