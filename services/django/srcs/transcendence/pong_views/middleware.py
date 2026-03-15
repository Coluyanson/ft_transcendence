import logging
import requests

from django.urls import resolve
from django.http import JsonResponse

logger = logging.getLogger(__name__)

AUTH_SERVICE_URL = 'http://localhost:8080'

class CustomLoginMiddleware:
    def __init__(self, get_response):
        logger.info("CustomLoginMiddleware initialized")
        self.get_response = get_response

    def __call__(self, request):
        # Determine the view name for the current request
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            try:
                response = requests.get(f"{AUTH_SERVICE_URL}/verify", headers={"Authorization": f"Bearer {token}"})
            except Exception as e:
                logger.error(e)
                return JsonResponse({'error': 'No accessible at the moment'}, status=400)
            if response.status_code == 200:
                request.user = response.json().get("username")
            else:
                return JsonResponse({'error': 'Unauthorized'}, status=401)
        else:
            return JsonResponse({'error': 'Authorization header missing or malformed'}, status=401)

        return self.get_response(request)
        # response = self.get_response(request)
        # match = resolve(request.path)
        # # print(match)
        # view_name = match.view_name  # Example: 'myapp:my_view'
        
        # # Check if the view is one that requires this middleware
        # if view_name == "pong_views:auth":  # Only apply to this specific view
        #     logger.info("CustomLoginMiddleware is processing a request")
        
        # return response
    
